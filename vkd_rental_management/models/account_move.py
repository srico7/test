from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    secondary_product_uom_qty = fields.Float(
        string="Quantity",
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)
    secondry_product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        store=True, readonly=False, precompute=True, ondelete='restrict')
    is_rental_invoice_line = fields.Boolean(string='Is Rental Invoice', default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_rental_invoice = fields.Boolean('Is Rental Invoice', default=False)