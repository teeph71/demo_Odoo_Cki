from odoo import models, fields

class AssemblyTemplate(models.Model):
    _name = 'bike.assembly.template'
    _description = 'Assembly Checklist Template'

    name = fields.Char(string='Template Name', required=True)
    category_id = fields.Many2one('product.category', string='Product Category')
    line_ids = fields.One2many('bike.assembly.template.line', 'template_id', string='Checklist Items')


class AssemblyTemplateLine(models.Model):
    _name = 'bike.assembly.template.line'
    _description = 'Assembly Checklist Template Line'
    _order = 'sequence'

    template_id = fields.Many2one('bike.assembly.template', string='Template', required=True, ondelete='cascade')
    name = fields.Char(string='Task Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
