{
    'name': 'Custom e-Invoice Integration',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Tích hợp nút phát hành Hóa đơn điện tử mô phỏng',
    'depends': ['account'], # Kế thừa từ module Kế toán (Invoicing)
    'data': [
        'security/einvoice_security.xml'
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
}