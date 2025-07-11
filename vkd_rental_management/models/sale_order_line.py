from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    secondary_product_uom_qty = fields.Float(
        string="Quantity",
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)
    secondry_product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_secondry_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',)

    @api.depends('product_id')
    def _compute_secondry_product_uom(self):
        for line in self:
            if line.product_id:
                line.secondry_product_uom = line.product_id.secondry_product_uom
            else:
                line.secondry_product_uom = False

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.secondary_product_uom_qty')
    def _compute_qty_invoiced(self):
        """
        Ensure correct invoicing of secondary quantity for rental orders.
        """
        for line in self:
            total_qty_invoiced = 0.0
            for invoice_line in line._get_invoice_lines():
                move = invoice_line.move_id
                if move.state not in ['cancel', 'draft']:  # Ignore drafts & canceled invoices
                    if move.move_type == 'out_invoice':  # Standard invoice
                        total_qty_invoiced += invoice_line.secondary_product_uom_qty
                    elif move.move_type == 'out_refund':  # Refund (Credit Note)
                        total_qty_invoiced -= invoice_line.secondary_product_uom_qty

            line.qty_invoiced = max(0.0, total_qty_invoiced)  # Prevent negative values

    def _get_invoice_qty(self):
        """
        Override invoice quantity calculation for rental orders.
        - Ensures correct secondary quantity invoicing.
        - Prevents Odoo from generating a reverse invoice.
        """
        self.ensure_one()
        if self.order_id.is_rental_order:
            remaining_qty = self.secondary_product_uom_qty - self.qty_invoiced
            if remaining_qty <= 0:
                raise ValidationError("No remaining quantity to invoice for rental order.")
            return remaining_qty
        return super()._get_invoice_qty()