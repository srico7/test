from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    delivery_sale_order_id = fields.Many2one('sale.order')
    custom_sale_order_id = fields.Many2one('sale.order')
    clearance_sale_order_id = fields.Many2one('sale.order')
    port_sale_order_id = fields.Many2one('sale.order')
    is_first_invoice = fields.Boolean(string='Is First Clearance Invoice', default=False,
                                      help='Is First Clearance Invoice')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    custom_sale_order_id = fields.Many2one('sale.order')

    def _create_payment_vals_from_wizard(self, batch_result):
        # Call the parent method to get default payment values
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        # Get the related move (vendor bill)
        moves = batch_result['lines'].mapped('move_id')

        # Ensure there is only one move (vendor bill) in the batch
        if len(moves) == 1 and moves.move_type == 'in_invoice' and moves.custom_sale_order_id:
            # Update the payment values with the custom sale order ID
            payment_vals['custom_sale_order_id'] = moves.custom_sale_order_id.id

        return payment_vals

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        for move in self:
            if move.partner_type == 'supplier' and move.line_ids[0].move_id.custom_sale_order_id.id:
                # Use the ID of the custom_sale_order_id record
                custom_order = self.env['custom.order'].search(
                    [('custom_sale_order_id', '=', move.line_ids[0].move_id.custom_sale_order_id.id)], limit=1
                )
                if custom_order:
                    custom_order.custom_state = 'paid'
        return res
