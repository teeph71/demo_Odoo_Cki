from odoo import models

class BikeAssemblyOrder(models.Model):
    _inherit = 'bike.assembly.order'

    def action_complete_assembly(self):
        res = super().action_complete_assembly()
        
        for order in self:
            Template = self.env['bike.pdi.template']
            template = Template.search([('category_id', 'parent_of', order.product_id.categ_id.id)], limit=1)
            
            checklist_vals = []
            if template:
                for t_line in template.line_ids:
                    checklist_vals.append((0, 0, {
                        'item_name': t_line.name,
                    }))
                    
            self.env['bike.pdi.order'].create({
                'picking_id': order.picking_id.id,
                'sales_order_id': order.sales_order_id.id,
                'customer_id': order.customer_id.id,
                'product_id': order.product_id.id,
                'serial_id': order.serial_id.id,
                'checklist_template_id': template.id if template else False,
                'checklist_line_ids': checklist_vals,
            })
            
        return res
