# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
