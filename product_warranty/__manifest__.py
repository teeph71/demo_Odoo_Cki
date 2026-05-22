{
    'name': 'Quản lý thời gian bảo hành xe đạp',
    'version': '1.0',
    'summary': 'Thêm trường thời gian bảo hành vào form sản phẩm',
    'category': 'Sales',
    'author': 'Nhóm Dự Án ERP',
    'depends': ['product'],  
    'data': [
        'views/product_template_view.xml',  # <-- BẮT BUỘC PHẢI CÓ DÒNG NÀY để Odoo biết file giao diện ở đâu
    ],
    'installable': True,
    'application': True,
}