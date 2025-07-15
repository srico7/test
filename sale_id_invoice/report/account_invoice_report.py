from odoo import models, fields, api
from odoo.tools.sql import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    custom_sale_pricelist_id = fields.Many2one(
        'product.pricelist',
        string='SO pricelist',
        readonly=True,
        copy=True,
    )

    def _select(self):
        select_str = super()._select()
        additional_select = SQL(", move.custom_sale_pricelist_id as custom_sale_pricelist_id")
        return SQL("%s %s", select_str, additional_select)

    def _group_by(self):
        group_by_str = super()._group_by()
        additional_group_by = SQL(", move.custom_sale_pricelist_id")
        return SQL("%s %s", group_by_str, additional_group_by)
