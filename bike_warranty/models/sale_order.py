from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warranty_ids = fields.One2many(
        comodel_name='bike.warranty',
        inverse_name='sale_order_id',
        string='Phiếu Bảo Hành',
    )
    warranty_count = fields.Integer(
        string='Số phiếu BH',
        compute='_compute_warranty_count',
    )

    @api.depends('warranty_ids')
    def _compute_warranty_count(self):
        for order in self:
            order.warranty_count = len(order.warranty_ids)

    # ─── Tự động tạo phiếu BH khi xác nhận SO ───────────────────────────────

    def action_confirm(self):
        """Override: tự động tạo phiếu bảo hành sau khi xác nhận SO."""
        res = super().action_confirm()
        for order in self:
            order._auto_create_warranty_cards()
        return res

    def _get_warranty_category_ids(self):
        """Đọc danh sách category ID được cấu hình trong Settings."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            'bike_warranty.warranty_category_ids', ''
        )
        return [int(x) for x in param.split(',') if x.strip().isdigit()]

    def _auto_create_warranty_cards(self):
        """
        Tạo phiếu bảo hành tự động cho từng dòng sản phẩm trong SO.

        Điều kiện để tạo phiếu BH:
          1. product.category nằm trong danh sách cấu hình tại Settings
             (không thêm field vào master data product.category)
          2. product.warranty_duration > 0

        Bỏ qua: phụ kiện, mũ bảo hiểm, chai nước,...
        (những category không được chọn trong Settings)
        """
        warranty_category_ids = self._get_warranty_category_ids()
        if not warranty_category_ids:
            return  # Chưa cấu hình → bỏ qua

        start_date = (
            self.date_order.date() if self.date_order else fields.Date.today()
        )
        warranties_to_create = []

        for line in self.order_line:
            # Điều kiện 1: category phải nằm trong danh sách cấu hình
            if line.product_id.categ_id.id not in warranty_category_ids:
                continue

            # Điều kiện 2: sản phẩm phải có thời hạn bảo hành > 0
            template = line.product_id.product_tmpl_id
            warranty_duration = getattr(template, 'warranty_duration', 0) or 0
            if warranty_duration <= 0:
                continue

            # Tạo 1 phiếu BH cho mỗi số lượng trong dòng SO
            qty = int(line.product_uom_qty) or 1
            for _ in range(qty):
                warranties_to_create.append({
                    'sale_order_id': self.id,
                    'sale_order_line_id': line.id,
                    'product_id': line.product_id.id,
                    'warranty_duration': warranty_duration,
                    'start_date': start_date,
                    'partner_id': self.partner_id.id,
                    'state': 'active',
                })

        if warranties_to_create:
            self.env['bike.warranty'].create(warranties_to_create)


    # ─── Smart button ─────────────────────────────────────────────────────────

    def action_view_warranties(self):
        """Smart button: xem tất cả phiếu BH của SO này."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bike_warranty.action_bike_warranty'
        )
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {
            'default_sale_order_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        if self.warranty_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.warranty_ids[0].id
        return action

    def action_create_warranty_from_so(self):
        """Mở form tạo phiếu bảo hành thủ công từ SO hiện tại."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tạo Phiếu Bảo Hành',
            'res_model': 'bike.warranty',
            'view_mode': 'form',
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_start_date': (
                    self.date_order.date() if self.date_order else fields.Date.today()
                ),
            },
            'target': 'new',
        }
