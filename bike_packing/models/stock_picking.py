from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        for picking in self:
            # Determine if this is the Packing transfer
            type_name = (picking.picking_type_id.name or '').lower()
            seq_code = (picking.picking_type_id.sequence_code or '').upper()
            is_packing_transfer = seq_code == 'PACK' or any(kw in type_name for kw in ['pack', 'đóng gói', 'dong goi'])
            
            if is_packing_transfer or picking.picking_type_id.code == 'outgoing':
                # Check if it's a bike order
                is_bike_order = any(move.product_id.is_bike for move in picking.move_ids)
                if is_bike_order:
                    # Check PDI and Assembly on the Packing Transfer
                    if is_packing_transfer:
                        # Check PDI
                        domain_pdi = [('sales_order_id', '=', picking.sale_id.id)] if picking.sale_id else [('picking_id', '=', picking.id)]
                        pdi_orders = self.env['bike.pdi.order'].search(domain_pdi)
                        if not pdi_orders:
                            raise UserError("Cannot validate Packing Transfer. It is a bike order but has no PDI records.")
                        if any(p.state != 'passed' for p in pdi_orders):
                            raise UserError("Cannot validate Packing Transfer. Not all bikes have passed PDI.")
                        
                        # Check Assembly
                        requires_assembly = any(move.product_id.is_bike and move.product_id.is_assembly_required for move in picking.move_ids)
                        if requires_assembly:
                            domain_asm = [('sales_order_id', '=', picking.sale_id.id)] if picking.sale_id else [('picking_id', '=', picking.id)]
                            assembly_orders = self.env['bike.assembly.order'].search(domain_asm)
                            if not assembly_orders:
                                raise UserError("Cannot validate Packing Transfer. It requires assembly but has no assembly records.")
                            if any(a.state != 'completed' for a in assembly_orders):
                                raise UserError("Cannot validate Packing Transfer. Not all assembly records are completed.")
                
                if picking.picking_type_id.code == 'outgoing':
                    # Existing packing check for Delivery Order
                    packing_orders = self.env['bike.packing.order'].search([('picking_id', '=', picking.id)])
                    if packing_orders:
                        unpacked = packing_orders.filtered(lambda p: p.state != 'packed')
                        if unpacked:
                            raise UserError("Cannot validate Delivery Order. Not all bikes have been packed completely.")
        return super().button_validate()
