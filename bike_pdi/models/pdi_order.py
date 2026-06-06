from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class BikePdiOrder(models.Model):
    _name = 'bike.pdi.order'
    _description = 'Bike PDI Order'
    _order = 'create_date desc'

    name = fields.Char(string='PDI Reference', required=True, copy=False, readonly=True, default='New')
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
    sales_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Bike', readonly=True)
    serial_id = fields.Many2one('stock.lot', string='Frame Serial', readonly=True)
    technician_id = fields.Many2one('res.users', string='Technician')
    
    @api.model
    def _read_group_state(self, *args, **kwargs):
        return ['pending', 'in_progress', 'passed', 'failed']

    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed')
    ], string='Status', default='pending', group_expand='_read_group_state')
    
    result = fields.Selection([
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL')
    ], string='PDI Result', readonly=True)
    
    start_time = fields.Datetime(string='Start Time', readonly=True)
    finish_time = fields.Datetime(string='Finish Time', readonly=True)
    fail_reason = fields.Text(string='Failure Notes')
    
    checklist_template_id = fields.Many2one('bike.pdi.template', string='Template', readonly=True)
    checklist_line_ids = fields.One2many('bike.pdi.checklist.line', 'pdi_id', string='Checklist')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.pdi.order') or 'New'
            
            if vals.get('checklist_template_id') and not vals.get('checklist_line_ids'):
                template = self.env['bike.pdi.template'].browse(vals['checklist_template_id'])
                if template:
                    lines = []
                    for t_line in template.line_ids:
                        lines.append((0, 0, {
                            'item_name': t_line.name,
                        }))
                    vals['checklist_line_ids'] = lines

        return super().create(vals_list)

    def action_start_inspection(self):
        for order in self:
            if order.state != 'pending':
                raise UserError("Phiếu kiểm định này đang được xử lý hoặc đã hoàn tất.")
            order.write({
                'state': 'in_progress',
                'start_time': fields.Datetime.now()
            })
        return True

    def action_set_pdi_pass(self):
        for order in self:
            if order.state != 'in_progress':
                raise UserError("Chỉ có thể kết luận trạng thái khi phiếu đang ở trạng thái Đang kiểm tra.")
            
            unconfirmed_lines = order.checklist_line_ids.filtered(lambda l: not l.status)
            if unconfirmed_lines:
                raise UserError("Chặn thao tác! Bạn bắt buộc phải đánh giá và tích chọn kết quả cho toàn bộ các dòng checklist kỹ thuật trước khi kết luận.")
            
            failed_lines = order.checklist_line_ids.filtered(lambda l: l.status == 'fail')
            if failed_lines:
                raise UserError("Không thể xác nhận ĐẠT tổng thể khi danh sách checklist chi tiết vẫn tồn tại hạng mục bị đánh giá LỖI (FAIL).")
            
            order.write({
                'state': 'passed',
                'result': 'PASS',
                'finish_time': fields.Datetime.now()
            })
            if order.picking_id:
                order.picking_id.message_post(body=f"PDI {order.name} Passed.")
                
            if order.sales_order_id:
                order.sales_order_id._compute_pdi_status()
        return True

    def action_set_pdi_fail(self):
        for order in self:
            if order.state != 'in_progress':
                raise UserError("Chỉ có thể kết luận trạng thái khi phiếu đang ở trạng thái Đang kiểm tra.")
            
            if not order.fail_reason or order.fail_reason.strip() == "":
                raise UserError("Quy tắc bắt buộc! Vui lòng nhập chi tiết lý do và hiện trạng lỗi cơ khí vào trường 'Lý do không đạt' trước khi xác nhận FAIL đơn hàng.")
            
            order.write({
                'state': 'failed',
                'result': 'FAIL',
                'finish_time': fields.Datetime.now()
            })
            
            assembly = self.env['bike.assembly.order'].search([
                ('picking_id', '=', order.picking_id.id),
                ('serial_id', '=', order.serial_id.id)
            ], limit=1)
            if assembly and assembly.state == 'completed':
                assembly.write({'state': 'rework'})
                assembly.message_post(body=f"Returned to Rework due to PDI Failure: {order.name}. Reason: {order.fail_reason}")
                
            if order.picking_id:
                order.picking_id.message_post(body=f"PDI {order.name} Failed. Sent to Rework. Reason: {order.fail_reason}")
                
            if order.sales_order_id:
                order.sales_order_id._compute_pdi_status()
        return True


class BikePdiChecklistLine(models.Model):
    _name = 'bike.pdi.checklist.line'
    _description = 'Bike PDI Checklist Line'

    pdi_id = fields.Many2one('bike.pdi.order', string='PDI Order', ondelete='cascade')
    item_name = fields.Char(string='Inspection Item', required=True)
    status = fields.Selection([
        ('pass', 'PASS'),
        ('fail', 'FAIL'),
        ('na', 'N/A')
    ], string='Result')
    note = fields.Text(string='Inspector Note')
    checked_by = fields.Many2one('res.users', string='Checked By')
    checked_at = fields.Datetime(string='Checked At')

    @api.onchange('status')
    def _onchange_status(self):
        if self.status:
            self.checked_by = self.env.user
            self.checked_at = fields.Datetime.now()
        else:
            self.checked_by = False
            self.checked_at = False
