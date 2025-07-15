from odoo import api, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super()._create_invoice(order, so_line, amount)
        res.write({'custom_sale_id': order.id})
        return res


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        if move.custom_sale_id:
            res.update({'custom_sale_id': move.custom_sale_id.id})
        return res

