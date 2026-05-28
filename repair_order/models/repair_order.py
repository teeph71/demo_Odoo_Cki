from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BikeRepairOrder(models.Model):
    _name = 'bike.repair.order'
    _description = 'Bike Repair Order'
    _order = 'create_date desc'

    # --- FIELDS ---
    name = fields.Char(string='Repair No', required=True, copy=False, default='New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('repairing', 'Repairing'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True)

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    
    x_is_member_display = fields.Boolean(related='customer_id.x_is_member', string="Is Member", readonly=True)
    x_member_tier_id_display = fields.Many2one(related='customer_id.x_member_tier_id', string="Customer Tier", readonly=True)

    bicycle_name = fields.Char(string='Bicycle', required=True)
    serial_number = fields.Char(string='Serial Number')
    problem_description = fields.Text(string='Problem Description')
    diagnosis = fields.Text(string='Diagnosis')
    
    technician_id = fields.Many2one('res.users', string='Technician', tracking=True,
        domain=lambda self: self._get_technician_domain())
    
    assigned_at = fields.Datetime(string='Assigned At', readonly=True)
    assigned_by = fields.Many2one('res.users', string='Assigned By', readonly=True)
    
    service_package_id = fields.Many2one('bike.repair.service.package', string='Service Package', required=True)
    warranty_card_id = fields.Many2one('bike.warranty', string='Warranty Card')

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True, copy=False)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')

    checklist_line_ids = fields.One2many('bike.repair.checklist.line', 'order_id', string='Repair Checklist')

    labor_cost = fields.Float(string='Labor Cost', compute='_compute_labor_cost', store=True, readonly=False)
    package_price = fields.Float(related='service_package_id.price', string='Package Price', store=True)
    parts_cost = fields.Float(string='Parts Cost', default=0.0)
    
    membership_discount = fields.Float(string='Membership Discount', compute='_compute_membership_discount')
    warranty_discount = fields.Float(string='Warranty Discount', compute='_compute_warranty_discount', store=True)
    total_amount = fields.Float(string='Total', compute='_compute_total_amount', store=True)

    # --- COMPUTE LOGIC ---
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.sale_order_id else 0

    @api.depends('service_package_id.price')
    def _compute_labor_cost(self):
        for rec in self:
            rec.labor_cost = rec.service_package_id.price or 0.0

    @api.depends('labor_cost', 'customer_id.x_is_member', 'customer_id.x_member_tier_id.discount_rate')
    def _compute_membership_discount(self):
        for rec in self:
            discount = 0.0
            # Nếu KHÔNG phải bảo hành thì mới tính chiết khấu hạng thành viên (tránh giảm 2 lần)
            if not rec.warranty_card_id:
                if rec.customer_id and getattr(rec.customer_id, 'x_is_member', False):
                    tier = getattr(rec.customer_id, 'x_member_tier_id', False)
                    if tier:
                        discount = rec.labor_cost * (tier.discount_rate / 100.0)
            rec.membership_discount = discount

    @api.depends('service_package_id.code', 'package_price', 'customer_id.x_is_member', 
                 'customer_id.x_member_tier_id.free_maintenance_sessions', 'warranty_card_id')
    def _compute_warranty_discount(self):
        for rec in self:
            discount = 0.0
            # TH1: NẾU CÓ THẺ BẢO HÀNH -> Miễn phí 100% tiền công gói dịch vụ
            if rec.warranty_card_id:
                discount = rec.labor_cost
            
            # TH2: Nếu không có thẻ bảo hành, xét gói RP-BASIC + lượt miễn phí của Member
            elif (rec.service_package_id and rec.service_package_id.code == 'RP-BASIC' and 
                  rec.customer_id and getattr(rec.customer_id, 'x_is_member', False)):
                tier = getattr(rec.customer_id, 'x_member_tier_id', False)
                if tier and tier.free_maintenance_sessions > 0:
                    discount = rec.package_price
            
            rec.warranty_discount = discount

    @api.depends('labor_cost', 'parts_cost', 'membership_discount', 'warranty_discount')
    def _compute_total_amount(self):
        for rec in self:
            # Tổng = (Công + Linh kiện) - Giảm giá Member - Giảm giá Bảo hành
            total = (rec.labor_cost + rec.parts_cost) - rec.membership_discount - rec.warranty_discount
            rec.total_amount = max(0.0, total)

    # --- ACTIONS ---
    def action_confirm(self):
        for rec in self:
            if not rec.service_package_id.product_id:
                raise UserError("Gói dịch vụ này chưa có sản phẩm liên kết. Vui lòng kiểm tra lại Package.")

            if not rec.sale_order_id:
                # Tính toán đơn giá thực tế đẩy sang SO 
                # Nếu bảo hành 100% thì đơn giá nhân công = 0
                so_labor_price = max(0.0, rec.labor_cost - rec.warranty_discount)

                so = self.env['sale.order'].create({
                    'partner_id': rec.customer_id.id,
                    'repair_order_id': rec.id,
                    'order_line': [(0, 0, {
                        'product_id': rec.service_package_id.product_id.id,
                        'name': f"[BẢO HÀNH] {rec.service_package_id.name}" if rec.warranty_card_id else rec.service_package_id.name,
                        'product_uom_qty': 1.0,
                        'price_unit': so_labor_price,
                    })],
                })
                rec.sale_order_id = so
            rec.state = 'confirmed'

    def action_start_repair(self):
        for rec in self:
            if not rec.technician_id:
                raise UserError(_("Vui lòng chọn kỹ thuật viên trước!"))
            rec.assigned_at = fields.Datetime.now()
            rec.assigned_by = self.env.user
            rec.state = 'repairing'

    def action_done(self):
        for rec in self:
            if any(not line.completed for line in rec.checklist_line_ids):
                raise UserError(_("Cần hoàn thành tất cả các mục checklist!"))
            
            # Chỉ trừ số lần bảo trì miễn phí nếu KHÔNG dùng thẻ bảo hành
            if not rec.warranty_card_id:
                if (rec.service_package_id and rec.service_package_id.code == 'RP-BASIC' and 
                    rec.customer_id and getattr(rec.customer_id, 'x_is_member', False)):
                    tier = getattr(rec.customer_id, 'x_member_tier_id', None)
                    if tier and tier.free_maintenance_sessions > 0:
                        tier.write({'free_maintenance_sessions': tier.free_maintenance_sessions - 1})
            rec.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_view_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    @api.model
    def _get_technician_domain(self):
        employees = self.env['hr.employee'].search([('department_id.name', '=', 'Phòng ban Kho')])
        return [('id', 'in', employees.mapped('user_id').ids)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.repair.order') or 'New'
        return super().create(vals_list)

    @api.onchange('service_package_id')
    def _onchange_service_package_id(self):
        if self.service_package_id:
            lines = []
            for template in self.service_package_id.checklist_template_ids:
                for line in template.line_ids:
                    if line.name:
                        lines.append((0, 0, {'name': line.name, 'completed': False}))
            self.checklist_line_ids = [(5, 0, 0)] + lines

    @api.onchange('warranty_card_id')
    def _onchange_warranty_card_id(self):
        if self.warranty_card_id:
            if hasattr(self.warranty_card_id, 'partner_id') and self.warranty_card_id.partner_id:
                self.customer_id = self.warranty_card_id.partner_id
            
            if hasattr(self.warranty_card_id, 'product_id') and self.warranty_card_id.product_id:
                self.bicycle_name = self.warranty_card_id.product_id.display_name
            
            if hasattr(self.warranty_card_id, 'serial_number') and self.warranty_card_id.serial_number:
                self.serial_number = self.warranty_card_id.serial_number

    @api.onchange('customer_id')
    def _onchange_customer_id_filter_warranty(self):
        if self.customer_id:
            return {'domain': {'warranty_card_id': [('partner_id', '=', self.customer_id.id)]}}
        return {'domain': {'warranty_card_id': []}}