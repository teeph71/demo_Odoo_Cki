from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleLostReason(models.Model):
    _name = 'sale.lost.reason'
    _description = 'Sale Lost Reason'

    name = fields.Char(required=True)
    description = fields.Text(string="Definition")
    active = fields.Boolean('Active', default=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if record.name:
                existing = self.search([
                    ('id', '!=', record.id),
                    ('name', '=ilike', record.name.strip())
                ], limit=1)

                if existing:
                    raise ValidationError(
                        "Lý do với tên '%s' đã tồn tại." % record.name.strip()
                    )