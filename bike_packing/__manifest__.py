{
    'name': 'Bike Packing',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Manage bike packing process before delivery',
    'description': """
Bike Packing Process
====================
This module handles the packing process after the Pre-Delivery Inspection (PDI) passes.
- Automatic creation of Packing Orders.
- Manage packing checklist.
- Prevent delivery validation until packing is completed.
    """,
    'author': 'Odoo Consultant',
    'depends': ['bike_pdi', 'sale', 'stock'],
    'data': [
        'security/packing_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/packing_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
