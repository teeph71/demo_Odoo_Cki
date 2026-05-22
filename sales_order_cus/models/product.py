# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty_duration = fields.Integer(
        string='Thời hạn bảo hành (tháng)',
        default=0,
        help='Nhập số tháng bảo hành cho sản phẩm. Ví dụ: 24 = 2 năm, 36 = 3 năm.'
    )

    @api.constrains('warranty_duration')
    def _check_warranty_duration(self):
        for product in self:
            if product.warranty_duration < 0:
                raise ValidationError('Thời hạn bảo hành không được nhỏ hơn 0.')
