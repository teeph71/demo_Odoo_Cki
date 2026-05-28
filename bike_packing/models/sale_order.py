from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    packing_status = fields.Selection([
        ('pending', 'Pending Packing'),
        ('packing', 'Packing'),
        ('waiting_item', 'Waiting Item'),
        ('packed', 'Packed'),
    ], string='Packing Status', compute='_compute_packing_status', store=True)

    def _compute_packing_status(self):
        for order in self:
            packing_orders = self.env['bike.packing.order'].search([('sales_order_id', '=', order.id)])
            if not packing_orders:
                order.packing_status = False
                continue
            
            states = packing_orders.mapped('state')
            if 'waiting_item' in states:
                order.packing_status = 'waiting_item'
            elif 'packing' in states:
                order.packing_status = 'packing'
            elif 'pending' in states or 'draft' in states:
                order.packing_status = 'pending'
            elif all(s == 'packed' for s in states):
                order.packing_status = 'packed'
            else:
                order.packing_status = False
