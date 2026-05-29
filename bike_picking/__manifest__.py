{
    'name': 'Bike Picking Customization',
    'version': '1.0',
    'summary': 'Custom picking process for bikes',
    'description': (
        'Adds picking status and serial number tracking '
        'for bike assembly flow.'
    ),
    'category': 'Inventory',
    'author': 'Odoo Consultant',
    'depends': ['stock', 'sale_management'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
