from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pdi_status = fields.Selection([
        ('pending', 'Pending PDI'),
        ('in_progress', 'In Inspection'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('ready_pickup', 'Ready Pickup'),
    ], string='PDI Status', compute='_compute_pdi_status', store=True)

    def _compute_pdi_status(self):
        for order in self:
            pdi_orders = self.env['bike.pdi.order'].search([('sales_order_id', '=', order.id)])
            if not pdi_orders:
                order.pdi_status = False
                continue
            
            states = pdi_orders.mapped('state')
            if 'failed' in states:
                order.pdi_status = 'failed'
            elif 'in_progress' in states:
                order.pdi_status = 'in_progress'
            elif 'pending' in states:
                order.pdi_status = 'pending'
            elif all(s == 'passed' for s in states):
                order.pdi_status = 'ready_pickup'
            else:
                order.pdi_status = False
