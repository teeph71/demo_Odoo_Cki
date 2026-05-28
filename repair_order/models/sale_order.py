from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    repair_order_id = fields.Many2one('bike.repair.order', string='Source Repair Order', readonly=True)

    def action_view_repair_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order',
            'res_model': 'bike.repair.order',
            'view_mode': 'form',
            'res_id': self.repair_order_id.id,
        }