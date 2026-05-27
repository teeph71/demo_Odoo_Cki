from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warranty_ids = fields.One2many(
        comodel_name='bike.warranty',
        inverse_name='sale_order_id',
        string='Warranty Cards',
    )
    warranty_count = fields.Integer(
        string='Warranty Count',
        compute='_compute_warranty_count',
    )

    @api.depends('warranty_ids')
    def _compute_warranty_count(self):
        for order in self:
            order.warranty_count = len(order.warranty_ids)

    # ─── Tự động tạo phiếu BH khi xác nhận SO ───────────────────────────────

    def action_confirm(self):
        """Override: automatically create warranty cards after confirming SO."""
        res = super().action_confirm()
        for order in self:
            order._auto_create_warranty_cards()
        return res

    def _get_warranty_category_ids(self):
        """Read the list of category IDs configured in Settings."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            'bike_warranty.warranty_category_ids', ''
        )
        return [int(x) for x in param.split(',') if x.strip().isdigit()]

    def _auto_create_warranty_cards(self):
        """
        Automatically create warranty cards for each product line in the SO.

        Conditions for creating a warranty card:
          1. product.category is in the list configured in Settings
             (no extra field added to product.category master data)
          2. product.warranty_duration > 0

        Skip: accessories, helmets, water bottles, etc.
        (categories not selected in Settings)
        """
        warranty_category_ids = self._get_warranty_category_ids()
        if not warranty_category_ids:
            return  # Not configured → skip

        start_date = (
            self.date_order.date() if self.date_order else fields.Date.today()
        )
        warranties_to_create = []

        for line in self.order_line:
            # Condition 1: category must be in the configured list
            if line.product_id.categ_id.id not in warranty_category_ids:
                continue

            # Condition 2: product must have warranty_duration > 0
            template = line.product_id.product_tmpl_id
            warranty_duration = getattr(template, 'warranty_duration', 0) or 0
            if warranty_duration <= 0:
                continue

            # Create 1 warranty card per quantity in the SO line
            qty = int(line.product_uom_qty) or 1
            for _ in range(qty):
                warranties_to_create.append({
                    'sale_order_id': self.id,
                    'sale_order_line_id': line.id,
                    'product_id': line.product_id.id,
                    'warranty_duration': warranty_duration,
                    'start_date': start_date,
                    'partner_id': self.partner_id.id,
                    'state': 'active',
                })

        if warranties_to_create:
            self.env['bike.warranty'].create(warranties_to_create)


    # ─── Smart button ─────────────────────────────────────────────────────────

    def action_view_warranties(self):
        """Smart button: view all warranty cards for this SO."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bike_warranty.action_bike_warranty'
        )
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {
            'default_sale_order_id': self.id,
            'default_partner_id': self.partner_id.id,
        }
        if self.warranty_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.warranty_ids[0].id
        return action

    def action_create_warranty_from_so(self):
        """Open form to manually create a warranty card from the current SO."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Warranty Card',
            'res_model': 'bike.warranty',
            'view_mode': 'form',
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_start_date': (
                    self.date_order.date() if self.date_order else fields.Date.today()
                ),
            },
            'target': 'new',
        }
