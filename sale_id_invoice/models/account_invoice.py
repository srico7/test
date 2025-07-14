
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.move"

    custom_sale_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=False,
        copy=True,
    )

    custom_sale_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='SO pricelist',
        readonly=True,
        related='custom_sale_id.pricelist_id',
        store=True,
    )
