from odoo import models, fields

class BikePdiTemplate(models.Model):
    _name = 'bike.pdi.template'
    _description = 'PDI Template'

    name = fields.Char(string='Template Name', required=True)
    category_id = fields.Many2one('product.category', string='Product Category', required=True)
    line_ids = fields.One2many('bike.pdi.template.line', 'template_id', string='Checklist Items')

class BikePdiTemplateLine(models.Model):
    _name = 'bike.pdi.template.line'
    _description = 'PDI Template Line'

    template_id = fields.Many2one('bike.pdi.template', string='Template', ondelete='cascade')
    name = fields.Char(string='Task Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    note = fields.Text(string='Note')
