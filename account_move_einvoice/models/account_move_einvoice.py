from odoo import models, fields, api
from odoo.exceptions import UserError
import random
import string

class AccountMove(models.Model):
    _inherit = 'account.move' # Kế thừa bảng hóa đơn gốc

    # 1. Thêm 2 trường dữ liệu mới
    einvoice_status = fields.Selection([
        ('draft', 'Not Issued'),
        ('sent', 'Issued'),
        ('error', 'API Error')
    ], string='e-Invoice Status', default='draft', copy=False)
    
    einvoice_code = fields.Char(string='Lookup Code', readonly=True, copy=False)

    # 2. Hàm thực thi khi bấm nút "Issue e-Invoice"
    def action_send_einvoice(self):
        for record in self:
            # Ràng buộc: Chỉ hóa đơn đã Posted mới được phát hành
            if record.state != 'posted':
                raise UserError("You can only issue an e-Invoice when the invoice is in Posted state!")
            
            # Mô phỏng gọi API thành công: Chuyển trạng thái và tạo mã ngẫu nhiên
            random_code = ''.join(random.choices(string.digits, k=10))
            record.einvoice_status = 'sent'
            record.einvoice_code = f"VNPT-{random_code}"
            
            # Ghi Log vào Chatter bên phải màn hình
            record.message_post(body=f"e-Invoice issued successfully. Lookup Code: VNPT-{random_code}")