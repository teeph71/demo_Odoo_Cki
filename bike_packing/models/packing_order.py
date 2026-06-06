from odoo import models, fields, api
from odoo.exceptions import UserError

class BikePackingOrder(models.Model):
    _name = 'bike.packing.order'
    _description = 'Bike Packing Order'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Packing Reference', required=True, copy=False, readonly=True, default='New')
    sales_order_id = fields.Many2one('sale.order', string='Sales Order', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Bike', readonly=True)
    serial_id = fields.Many2one('stock.lot', string='Frame Serial', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', tracking=True)
    warehouse_user_id = fields.Many2one('res.users', string='Warehouse Staff', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Packing'),
        ('packing', 'Packing'),
        ('waiting_item', 'Waiting Item'),
        ('packed', 'Packed')
    ], string='Status', default='draft', tracking=True)
    
    start_time = fields.Datetime(string='Start Time', readonly=True)
    packed_time = fields.Datetime(string='Finish Time', readonly=True)
    
    checklist_line_ids = fields.One2many('bike.packing.checklist.line', 'packing_id', string='Checklist')

    @api.constrains('picking_id')
    def _check_picking_pdi_assembly(self):
        for order in self:
            if order.picking_id:
                # Gọi hàm helper dùng chung từ stock.picking
                order.picking_id._check_bike_pdi_assembly_status()

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.sales_order_id = self.picking_id.sale_id.id if hasattr(self.picking_id, 'sale_id') and self.picking_id.sale_id else False
            self.customer_id = self.picking_id.partner_id.id if self.picking_id.partner_id else False
            
            # Try to populate product and serial if there is only one bike
            bike_moves = self.picking_id.move_ids.filtered(lambda m: m.product_id.is_bike)
            if len(bike_moves) == 1:
                self.product_id = bike_moves[0].product_id.id
                for line in bike_moves[0].move_line_ids:
                    if line.lot_id:
                        self.serial_id = line.lot_id.id
                        break
            elif len(bike_moves) > 1:
                # Clear them if there are multiple, to let user select if they were editable, 
                # but they are readonly. We might need to make them editable if multiple bikes exist.
                # For now, just set to the first one as default
                self.product_id = bike_moves[0].product_id.id
                for line in bike_moves[0].move_line_ids:
                    if line.lot_id:
                        self.serial_id = line.lot_id.id
                        break

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.packing.order') or 'New'
            
        records = super().create(vals_list)
        
        for record in records:
            if not record.checklist_line_ids:
                default_items = [
                    'Bike verified',
                    'Frame serial verified',
                    'Helmet packed',
                    'Lock packed',
                    'Manual included',
                    'Warranty card included',
                    'Invoice attached',
                    'Visual condition checked'
                ]
                record.write({
                    'checklist_line_ids': [(0, 0, {'item_name': item}) for item in default_items]
                })
        return records

    def action_start_packing(self):
        for order in self:
            if order.state not in ['pending', 'waiting_item']:
                raise UserError("Only pending or waiting items can be started.")
            order.write({
                'state': 'packing',
                'start_time': fields.Datetime.now() if not order.start_time else order.start_time,
                'warehouse_user_id': self.env.user.id
            })
            if order.sales_order_id:
                order.sales_order_id._compute_packing_status()
        return True

    def action_complete_packing(self):
        for order in self:
            if order.state != 'packing':
                raise UserError("Only packing state can be completed.")
            
            # Re-check PDI and Assembly
            if order.picking_id:
                # Gọi hàm helper dùng chung từ stock.picking
                order.picking_id._check_bike_pdi_assembly_status()
            
            unchecked_lines = order.checklist_line_ids.filtered(lambda l: not l.checked)
            if unchecked_lines:
                raise UserError("You must check all checklist items before completing the packing.")
            
            order.write({
                'state': 'packed',
                'packed_time': fields.Datetime.now()
            })
            
            if order.picking_id:
                order.picking_id.message_post(body=f"Packing {order.name} Completed.")
                
            if order.sales_order_id:
                order.sales_order_id._compute_packing_status()
        return True

    def action_waiting_item(self):
        for order in self:
            if order.state != 'packing':
                raise UserError("Only packing state can be marked as waiting item.")
            order.write({
                'state': 'waiting_item'
            })
            if order.sales_order_id:
                order.sales_order_id._compute_packing_status()
        return True

class BikePackingChecklistLine(models.Model):
    _name = 'bike.packing.checklist.line'
    _description = 'Bike Packing Checklist Line'

    packing_id = fields.Many2one('bike.packing.order', string='Packing Order', ondelete='cascade')
    item_name = fields.Char(string='Item Name', required=True)
    checked = fields.Boolean(string='Checked', default=False)
    note = fields.Text(string='Note')
    checked_by = fields.Many2one('res.users', string='Checked By', readonly=True)
    checked_at = fields.Datetime(string='Checked At', readonly=True)

    @api.onchange('checked')
    def _onchange_checked(self):
        if self.checked:
            self.checked_by = self.env.user
            self.checked_at = fields.Datetime.now()
        else:
            self.checked_by = False
            self.checked_at = False
