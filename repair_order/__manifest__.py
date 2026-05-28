{
    'name': 'Bike Repair',
    'version': '1.0',
    'summary': 'Bike Repair Management',
    'category': 'Services',
    'depends': [
        'base',
        'mail',
        'sale',
        'stock',
        'account',
        'hr',
        'bike_warranty',
        'bicycle_membership',
    ],
    'data': [
    'security/ir.model.access.csv',
    'security/repair_order_security.xml',
    'data/sequence.xml',

    'views/service_package_views.xml',
    'views/repair_order_views.xml',
    'views/menu_views.xml',
    'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
