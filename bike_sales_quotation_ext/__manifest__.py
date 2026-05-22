
{
    'name': 'Bike Sales Quotation Extension',
    'version': '1.1',
    'depends': ['sale', 'bicycle_membership'],
    'category': 'Sales',
    'summary': 'Đánh dấu lý do lost và giảm giá theo hạng thành viên',
    'data': [
        'security/ir.model.access.csv',
        'views/sale_lost_reason_views.xml',
        'views/sale_order_views.xml',
        'wizard/quotation_lost_wizard_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
}
