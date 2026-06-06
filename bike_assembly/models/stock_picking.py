from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        # Call the original method to handle status change and validations
        res = super()._action_done()

        AssemblyOrder = self.env['bike.assembly.order']
        Template = self.env['bike.assembly.template']
        
        # Điểm 2: Dùng Cache Gom nhóm Template để giải quyết triệt để lỗi N+1 Query
        template_cache = {}

        for picking in self:
            for move in picking.move_ids:
                if move.product_id.is_bike and move.product_id.is_assembly_required:
                    categ_id = move.product_id.categ_id.id
                    
                    # Điểm 3: Thêm order="id desc" để đảm bảo lấy Template của Category Con trước
                    if categ_id not in template_cache:
                        template = Template.search([('category_id', 'parent_of', categ_id)], limit=1, order='id desc')
                        template_cache[categ_id] = template.id if template else False
                        
                    template_id = template_cache[categ_id]
                    
                    # Tạo 1 đơn lắp ráp cho mỗi mã Serial (move_line)
                    for line in move.move_line_ids:
                        # lot_id mặc định đã có sau khi gọi super()._action_done()
                        if line.quantity > 0 and line.lot_id:
                            # Điểm 4: Việc sinh checklist sẽ do hàm create của model bike.assembly.order tự động lo
                            AssemblyOrder.create({
                                'picking_id': picking.id,
                                'sales_order_id': picking.sale_id.id if picking.sale_id else False,
                                'customer_id': picking.partner_id.id,
                                'product_id': move.product_id.id,
                                'serial_id': line.lot_id.id,
                                'checklist_template_id': template_id,
                                'state': 'draft',
                            })
        return res
