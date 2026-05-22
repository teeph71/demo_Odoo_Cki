from odoo import api, fields, models
class QuotationLostWizard(models.TransientModel):
    _name = 'quotation.lost.wizard'
    _description = 'Quotation Lost Wizard'

    sale_order_id = fields.Many2one('sale.order', required=True)
    action_type = fields.Selection([
        ('lost_revision', 'Create New Revision'),
        ('lost_only', 'Mark Lost Only')
    ], string="Action", default='lost_revision', required=True)

    lost_reason_id = fields.Many2one('sale.lost.reason', string='Reason', required=True)
    note = fields.Text(string="Note")

    # Hàm xử lý khi người dùng xác nhận hành động
    def action_confirm(self):
        self.ensure_one()
        sale = self.sale_order_id

        # 1. Hủy đơn hiện tại
        sale.write({
            'x_is_lost': True,
            'x_lost_reason_id': self.lost_reason_id.id,
            'x_lost_note': self.note,
            'state': 'cancel',
        })

        # 2. Xử lý tạo Revision
        if self.action_type == 'lost_revision':
            base_name = sale.name.split('-REV')[0]
            next_rev = sale.x_revision_no + 1
            new_name = f"{base_name}-REV{next_rev}"

            new_order = sale.copy({
                'name': new_name,
                'x_parent_quotation_id': sale.id,
                'x_revision_no': next_rev,
                'x_is_lost': False,
                'state': 'draft',
                'x_lost_reason_id': False,
                'x_lost_note': False,
            })

            # Mở thẳng đơn hàng mới
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': new_order.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # 3. Nếu chỉ Mark Lost thì chỉ đóng Wizard
        return {'type': 'ir.actions.act_window_close'}