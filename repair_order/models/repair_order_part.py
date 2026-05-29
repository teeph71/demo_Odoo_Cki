from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BikeRepairOrderPart(models.Model):
    _name = 'bike.repair.order.part'
    _description = 'Repair Order Part Line'
    _order = 'id'

    order_id = fields.Many2one(
        'bike.repair.order',
        string='Repair Order',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="['|', ('name', 'ilike', 'Phụ kiện'), ('categ_id.name', 'ilike', 'Phụ kiện')]",
    )
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_cost = fields.Float(string='Unit Cost', compute='_compute_unit_cost', store=True)
    line_cost = fields.Float(string='Line Cost', compute='_compute_line_cost', store=True)

    sale_line_id = fields.Many2one('sale.order.line', string='Related Sale Line', ondelete='set null')

    @api.depends('product_id')
    def _compute_unit_cost(self):
        for rec in self:
            if rec.product_id:
                rec.unit_cost = rec.product_id.standard_price or rec.product_id.list_price or 0.0
            else:
                rec.unit_cost = 0.0

    @api.depends('unit_cost', 'quantity')
    def _compute_line_cost(self):
        for rec in self:
            rec.line_cost = rec.unit_cost * (rec.quantity or 0.0)

    @api.constrains('quantity')
    def _check_positive_values(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError('Số lượng phải lớn hơn 0.')
            
    def _check_order_state(self):
        for rec in self:
            if rec.order_id.state in ['done', 'cancel']:
                raise UserError(_("Bạn không thể thay đổi thông tin linh kiện khi đơn sửa chữa đã hoàn thành hoặc bị huỷ!"))

    @api.model_create_multi
    def create(self, vals_list):
        records = super(BikeRepairOrderPart, self).create(vals_list)
        for rec in records:
            rec._check_order_state()
            if rec.order_id.sale_order_id:
                sale_line = self.env['sale.order.line'].create({
                    'order_id': rec.order_id.sale_order_id.id,
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.quantity,
                    'price_unit': rec.unit_cost,
                    'name': rec.product_id.name,
                })
                rec.with_context(skip_so_sync=True).write({'sale_line_id': sale_line.id})
        return records

    def write(self, vals):
        self._check_order_state()
        res = super(BikeRepairOrderPart, self).write(vals)
        if not self._context.get('skip_so_sync'):
            for rec in self:
                if rec.sale_line_id:
                    rec.sale_line_id.write({
                        'product_uom_qty': rec.quantity,
                        'price_unit': rec.unit_cost,
                    })
        return res

    def unlink(self):
        self._check_order_state()
        sale_lines_to_unlink = self.mapped('sale_line_id').filtered(lambda l: l.exists())
        if sale_lines_to_unlink:
            sale_lines_to_unlink.unlink()
        return super(BikeRepairOrderPart, self).unlink()