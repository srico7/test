from odoo import _, api, fields, models
from odoo.osv.expression import OR, AND
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from odoo.fields import Command

DELIVERY_ORDER_STATE = [
    ('pending_arrival', "Pending Arrival"),
    ('arrived', "Arrived"),
    ('do_approved', "DO Approved"),
]

class DeliveryOrder(models.Model):
    _name = 'delivery.order'
    _description = 'Delivery Order Process'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc'
    _check_company_auto = True

    delivery_sale_order_id = fields.Many2one('sale.order')
    name = fields.Char(
        string="Name",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        change_default=True, index=True,
        tracking=1,
        domain="[('company_id', 'in', (False, company_id))]")
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    arrived_date = fields.Datetime(string="Arrived Date", index=True, related='delivery_sale_order_id.arrived_date')
    agent_id = fields.Many2one(comodel_name='res.partner', string='Agent Name', )
    agent_email = fields.Char(string='Email', related='agent_id.email')
    agent_contact = fields.Char(string='Contact', related='agent_id.phone')
    bl_number = fields.Char(string='BL Number', copy=False)
    origin = fields.Char('Source Document', copy=False,
                         help="Reference of the document that generated this custom order "
                              "request (e.g. a sales order)")
    delivery_state = fields.Selection(
        selection=DELIVERY_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='pending_arrival')
    first_payment_inv = fields.Many2one('account.move', copy=False)
    journal_type = fields.Many2one('account.journal', 'Journal',
                                   default=lambda self: self.env[
                                       'account.journal'].search(
                                       [('id', '=', 2)]))
    account_type = fields.Many2one('account.account', 'Account',
                                   default=lambda self: self.env[
                                       'account.account'].search(
                                       [('id', '=', 17)]))
    first_payment = fields.Float(string='First Payment',
                                 help="Transaction/Office/Contract charge "
                                      "amount, must paid by customer side "
                                      "other "
                                      "than recurrent payments",
                                 track_visibility='onchange',
                                 required=True, default=False)
    delivery_order_vendor_bill_count = fields.Integer(string="Vendor Bill",
                                                      compute='compute_delivery_order_vendor_bill_count',
                                                      default=0)

    # def create(self, vals_list):
    #     """ Create a sequence for the clearance model """
    #     for vals in vals_list:
    #         if vals.get('name', _('New')) == _('New'):
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 'delivery.order') or _("New")
    #     return super().create(vals_list)

    def action_pending_arrival(self):
        self.write({'delivery_state': 'arrived'})

    def action_do_approve(self):
        self.write({'delivery_state': 'do_approved'})

    def action_create_vendor_bill(self):
        for each in self:
            inv_obj = self.env['account.move']
            supplier = self.agent_id
            if supplier:
                inv_data = {
                    'ref': supplier.name,
                    'move_type': 'in_invoice',
                    'partner_id': supplier.id,
                    'currency_id': self.account_type.company_id.currency_id.id,
                    'journal_id': self.journal_type.id,
                    'invoice_origin': self.name,
                    'delivery_sale_order_id': self.delivery_sale_order_id.id,
                    'company_id': self.account_type.company_id.id,
                    'invoice_date_due': self.create_date,
                    'is_first_invoice': True,
                }
                inv_id = inv_obj.create(inv_data)
                self.first_payment_inv = inv_id.id
                action = self.env.ref('account.action_move_in_invoice_type')
                result = {
                    'name': action.name,
                    'type': 'ir.actions.act_window',
                    'views': [[False, 'form']],
                    'target': 'current',
                    'res_id': inv_id.id,
                    'res_model': 'account.move',
                }
            else:
                raise UserError(_("Please select vendor before create vendor bill.....!"))

            return result

    def compute_delivery_order_vendor_bill_count(self):
        for record in self:
            record.delivery_order_vendor_bill_count = self.env['account.move'].search_count(
                [('delivery_sale_order_id', '=', self.delivery_sale_order_id.id)])

    def action_get_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('delivery_sale_order_id', '=', self.delivery_sale_order_id.id)],
            'context': {'create': False},
        }

    @api.onchange('arrived_date')
    def _onchange_arrived_date(self):
        for rec in self:
            if rec.arrived_date:
                self.write({'delivery_state': 'arrived'})
            else:
                self.write({'delivery_state': 'pending_arrival'})

    def write(self, vals):
        if 'arrived_date' in vals:
            vals['delivery_state'] = 'arrived' if vals['arrived_date'] else 'Pending_arrival'
        return super(DeliveryOrder, self).write(vals)
