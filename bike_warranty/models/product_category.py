from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    needs_warranty_card = fields.Boolean(
        string='Cần phiếu bảo hành',
        default=False,
        help='Dành cho các loại xe cần tạo phiếu bảo hành khi bán.\n'
             'Ví dụ: Xe đạp ✅ | Mũ bảo hiểm, Chai nước ❌',
    )
