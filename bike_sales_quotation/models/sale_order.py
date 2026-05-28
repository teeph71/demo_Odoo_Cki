from odoo import api, fields, models
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_is_lost = fields.Boolean(string="Is Lost", default=False)
    x_revision_no = fields.Integer(string="Revision Number", default=0)
    x_parent_quotation_id = fields.Many2one('sale.order', string="Original Quotation")
    x_lost_reason_id = fields.Many2one('sale.lost.reason', string="Lost Reason")
    x_lost_note = fields.Text(string="Lost Note")

    x_member_tier_id_display = fields.Many2one(
        related='partner_id.x_member_tier_id', 
        string="Customer Tier", 
        readonly=True,
        store=False
    )
    x_is_member_display = fields.Boolean(
        related='partner_id.x_is_member', 
        readonly=True,
        store=False
    )

    # --- LOGIC CHIẾT KHẤU THEO HẠNG ---
    @api.onchange('partner_id')
    def _onchange_partner_id_update_tier_discount(self):
        tier_discount = 0.0
        if self.partner_id and self.partner_id.x_is_member and self.partner_id.x_member_tier_id:
            tier_discount = self.partner_id.x_member_tier_id.discount_rate
        
        for line in self.order_line:
            line.discount = tier_discount

    # --- HÀM ĐÁNH DẤU LOST  ---
    def action_mark_lost(self):
        self.ensure_one()
        return {
            'name': 'Mark Lost',
            'type': 'ir.actions.act_window',
            'res_model': 'quotation.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id}
        }

    # --- CRON TỰ ĐỘNG ĐÁNH DẤU LOST CHO QUOTATION HẾT HẠN ---
    @api.model
    def cron_auto_mark_lost(self):
        today = fields.Date.today()
        quotations = self.search([
            ('state', 'in', ['draft', 'sent']),
            ('validity_date', '<', today),
            ('x_is_lost', '=', False)
        ])
        if quotations:
            quotations.write({'x_is_lost': True, 'state': 'cancel'})

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Tự động gán chiết khấu khi thêm sản phẩm mới vào đơn hàng
    @api.onchange('product_id')
    def _onchange_product_id_set_tier_discount(self):
        partner = self.order_id.partner_id
        if partner and partner.x_is_member and partner.x_member_tier_id:
            self.discount = partner.x_member_tier_id.discount_rate
        else:
            self.discount = 0.0

    # --- Số lượng không âm, Giá không thấp hơn giá vốn ---
    @api.constrains('product_uom_qty', 'price_unit', 'product_id')
    def _check_qty_and_price(self):
        for line in self:
            if not line.product_id:
                continue

            if line.product_uom_qty < 0:
                raise ValidationError(f"Số lượng sản phẩm '{line.product_id.name}' không được âm.")

            if line.price_unit < line.product_id.standard_price:
                raise ValidationError(
                    f"Giá bán của sản phẩm '{line.product_id.name}' ({line.price_unit}) "
                    f"không được thấp hơn giá vốn ({line.product_id.standard_price})."
                )