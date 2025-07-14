
from odoo import models, api


class Sale(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super(Sale, self)._prepare_invoice()
        vals = {
            'custom_sale_id': self.id,
        }
        res.update(vals)
        return res
