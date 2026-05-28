
{
    'name': 'Custom CK Han',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Kế thừa quy trình Sales Order',
    'description': """ Kế thừa quy trình Sales Order và phân quyền vai trò chuyên sâu """,
    'author': 'CK Han',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'sale_management',
        'sale_stock',
    ],
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
