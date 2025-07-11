from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one('sale.order', string='Sale Order Id')
    is_so = fields.Boolean(default=False, copy=False)

    @api.onchange('sale_order_id')
    def _onchange_is_so(self):
        if self.sale_order_id:
            self.is_so = True
        else:
            self.is_so = False
