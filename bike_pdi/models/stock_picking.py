from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        res = super()._action_done()

        for picking in self:
            requires_assembly = False
            for move in picking.move_ids:
                if move.product_id.is_bike and move.product_id.is_assembly_required:
                    requires_assembly = True
                    break
            
            if not requires_assembly and picking.picking_type_id.code == 'internal':
                PdiOrder = self.env['bike.pdi.order']
                Template = self.env['bike.pdi.template']
                
                for move in picking.move_ids:
                    if move.product_id.is_bike:
                        template = Template.search([('category_id', 'parent_of', move.product_id.categ_id.id)], limit=1)
                        for line in move.move_line_ids:
                            if line.quantity > 0 and (line.lot_id or line.lot_name):
                                lot_id = line.lot_id.id
                                if not lot_id and line.lot_name:
                                    lot = self.env['stock.lot'].search([('name', '=', line.lot_name), ('product_id', '=', move.product_id.id)], limit=1)
                                    lot_id = lot.id if lot else False

                                checklist_vals = []
                                if template:
                                    for t_line in template.line_ids:
                                        checklist_vals.append((0, 0, {
                                            'item_name': t_line.name,
                                        }))

                                PdiOrder.create({
                                    'picking_id': picking.id,
                                    'sales_order_id': picking.sale_id.id if picking.sale_id else False,
                                    'customer_id': picking.partner_id.id,
                                    'product_id': move.product_id.id,
                                    'serial_id': lot_id,
                                    'checklist_template_id': template.id if template else False,
                                    'checklist_line_ids': checklist_vals,
                                    'state': 'pending',
                                })
        return res

    def button_validate(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                pdi_orders = self.env['bike.pdi.order'].search([('picking_id', '=', picking.id)])
                if pdi_orders:
                    unpassed = pdi_orders.filtered(lambda p: p.state != 'passed')
                    if unpassed:
                        raise UserError("Cannot validate Delivery Order. Not all bikes have passed PDI.")
                        
                # Also check assembly orders linked to this picking that haven't been passed
                assembly_orders = self.env['bike.assembly.order'].search([('picking_id', '=', picking.id)])
                for asm in assembly_orders:
                    # check if this asm has a passing PDI
                    pdi = self.env['bike.pdi.order'].search([('picking_id', '=', picking.id), ('serial_id', '=', asm.serial_id.id)], limit=1)
                    if not pdi or pdi.state != 'passed':
                        raise UserError(f"Cannot validate Delivery Order. The assembled bike with serial {asm.serial_id.name if asm.serial_id else ''} has not passed PDI.")
        return super().button_validate()
