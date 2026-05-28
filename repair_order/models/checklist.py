from odoo import models, fields

class BikeRepairChecklistTemplate(models.Model):
    _name = 'bike.repair.checklist.template'
    _description = 'Checklist Template'
    name = fields.Char(required=True)
    line_ids = fields.One2many('bike.repair.checklist.line', 'template_id')

class BikeRepairChecklistLine(models.Model):
    _name = 'bike.repair.checklist.line'
    _description = 'Checklist Line'

    name = fields.Char(string='Task', required=True)
    completed = fields.Boolean(string='Completed', default=False)
    notes = fields.Text(string='Notes')
    
    template_id = fields.Many2one('bike.repair.checklist.template', ondelete='cascade')
    order_id = fields.Many2one('bike.repair.order', ondelete='cascade')