from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tools import format_date, frozendict


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    entry_start_date = fields.Date(string='Start Date')
    entry_end_date = fields.Date(string='End date')

    def _create_invoices(self, sale_orders):
        """Pass start_date and end_date via context when creating invoices."""
        # Append the start_date and end_date to the context
        sale_orders = sale_orders.with_context(
            timesheet_start_date=self.entry_start_date,
            timesheet_end_date=self.entry_end_date
        )

        # Call the original _create_invoices method with the updated context
        invoices = super()._create_invoices(sale_orders)

        return invoices