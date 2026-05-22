from odoo import models, fields, api
from odoo.exceptions import UserError
import random
import string

class AccountMove(models.Model):
    _inherit = 'account.move' # Kế thừa bảng hóa đơn gốc

    # 1. Thêm 2 trường dữ liệu mới
    einvoice_status = fields.Selection([
        ('draft', 'Chưa phát hành'),
        ('sent', 'Đã phát hành HĐĐT'),
        ('error', 'Lỗi API')
    ], string='Trạng thái e-Invoice', default='draft', copy=False)
    
    einvoice_code = fields.Char(string='Mã tra cứu HĐĐT', readonly=True, copy=False)

    # 2. Hàm thực thi khi bấm nút "Phát hành e-Invoice"
    def action_send_einvoice(self):
        for record in self:
            # Ràng buộc: Chỉ hóa đơn đã Posted mới được phát hành
            if record.state != 'posted':
                raise UserError("Chỉ có thể phát hành HĐĐT khi hóa đơn đã được Vào sổ (Posted)!")
            
            # Mô phỏng gọi API thành công: Chuyển trạng thái và tạo mã ngẫu nhiên
            random_code = ''.join(random.choices(string.digits, k=10))
            record.einvoice_status = 'sent'
            record.einvoice_code = f"VNPT-{random_code}"
            
            # Ghi Log vào Chatter bên phải màn hình
            record.message_post(body=f"Đã phát hành Hóa đơn điện tử thành công. Mã tra cứu: VNPT-{random_code}")