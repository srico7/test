from odoo import fields, models, _


class CommercialInvoiceLine(models.Model):
    _name = 'commercial.invoice.line'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Sale Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    commercial_invoice_number = fields.Char(string='CL Number')
    number_cls = fields.Integer(string='Number of CLS')
