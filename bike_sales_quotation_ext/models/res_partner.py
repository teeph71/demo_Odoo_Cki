from odoo import fields, models
class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_membership_discount = fields.Float()
    x_membership_renewal_date = fields.Date()

    x_discount_active_after_renewal = fields.Boolean(default=True, string="Activate Discount After Renewal")
