from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class BikeAssemblyOrder(models.Model):
    _name = 'bike.assembly.order'
    _description = 'Bike Assembly Order'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
    sales_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Bike', readonly=True)
    serial_id = fields.Many2one('stock.lot', string='Frame Serial', readonly=True)
    technician_id = fields.Many2one('res.users', string='Technician', tracking=True)
    checklist_template_id = fields.Many2one('bike.assembly.template', string='Template', readonly=True)
    
    start_time = fields.Datetime(string='Start Time', readonly=True)
    finish_time = fields.Datetime(string='Finish Time', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rework', 'Rework')
    ], string='Status', default='draft', tracking=True)
    
    checklist_line_ids = fields.One2many('bike.assembly.checklist.line', 'order_id', string='Checklist')
    notes = fields.Text(string='Notes')

    @api.onchange('checklist_template_id')
    def _onchange_checklist_template_id(self):
        if self.checklist_template_id:
            # Clear existing checklist if any
            self.checklist_line_ids = [(5, 0, 0)]
            lines = []
            for t_line in self.checklist_template_id.line_ids:
                lines.append((0, 0, {
                    'task_name': t_line.name,
                }))
            self.checklist_line_ids = lines

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.assembly.order') or 'New'
        return super().create(vals_list)

    def action_assign(self):
        self.ensure_one()
        if not self.technician_id:
            raise UserError("Vui lòng chọn Kỹ thuật viên (Technician) trước khi Assign.")
        self.state = 'assigned'

    def action_start_assembly(self):
        self.ensure_one()
        self.start_time = datetime.now()
        self.state = 'in_progress'

    def action_complete_assembly(self):
        self.ensure_one()
        if not self.serial_id:
            raise UserError("Bắt buộc phải có Frame Serial (Số khung) trước khi hoàn tất.")
        
        unchecked_lines = self.checklist_line_ids.filtered(lambda l: not l.completed)
        if unchecked_lines:
            raise UserError("Bạn phải hoàn thành toàn bộ Checklist trước khi hoàn tất lắp ráp.")
            
        self.finish_time = datetime.now()
        self.state = 'completed'

    def action_return_rework(self):
        self.ensure_one()
        self.state = 'rework'


class BikeAssemblyChecklistLine(models.Model):
    _name = 'bike.assembly.checklist.line'
    _description = 'Bike Assembly Checklist Line'

    order_id = fields.Many2one('bike.assembly.order', string='Assembly Order', ondelete='cascade')
    task_name = fields.Char(string='Task Name', required=True)
    completed = fields.Boolean(string='Completed', default=False)
    notes = fields.Text(string='Notes')
    completed_by = fields.Many2one('res.users', string='Completed By')
    completed_at = fields.Datetime(string='Completed At')

    @api.onchange('completed')
    def _onchange_completed(self):
        if self.completed:
            self.completed_by = self.env.user
            self.completed_at = datetime.now()
        else:
            self.completed_by = False
            self.completed_at = False
