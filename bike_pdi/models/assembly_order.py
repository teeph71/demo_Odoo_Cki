from odoo import models

class BikeAssemblyOrder(models.Model):
    _inherit = 'bike.assembly.order'

    def action_complete_assembly(self):
        res = super().action_complete_assembly()
        
        Template = self.env['bike.pdi.template']
        template_cache = {}
        
        for order in self:
            categ_id = order.product_id.categ_id.id
            if categ_id not in template_cache:
                template = Template.search([('category_id', 'parent_of', categ_id)], limit=1, order='id desc')
                template_cache[categ_id] = template.id if template else False
            
            template_id = template_cache[categ_id]
                    
            self.env['bike.pdi.order'].create({
                'picking_id': order.picking_id.id,
                'sales_order_id': order.sales_order_id.id,
                'customer_id': order.customer_id.id,
                'product_id': order.product_id.id,
                'serial_id': order.serial_id.id,
                'checklist_template_id': template_id,
            })
            
        return res
