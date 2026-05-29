{
    'name': 'Bike PDI (Pre-Delivery Inspection)',
    'version': '1.0',
    'category': 'Operations',
    'summary': 'Quản lý quy trình kiểm định chất lượng xe đạp (PDI)',
    'description': """
        Module quản lý quy trình PDI cho xe đạp:
        - Tự động sinh PDI Checklist sau khi Lắp ráp hoặc xuất kho.
        - Quản lý Template Checklist theo Category.
        - Khóa giao hàng (Delivery) nếu xe chưa đạt chuẩn (Failed PDI).
        - Quản lý trạng thái PDI cho Sales.
    """,
    'author': 'Odoo Consultant',
    'depends': ['base', 'stock', 'sale_management', 'bike_assembly'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/ir_sequence.xml',
        'views/pdi_menus.xml',
        'views/pdi_template_views.xml',
        'views/pdi_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
