{
    'name': 'Custom Bicycle Customer',
    'version': '1.0',
    'category': 'Sales',
    'depends': ['base', 'sale'],
    'summary': 'Quản lý khách hàng và hạng thành viên cho EcoBike',
    'data': [
        'security/ir.model.access.csv',
        'views/member_tier_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}