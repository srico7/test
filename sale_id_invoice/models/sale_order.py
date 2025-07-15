from odoo import models, api


# change Sale to SaleOrder
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res.update({
            'custom_sale_id': self.id,
        })
        return res
