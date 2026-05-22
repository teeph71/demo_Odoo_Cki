from odoo import models, fields, api
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_status = fields.Selection([
        ('waiting_pick', 'Waiting Picking'),
        ('picking', 'Picking'),
        ('picked', 'Picked'),
        ('assembly', 'Assembly'),
        ('pdi', 'PDI'),
        ('ready_pickup', 'Ready Pickup'),
    ], string='Custom Status', default='waiting_pick', tracking=True)

    is_bike_order = fields.Boolean(
        string='Is Bike Order',
        compute='_compute_is_bike_order',
    )

    @api.depends('move_ids.product_id.is_bike')
    def _compute_is_bike_order(self):
        for picking in self:
            is_bike = False
            for move in picking.move_ids:
                if move.product_id.is_bike:
                    is_bike = True
                    break
            picking.is_bike_order = is_bike

    def action_start_picking(self):
        for picking in self:
            if picking.picking_status == 'waiting_pick':
                picking.picking_status = 'picking'

    def action_complete_picking(self):
        for picking in self:
            if picking.picking_status == 'picking':
                # Validations for Bikes
                requires_assembly = False
                for move in picking.move_ids:
                    if move.product_id.is_bike:
                        # Check serial assignment on move lines
                        total_qty_assigned = sum(
                            line.quantity for line in move.move_line_ids
                            if line.lot_id or line.lot_name
                        )
                        if total_qty_assigned < move.product_uom_qty:
                            raise UserError(
                                f"Serial number is required for all "
                                f"{move.product_id.display_name} "
                                f"before completing picking."
                            )

                        if move.product_id.is_assembly_required:
                            requires_assembly = True

                # Route picking
                if picking.is_bike_order:
                    if requires_assembly:
                        picking.picking_status = 'assembly'
                    else:
                        picking.picking_status = 'pdi'
                else:
                    picking.picking_status = 'picked'

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        # Ensure new pickings start in waiting_pick if not set
        for picking in pickings:
            if not picking.picking_status:
                picking.picking_status = 'waiting_pick'
        return pickings
