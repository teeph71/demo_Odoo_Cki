from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    warranty_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='bike_warranty_config_category_rel',
        column1='config_id',
        column2='category_id',
        string='Loại sản phẩm cần phiếu bảo hành',
        help='Chọn các loại sản phẩm sẽ tự động tạo phiếu bảo hành khi bán.\n'
             'Ví dụ: Xe đạp, Xe máy điện. Bỏ qua phụ kiện, mũ, chai nước,...',
    )

    def set_values(self):
        """Lưu danh sách category ID vào ir.config_parameter."""
        super().set_values()
        category_ids_str = ','.join(
            str(c.id) for c in self.warranty_category_ids
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'bike_warranty.warranty_category_ids',
            category_ids_str,
        )

    @api.model
    def get_values(self):
        """Đọc danh sách category ID từ ir.config_parameter."""
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'bike_warranty.warranty_category_ids', ''
        )
        category_ids = [
            int(x) for x in param.split(',') if x.strip().isdigit()
        ]
        res['warranty_category_ids'] = [(6, 0, category_ids)]
        return res
