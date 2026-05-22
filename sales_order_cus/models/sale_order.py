# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    override_note = fields.Text(
        string='Ghi chú ghi đè tồn kho',
        help='Yêu cầu ghi chú khi quản lý bán hàng ghi đè đặt hàng vượt tồn kho khả dụng.'
    )

    def write(self, vals):
        for order in self:
            # Ngăn nhân viên bán hàng chỉnh sửa đơn hàng đã xuất kho (đầy đủ hoặc một phần)
            if order.delivery_status in ('full', 'partial') and not self.env.user.has_group('sale.group_sale_manager') and not self.env.su:
                raise UserError("Đơn hàng đã xuất kho, không được phép chỉnh sửa.")
        return super(SaleOrder, self).write(vals)

    def unlink(self):
        for order in self:
            # Ngăn nhân viên bán hàng xóa đơn hàng đã xuất kho (đầy đủ hoặc một phần)
            if order.delivery_status in ('full', 'partial') and not self.env.user.has_group('sale.group_sale_manager') and not self.env.su:
                raise UserError("Đơn hàng đã xuất kho, không được phép xóa.")
        return super(SaleOrder, self).unlink()
