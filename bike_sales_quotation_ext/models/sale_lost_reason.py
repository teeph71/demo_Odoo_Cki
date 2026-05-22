from odoo import fields, models
class SaleLostReason(models.Model):
    _name = 'sale.lost.reason'
    _description = 'Sale Lost Reason'

    name = fields.Char(required=True)
    description = fields.Text(string="Definition")