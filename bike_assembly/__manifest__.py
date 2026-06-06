{
    'name': 'Bike Workshop (Assembly)',
    'version': '1.0',
    'category': 'Operations',
    'summary': 'Quản lý quy trình lắp ráp xe đạp sau khi lấy hàng',
    'description': """
        Module quản lý quy trình Assembly cho xe đạp:
        - Tự động sinh Assembly Task từ Picking.
        - Quản lý Template Checklist theo Category.
        - Phân công Kỹ thuật viên (Technician).
        - Quản lý trạng thái Assembly và Rework.
    """,
    'author': 'Odoo Consultant',
    'depends': ['base', 'stock', 'sale_management', 'bike_picking', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/assembly_template_views.xml',
        'views/assembly_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
