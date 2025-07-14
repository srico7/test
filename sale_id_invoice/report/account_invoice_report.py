
from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    custom_sale_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='SO pricelist',
        readonly=True,
        copy=True,
    )

    @api.model
    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += ", move.custom_sale_pricelist_id as custom_sale_pricelist_id"
        return select_str

    @api.model
    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ", move.custom_sale_pricelist_id"
        return group_by_str
