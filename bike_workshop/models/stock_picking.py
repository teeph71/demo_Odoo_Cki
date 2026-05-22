from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        # Call the original method to handle status change and validations
        res = super()._action_done()

        for picking in self:
            requires_assembly = False
            for move in picking.move_ids:
                if move.product_id.is_bike and move.product_id.is_assembly_required:
                    requires_assembly = True
                    break
            
            if requires_assembly:
                picking.picking_status = 'assembly'
                AssemblyOrder = self.env['bike.assembly.order']
                Template = self.env['bike.assembly.template']
                
                for move in picking.move_ids:
                    if move.product_id.is_bike and move.product_id.is_assembly_required:
                        # Find template for this product category or its parent categories
                        template = Template.search([('category_id', 'parent_of', move.product_id.categ_id.id)], limit=1)
                        
                        # We create one task per move_line (per serial)
                        for line in move.move_line_ids:
                            if line.quantity > 0 and (line.lot_id or line.lot_name):
                                lot_id = line.lot_id.id
                                if not lot_id and line.lot_name:
                                    # In some cases lot might just be a name in the UI before being saved,
                                    # but we assume lot_id is present if serial tracking is configured correctly.
                                    lot = self.env['stock.lot'].search([('name', '=', line.lot_name), ('product_id', '=', move.product_id.id)], limit=1)
                                    lot_id = lot.id if lot else False

                                checklist_vals = []
                                if template:
                                    for t_line in template.line_ids:
                                        checklist_vals.append((0, 0, {
                                            'task_name': t_line.name,
                                        }))

                                AssemblyOrder.create({
                                    'picking_id': picking.id,
                                    'sales_order_id': picking.sale_id.id if picking.sale_id else False,
                                    'customer_id': picking.partner_id.id,
                                    'product_id': move.product_id.id,
                                    'serial_id': lot_id,
                                    'checklist_template_id': template.id if template else False,
                                    'checklist_line_ids': checklist_vals,
                                    'state': 'draft',
                                })
        return res
