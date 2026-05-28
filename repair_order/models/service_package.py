from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BikeRepairServicePackage(models.Model):
    _name = 'bike.repair.service.package'
    _description = 'Bike Repair Service Package'
    _order = 'sequence, name'

    name = fields.Char(string='Package Name', required=True)
    code = fields.Char(string='Package Code')
    price = fields.Float(string='Package Price', required=True)
    checklist_template_ids = fields.Many2many(
        'bike.repair.checklist.template',
        string='Checklist Templates',
    )
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    repair_order_ids = fields.One2many(
        'bike.repair.order',
        'service_package_id',
        string='Repair Orders'
    )

    product_id = fields.Many2one(
        'product.product', 
        string='Linked Product',
        readonly=True,
        ondelete='restrict'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Tạo một sản phẩm dịch vụ tương ứng trong hệ thống Odoo"""
        for vals in vals_list:
            product = self.env['product.product'].create({
                'name': vals.get('name'),
                'type': 'service',
                'list_price': vals.get('price', 0.0),
                'sale_ok': True,     
                'purchase_ok': False,
                'default_code': vals.get('code'),
            })
            vals['product_id'] = product.id
            
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        # Nếu bạn đổi tên hoặc giá của Package, cập nhật luôn vào Product cho đồng bộ
        if 'name' in vals or 'price' in vals:
            for rec in self:
                if rec.product_id:
                    update_vals = {}
                    if 'name' in vals:
                        update_vals['name'] = vals['name']
                    if 'price' in vals:
                        update_vals['list_price'] = vals['price']
                    rec.product_id.write(update_vals)
        return res