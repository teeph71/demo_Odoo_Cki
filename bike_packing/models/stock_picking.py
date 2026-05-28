from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                # Check if it's a bike order
                is_bike_order = any(move.product_id.is_bike for move in picking.move_ids)
                if is_bike_order:
                    # Check PDI
                    pdi_orders = self.env['bike.pdi.order'].search([('picking_id', '=', picking.id)])
                    if not pdi_orders:
                        raise UserError("Cannot validate Delivery Order. It is a bike order but has no PDI records.")
                    if any(p.state != 'passed' for p in pdi_orders):
                        raise UserError("Cannot validate Delivery Order. Not all bikes have passed PDI.")
                    
                    # Check Assembly
                    requires_assembly = any(move.product_id.is_bike and move.product_id.is_assembly_required for move in picking.move_ids)
                    if requires_assembly:
                        assembly_orders = self.env['bike.assembly.order'].search([('picking_id', '=', picking.id)])
                        if not assembly_orders:
                            raise UserError("Cannot validate Delivery Order. It requires assembly but has no assembly records.")
                        if any(a.state != 'completed' for a in assembly_orders):
                            raise UserError("Cannot validate Delivery Order. Not all assembly records are completed.")

                # Existing packing check
                packing_orders = self.env['bike.packing.order'].search([('picking_id', '=', picking.id)])
                if packing_orders:
                    unpacked = packing_orders.filtered(lambda p: p.state != 'packed')
                    if unpacked:
                        raise UserError("Cannot validate Delivery Order. Not all bikes have been packed completely.")
        return super().button_validate()
