from odoo import models, fields, api
from odoo.exceptions import ValidationError

class BicycleMemberTier(models.Model):
    _name = 'bicycle.member.tier'
    _description = 'Bicycle Member Tier'
    _order = 'min_points asc'

    name = fields.Char(string='Tier Name', required=True)
    min_points = fields.Integer(string='Minimum Points', required=True, default=0)
    
    # Benefits
    discount_rate = fields.Float(string='Discount Rate (%)', help="Cài đặt % Giảm giá cho hạng này")
    points_multiplier = fields.Float(string='Points Multiplier', default=1.0, help="Hệ số nhân điểm thưởng")
    benefits_description = fields.Html(string='Benefits Description')
    free_maintenance_sessions = fields.Integer(string="Free Maintenance Sessions", default=0)

    # Ràng buộc các hệ số phải là số nguyên ≥ 0
    @api.constrains('min_points', 'points_multiplier', 'free_maintenance_sessions')
    def _check_business_rules(self):
        for record in self:
            if record.min_points < 0:
                raise ValidationError("Điểm tối thiểu phải là số nguyên ≥ 0.")
            
            if record.discount_rate < 0 or record.discount_rate > 100:
                raise ValidationError("Tỷ lệ giảm giá phải từ 0% đến 100%.")
            
            if record.points_multiplier <= 0:
                raise ValidationError("Hệ số tích điểm phải lớn hơn 0.")

            if record.free_maintenance_sessions < 0:
                raise ValidationError("Số buổi bảo trì miễn phí phải ≥ 0.")