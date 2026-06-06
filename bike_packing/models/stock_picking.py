from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _check_bike_pdi_assembly_status(self):
        self.ensure_one()
        is_bike_order = any(move.product_id.is_bike for move in self.move_ids)
        if not is_bike_order:
            return

        # Tìm kiếm an toàn qua nhiều bước của luồng kho (Pick -> Pack -> Out)
        if self.sale_id:
            domain = [('sales_order_id', '=', self.sale_id.id)]
        elif self.group_id:
            domain = [('picking_id.group_id', '=', self.group_id.id)]
        else:
            domain = [('picking_id', '=', self.id)]

        # Kiểm tra PDI
        pdi_orders = self.env['bike.pdi.order'].search(domain)
        if not pdi_orders:
            raise UserError("Chưa thể xác nhận. Đơn hàng xe đạp này chưa có bản ghi kiểm định PDI.")
        if any(p.state != 'passed' for p in pdi_orders):
            raise UserError("Chưa thể xác nhận. Tất cả xe đạp phải được đánh giá ĐẠT PDI.")
        
        # Kiểm tra Lắp ráp
        requires_assembly = any(move.product_id.is_bike and move.product_id.is_assembly_required for move in self.move_ids)
        if requires_assembly:
            assembly_orders = self.env['bike.assembly.order'].search(domain)
            if not assembly_orders:
                raise UserError("Chưa thể xác nhận. Đơn hàng yêu cầu lắp ráp nhưng chưa có bản ghi Lắp ráp.")
            if any(a.state != 'completed' for a in assembly_orders):
                raise UserError("Chưa thể xác nhận. Chưa hoàn thành tất cả các hạng mục Lắp ráp.")

    def button_validate(self):
        for picking in self:
            type_name = (picking.picking_type_id.name or '').lower()
            seq_code = (picking.picking_type_id.sequence_code or '').upper()
            is_packing_transfer = seq_code == 'PACK' or any(kw in type_name for kw in ['pack', 'đóng gói', 'dong goi'])
            
            if is_packing_transfer:
                # Gọi hàm helper dùng chung để check PDI & Lắp ráp
                picking._check_bike_pdi_assembly_status()
                
            elif picking.picking_type_id.code == 'outgoing':
                # Kiểm tra khâu Đóng gói trước khi Giao hàng
                # Tìm Packing Order bằng sales_order_id hoặc group_id để tránh lỗi đứt gãy giữa các bước kho
                if picking.sale_id:
                    domain_pack = [('sales_order_id', '=', picking.sale_id.id)]
                elif picking.group_id:
                    domain_pack = [('picking_id.group_id', '=', picking.group_id.id)]
                else:
                    domain_pack = [('picking_id', '=', picking.id)]
                
                packing_orders = self.env['bike.packing.order'].search(domain_pack)
                if packing_orders:
                    unpacked = packing_orders.filtered(lambda p: p.state != 'packed')
                    if unpacked:
                        raise UserError("Không thể xác nhận phiếu Giao hàng (Delivery). Xe đạp chưa được Đóng gói hoàn tất.")
                        
        return super().button_validate()
