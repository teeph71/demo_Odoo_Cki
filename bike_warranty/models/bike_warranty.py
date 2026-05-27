from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class BikeWarranty(models.Model):
    _name = 'bike.warranty'
    _description = 'Bike Warranty Card'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ─── Thông tin phiếu ─────────────────────────────────────────────────────
    name = fields.Char(
        string='Warranty Code',
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    note = fields.Text(string='Notes')

    # ─── Liên kết đơn hàng ───────────────────────────────────────────────────
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
        tracking=True,
        domain=[('state', 'in', ['sale', 'done'])],
    )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Order Line',
        domain="[('order_id', '=', sale_order_id)]",
    )

    # ─── Thông tin sản phẩm ──────────────────────────────────────────────────
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        tracking=True,
    )
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        compute='_compute_product_info',
        store=True,
    )
    warranty_duration = fields.Integer(
        string='Thời hạn bảo hành (tháng)',
        help='Lấy tự động từ cấu hình sản phẩm',
    )

    # ─── Thời gian bảo hành ──────────────────────────────────────────────────
    start_date = fields.Date(
        string='Warranty Start Date',
        default=fields.Date.today,
        tracking=True,
    )
    end_date = fields.Date(
        string='Warranty End Date',
        compute='_compute_end_date',
        store=True,
        tracking=True,
    )

    # ─── Thông tin khách hàng ────────────────────────────────────────────────
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        tracking=True,
    )
    partner_name = fields.Char(
        string='Customer Name',
        compute='_compute_partner_info',
        store=True,
        readonly=False,
    )
    partner_phone = fields.Char(
        string='Phone',
        compute='_compute_partner_info',
        store=True,
        readonly=False,
    )
    partner_street = fields.Char(
        string='Address',
        compute='_compute_partner_info',
        store=True,
        readonly=False,
    )
    partner_city = fields.Char(
        string='City',
        compute='_compute_partner_info',
        store=True,
        readonly=False,
    )

    # ─── Compute methods ─────────────────────────────────────────────────────

    @api.depends('start_date', 'warranty_duration')
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.warranty_duration > 0:
                record.end_date = record.start_date + relativedelta(
                    months=record.warranty_duration
                )
            else:
                record.end_date = False

    @api.depends('product_id')
    def _compute_product_info(self):
        for record in self:
            if record.product_id:
                record.product_category_id = record.product_id.categ_id
            else:
                record.product_category_id = False

    @api.depends('partner_id')
    def _compute_partner_info(self):
        for record in self:
            if record.partner_id:
                record.partner_name = record.partner_id.name
                record.partner_phone = (
                    record.partner_id.phone or record.partner_id.mobile
                )
                record.partner_street = record.partner_id.street
                record.partner_city = record.partner_id.city
            else:
                record.partner_name = False
                record.partner_phone = False
                record.partner_street = False
                record.partner_city = False

    # ─── Onchange ─────────────────────────────────────────────────────────────

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Tự động điền khách hàng khi chọn SO."""
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id
            self.start_date = (
                self.sale_order_id.date_order.date()
                if self.sale_order_id.date_order else fields.Date.today()
            )
        else:
            self.sale_order_line_id = False

    @api.onchange('sale_order_line_id')
    def _onchange_sale_order_line_id(self):
        """Tự động điền sản phẩm và thời hạn BH khi chọn dòng SO."""
        if self.sale_order_line_id:
            product = self.sale_order_line_id.product_id
            self.product_id = product
            template = product.product_tmpl_id
            if hasattr(template, 'warranty_duration'):
                self.warranty_duration = template.warranty_duration

    # ─── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('warranty_duration')
    def _check_warranty_duration(self):
        for record in self:
            if record.warranty_duration < 0:
                raise ValidationError(
                    'Thời hạn bảo hành không được nhỏ hơn 0!'
                )

    # ─── Workflow actions ─────────────────────────────────────────────────────

    def action_activate(self):
        """Kích hoạt phiếu bảo hành."""
        for record in self:
            if not record.product_id:
                raise ValidationError('Vui lòng chọn sản phẩm trước khi kích hoạt!')
            if not record.partner_id:
                raise ValidationError('Vui lòng chọn khách hàng trước khi kích hoạt!')
            record.state = 'active'

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'}) 

    def action_set_expired(self):
        self.write({'state': 'expired'})

    def action_print_warranty(self):
        return self.env.ref(
            'bike_warranty.action_report_bike_warranty'
        ).report_action(self)

    # ─── CRUD override ────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'bike.warranty'
                ) or 'New'
        return super().create(vals_list)

    # ─── Cron: tự động hết hạn ────────────────────────────────────────────────

    @api.model
    def _cron_check_warranty_expiry(self):
        """Cron job: chuyển phiếu active → expired khi quá ngày hết hạn."""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today),
        ])
        expired.write({'state': 'expired'})
