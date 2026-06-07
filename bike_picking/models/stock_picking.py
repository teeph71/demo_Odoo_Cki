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

    is_pick_transfer = fields.Boolean(
        string='Is Pick Transfer',
        compute='_compute_is_pick_transfer',
        store=False,
    )

    @api.depends('picking_type_id')
    def _compute_is_pick_transfer(self):
        for picking in self:
            if not picking.picking_type_id:
                picking.is_pick_transfer = False
                continue
            
            type_name = (picking.picking_type_id.name or '').lower()
            seq_code = (picking.picking_type_id.sequence_code or '').upper()
            
            is_pack_or_out = (
                seq_code in ['PACK', 'OUT'] or 
                picking.picking_type_id.code == 'outgoing' or
                any(kw in type_name for kw in ['pack', 'đóng gói', 'dong goi', 'delivery', 'giao hàng', 'giao hang', 'out'])
            )
            
            is_pick = (
                seq_code == 'PICK' or 
                any(kw in type_name for kw in ['pick', 'lấy hàng', 'lay hang'])
            )
            
            # Default to showing it if it's explicitly a pick, or if it's not a pack/out
            if is_pack_or_out and not is_pick:
                picking.is_pick_transfer = False
            else:
                # If we have 1-step delivery, sequence_code is OUT, so it would be hidden by the above logic.
                # But wait, if they have picking, packing, delivery, they must be using 2-step or 3-step.
                # So if it's OUT, hide it. If it's PACK, hide it. Otherwise show it.
                picking.is_pick_transfer = True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Xóa giá trị mặc định 'waiting_pick' nếu không phải là phiếu Pick
            if not record.is_pick_transfer:
                record.picking_status = False
        return records

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
        return res

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            # Chỉ cập nhật trạng thái cho các phiếu Pick
            if not picking.is_pick_transfer:
                continue
                
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
