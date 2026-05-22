# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id', 'product_uom_qty')
    def _check_inventory_availability(self):
        for line in self:
            # Chỉ kiểm tra đối với các sản phẩm lưu kho vật lý (storable/physical products)
            if not line.product_id or not (line.product_id.is_storable or line.product_id.type == 'product') or line.product_uom_qty <= 0:
                continue

            # Lấy số lượng tồn kho khả dụng (Free to Use Quantity) theo kho hàng của Đơn bán hàng
            warehouse = line.warehouse_id or line.order_id.warehouse_id
            product_in_warehouse = line.product_id.with_context(warehouse_id=warehouse.id)
            available_qty = product_in_warehouse.free_qty

            # Quy đổi số lượng đặt về đơn vị đo lường (UoM) mặc định của sản phẩm để so sánh chính xác với tồn kho
            ordered_qty = line.product_uom_qty
            if line.product_uom_id and line.product_id.uom_id and line.product_uom_id != line.product_id.uom_id:
                ordered_qty = line.product_uom_id._compute_quantity(ordered_qty, line.product_id.uom_id)

            if ordered_qty > available_qty:
                is_manager = self.env.user.has_group('sale.group_sale_manager')
                if not is_manager:
                    raise ValidationError(
                        f"Không thể đặt số lượng ({line.product_uom_qty} {line.product_uom_id.name}) vượt quá tồn kho khả dụng ({available_qty} {line.product_id.uom_id.name}) "
                        f"cho sản phẩm '{line.product_id.name}'.\n"
                        "Chỉ Quản lý bán hàng mới có quyền ghi đè."
                    )
                else:
                    # Yêu cầu Quản lý bán hàng phải điền ghi chú giải trình lý do ghi đè
                    if not line.order_id.override_note or not line.order_id.override_note.strip():
                        raise ValidationError(
                            f"Đơn hàng đang đặt số lượng vượt quá tồn kho khả dụng cho sản phẩm '{line.product_id.name}'.\n"
                            "Yêu cầu phải nhập lý do vào trường 'Ghi chú ghi đè tồn kho' trên đơn hàng."
                        )

    def write(self, vals):
        for line in self:
            # Ngăn nhân viên bán hàng chỉnh sửa chi tiết đơn hàng đã xuất kho (đầy đủ hoặc một phần)
            if line.order_id.delivery_status in ('full', 'partial') and not self.env.user.has_group('sale.group_sale_manager') and not self.env.su:
                raise UserError("Đơn hàng đã xuất kho, không được phép chỉnh sửa chi tiết đơn hàng.")
        return super(SaleOrderLine, self).write(vals)

    def unlink(self):
        for line in self:
            # Ngăn nhân viên bán hàng xóa chi tiết đơn hàng đã xuất kho (đầy đủ hoặc một phần)
            if line.order_id.delivery_status in ('full', 'partial') and not self.env.user.has_group('sale.group_sale_manager') and not self.env.su:
                raise UserError("Đơn hàng đã xuất kho, không được phép xóa chi tiết đơn hàng.")
        return super(SaleOrderLine, self).unlink()
