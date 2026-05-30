
{
    'name': 'Sales Order Extension',
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
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
