from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_bike = fields.Boolean(
        string='Is Bike',
        help=('Check this box if the product is a bike that requires '
              'serial number tracking during picking.')
    )
    is_assembly_required = fields.Boolean(
        string='Is Assembly Required',
        help='Check this box if the bike requires assembly after picking.'
    )
