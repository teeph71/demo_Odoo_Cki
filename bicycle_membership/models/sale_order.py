from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_loyalty_processed = fields.Boolean(default=False, copy=False)
    x_loyalty_points_earned = fields.Integer(default=0, copy=False)

    def action_confirm(self):
        res = super().action_confirm()
        
        for order in self:
            if not order.partner_id.x_is_member or order.x_loyalty_processed:
                continue

            try:
                # Tạo một Savepoint cho riêng việc cộng điểm
                with self.env.cr.savepoint():
                    partner = order.partner_id.sudo()
                    self.env.cr.execute("SELECT id FROM res_partner WHERE id=%s FOR UPDATE", (partner.id,))
                    
                    multiplier = partner.x_member_tier_id.points_multiplier or 1.0
                    points = int(round(order.amount_total / 10000 * multiplier))

                    if points > 0:
                        partner.write({
                            'x_total_spent': partner.x_total_spent + order.amount_total,
                            'x_loyalty_points': partner.x_loyalty_points + points,
                        })
                        order.sudo().write({
                            'x_loyalty_points_earned': points,
                            'x_loyalty_processed': True,
                        })
                        _logger.info("[LOYALTY] +%d pts cho đơn %s", points, order.name)
            except Exception as e:
                _logger.error("[LOYALTY ERROR] Không thể cộng điểm cho đơn %s: %s", order.name, str(e))
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        
        for order in self:
            if not order.x_loyalty_processed or order.x_loyalty_points_earned <= 0:
                continue

            try:
                # Sử dụng Savepoint để rollback điểm khi huỷ đơn
                with self.env.cr.savepoint():
                    partner = order.partner_id.sudo()
                    # Lock partner để đảm bảo tính chính xác của số dư điểm
                    self.env.cr.execute("SELECT id FROM res_partner WHERE id=%s FOR UPDATE", (partner.id,))

                    points_to_remove = order.x_loyalty_points_earned
                    
                    new_points = max(0, partner.x_loyalty_points - points_to_remove)
                    new_spent = max(0.0, partner.x_total_spent - order.amount_total)

                    partner.write({
                        'x_loyalty_points': new_points,
                        'x_total_spent': new_spent,
                    })
                    
                    # Đánh dấu đã rollback thành công
                    order.sudo().write({
                        'x_loyalty_points_earned': 0,
                        'x_loyalty_processed': False,
                    })
                    _logger.info("[LOYALTY ROLLBACK] Trừ %d pts từ đơn %s", points_to_remove, order.name)
            except Exception as e:
                _logger.error("[LOYALTY ROLLBACK ERROR] Đơn %s: %s", order.name, str(e))
        return res
    
    