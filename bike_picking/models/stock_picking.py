from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_status = fields.Selection([
        ('waiting_pick', 'Waiting Picking'),
        ('picking', 'Picking'),
        ('picked', 'Picked'),
        ('assembly', 'Assembly'),
        ('pdi', 'PDI'),
        ('ready_pickup', 'Ready Pickup'),
    ], string='Custom Status', default='waiting_pick', tracking=True)

    is_bike_order = fields.Boolean(
        string='Is Bike Order',
        compute='_compute_is_bike_order',
        store=True,
    )

    @api.depends('move_ids.product_id.is_bike')
    def _compute_is_bike_order(self):
        for picking in self:
            picking.is_bike_order = any(move.product_id.is_bike for move in picking.move_ids)

    def action_start_picking(self):
        for picking in self:
            if picking.picking_status == 'waiting_pick':
                picking.picking_status = 'picking'

    def button_validate(self):
        # 1. Custom validation trước khi chạy hàm chuẩn của Odoo
        for picking in self:
            if picking.picking_status == 'picking':
                for move in picking.move_ids:
                    if move.product_id.is_bike:
                        # Điểm 4: Dùng move.quantity (số lượng thực tế nhặt/done trong odoo mới) 
                        # thay vì move.product_uom_qty (số lượng yêu cầu) để hỗ trợ Backorder
                        total_qty_assigned = sum(
                            line.quantity for line in move.move_line_ids
                            if line.lot_id or line.lot_name
                        )
                        if total_qty_assigned < move.quantity:
                            raise UserError(
                                f"Serial number is required for "
                                f"{move.product_id.display_name} "
                                f"before completing picking."
                            )

        # 2. Gọi hàm gốc để Odoo xử lý việc xuất kho (đổi state sang 'done', tạo backorder...)
        res = super().button_validate()

        # 3. Điều hướng (Routing) sau khi phiếu kho đã Validate thành công
        # Lưu ý: res trả về có thể là một dict chứa action (ví dụ popup backorder).
        # Ta chỉ cập nhật picking_status nếu phiếu đã thực sự chuyển sang 'done'
        for picking in self:
            if picking.state == 'done':
                requires_assembly = any(move.product_id.is_assembly_required for move in picking.move_ids if move.product_id.is_bike)
                
                # Cập nhật status
                if picking.is_bike_order:
                    if requires_assembly:
                        picking.picking_status = 'assembly'
                    else:
                        picking.picking_status = 'pdi'
                else:
                    picking.picking_status = 'picked'
                    
        return res
