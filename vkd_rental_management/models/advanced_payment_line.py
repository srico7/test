from odoo import fields, models, _, api


class AdvancedPaymentLine(models.Model):
    _name = 'advanced.payment.line'

    name = fields.Char(
        string="Name",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('/'))
    is_internal_transfer = fields.Boolean(string='Internal Transfer', default=False)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)
    note = fields.Text('Notes')
    partner_id = fields.Many2one('res.partner', string='Customer',)
    deposit_amount = fields.Monetary('Amount', tracking=2)
    payment_journal_id = fields.Many2one('account.journal', string='Journal',
                                         domain="[('type', 'in', ['bank', 'cash'])]")
    date = fields.Date('Date', copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state = fields.Selection(string='State', selection=[('draft', 'Draft'),
                                                        ('posted', 'Posted')], default='draft', tracking=4)
    payment_id = fields.Many2one('account.payment', string='Payment', copy=False)
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
                                             domain="[('id', 'in', available_payment_method_line_ids)]",
                                             help="Manual: Pay or Get paid by any method outside of Odoo.\n"
                                                  "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
                                                  "Check: Pay bills by check and print it from Odoo.\n"
                                                  "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
                                                  "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
                                                  "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
                                                         compute='_compute_payment_method_line_fields')
    sale_order_id = fields.Many2one('sale.order')

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the clearance model """
        for vals in vals_list:
            if vals.get('name', _('/')) == _('/'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'advanced.payment.line') or _("/")
        return super().create(vals_list)

    @api.depends('payment_journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.payment_journal_id._get_available_payment_method_lines(
                'inbound')

    def action_confirm_advanced_payment(self):
        vals = {
            'payment_type': 'inbound',
            'is_internal_transfer': self.is_internal_transfer,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id and self.company_id.id or False,
            'amount': self.deposit_amount or 0.0,
            'currency_id': self.currency_id and self.currency_id.id or False,
            'journal_id': self.payment_journal_id and self.payment_journal_id.id or False,
            'payment_method_line_id': self.payment_method_line_id.id,
            'ref': self.note
        }
        payment_id = self.env['account.payment'].sudo().create(vals)
        payment_id.action_post()
        self.write({'state': 'posted'})
        self.payment_id = payment_id and payment_id.id or False

    def action_cancel(self):
        self.write({'state': 'cancel'})
