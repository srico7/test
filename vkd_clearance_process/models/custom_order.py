from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

CUSTOM_ORDER_STATE = [
    ('new_request', "New Request"),
    ('assign_to_broker', "Assign To Broker"),
    ('pending_custom', "Pending Custom"),
    ('clarification', "Clarification"),
    ('assign_to_broker_again', "Assign to Broker"),
    ('pending_payment', "Pending Payment"),
    ('paid', "Paid"),
]

class CustomOrder(models.Model):
    _name = 'custom.order'
    _description = 'Custom Order'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc'
    _check_company_auto = True

    custom_sale_order_id = fields.Many2one('sale.order')
    name = fields.Char(
        string="Name",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        change_default=True, index=True,
        tracking=1,
        domain="[('company_id', 'in', (False, company_id))]")
    user_id = fields.Many2one('res.users', string='Responsible User', index=True, default=lambda self: self.env.user)
    custom_state = fields.Selection(
        selection=CUSTOM_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='new_request')

    arrived_date = fields.Datetime(string="Arrived Date", index=True, related='custom_sale_order_id.arrived_date')
    clearance_type = fields.Selection([
        ('cbs', 'CBS'),
        ('lsc', 'LSC'),
        ('lst', 'LST'),
        ('trs', 'TRS')
    ],
        string="Clearance Type", required=True, index=True,
        default='cbs')
    shipment_type = fields.Selection([
        ('sea', 'Sea'),
        ('air', 'Air'),
    ], string='Shipment Type', index=True,
        default=False)
    sea_shipment_type = fields.Selection([
        ('lcl', 'LCL'),
        ('fcl', 'FCL'),
        ('bulk_at_port', 'Bulk at port')
    ], string='Sea Shipment', default=False)
    air_shipment_type = fields.Selection([
        ('direct', 'Direct'),
        ('hand_carrier', 'Hand Carrier'),
        ('courier', 'Courier')
    ], string='Air Shipment', default=False)
    register_form_number = fields.Char(string='R-Form Number',)
    agent_id = fields.Many2one(comodel_name='res.partner', string='Agent Name',)
    agent_email = fields.Char(string='Email', related='agent_id.email')
    agent_contact = fields.Char(string='Contact', related='agent_id.phone')

    broker_id = fields.Many2one(comodel_name='res.partner', string='Broker Name', )
    broker_email = fields.Char(string='Broker Email', related='broker_id.email')
    broker_contact = fields.Char(string='Broker Contact', related='broker_id.phone')
    bl_number = fields.Char(string='BL Number', copy=False, required=True)

    # documents

    bl_number = fields.Char(string='BL Number', copy=False)
    bl_number_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rel_bl_number_attachment_custom_order',  # Unique relation table
        'custom_order_id',  # Column for this model
        'attachment_id',  # Column for ir.attachment
        string='BL Number Attachments',
        help='Attachments related to BL Number'
    )

    packing_list = fields.Float(string='Packing List')
    packing_list_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rel_packing_list_attachment_custom_order',  # Unique relation table
        'custom_order_id',  # Column for this model
        'attachment_id',  # Column for ir.attachment
        string='Packing List Attachments',
        help='Attachments related to Packing List'
    )

    commercial_invoice_line = fields.One2many(
        comodel_name='commercial.invoice.line',
        inverse_name='sale_order_id',
        string='Commercial Invoices')
    commercial_invoice_number = fields.Char(string='Invoice Number')
    commercial_invoice_attachment_ids = fields.Many2many(
        'ir.attachment',
        'rel_commercial_invoice_attachment_custom_order',  # Unique relation table
        'custom_order_id',  # Column for this model
        'attachment_id',  # Column for ir.attachment
        string='Commercial Invoice Attachments',
        help='Attachments related to Invoice Number'
    )

    origin = fields.Char('Source Document', copy=False,
                         help="Reference of the document that generated this custom order "
                              "request (e.g. a sales order)")
    custom_order_count = fields.Integer(string="Sale",
                                        compute='compute_custom_sale_order_count',
                                        default=0)
    purchase_order_count = fields.Integer(string="purchase",
                                          default=0)

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
    custom_order_vendor_bill_count = fields.Integer(string="Vendor Bill",
                                                    compute='compute_custom_order_vendor_bill_count',
                                                    default=0)
    arrival_port = fields.Selection([
        ('kulhudhufushi_port', 'Kulhudhufushi Port'),
        ('male_port', 'Male Port'),
        ('hithadhoo_port', 'Hithadoo Port')
    ], string='Arrival Port')

    def action_assign_to_broker(self):
        self.write({'custom_state': 'assign_to_broker'})

    def action_clarification(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default. Updates state after email is sent. """
        self.ensure_one()

        # Get the email template
        mail_template = self.env.ref('vkd_clearance_process.email_template_clarification')

        # Prepare the context for the wizard
        ctx = {
            'default_model': 'custom.order',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'force_email': True,
            'custom_state_to_update': 'clarification',  # Pass the state to update in context
        }

        # Return the wizard action
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_assign_to_broker_again(self):
        self.write({'custom_state': 'assign_to_broker_again'})

    def action_pending_payment(self):
        self.write({'custom_state': 'pending_payment'})

    def action_paid(self):
        self.write({'custom_state': 'paid'})

    def compute_custom_sale_order_count(self):
        for record in self:
            record.custom_order_count = self.env['sale.order'].search_count(
                [('order_line.order_id', '=', self.custom_sale_order_id.id)])

    # def compute_purchase_order_count(self):
    #     for record in self:
    #         record.purchase_order_count = self.env['purchase.order'].search_count(
    #             [('origin', '=', self.origin)])

    def action_get_custom_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('order_line.order_id', '=', self.custom_sale_order_id.id)],
            'context': {'create': False},
        }

    def action_get_custom_purchase_order (self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('origin', '=', self.origin)],
            'context': {'create': False},
        }

    def write(self, vals):
        res = super(CustomOrder, self).write(vals)
        for record in self:
            if record.custom_sale_order_id:
                # Update BL details on sale order if needed
                sale_order = record.custom_sale_order_id
                sale_order.write({
                    'bl_number': record.bl_number,
                    # 'arrived_date': record.arrived_date,
                    'shipment_type': record.shipment_type,
                    'register_form_number': record.register_form_number,
                })
        return res

    # def create_purchase_order(self, partner=False, origin=False, lines=False):
    #     """ Create and return a new purchase order."""
    #     if self.agent_id:
    #         vals = {
    #             'partner_id': self.agent_id.id,
    #             'origin': self.origin,
    #         }
    #         # # Create order lines if defined.
    #         # if lines:
    #         #     vals['order_line'] = []
    #         #     for line in lines:
    #         #         product = line['product']
    #         #         order_line_vals = (0, 0, {
    #         #             'date_planned': fields.Date.today(),
    #         #             'name': product.display_name,
    #         #             'price_unit': line['price'],
    #         #             'product_id': product.id,
    #         #             'product_qty': line.get('quantity', 1),
    #         #             'product_uom': line.get('uom', product.uom_id.id),
    #         #         })
    #         #         vals['order_line'].append(order_line_vals)
    #
    #         new_purchase = self.env['purchase.order'].create(vals)
    #     else:
    #         raise UserError(_("Please select agent before create purchase.....!"))
    #     return new_purchase

    def action_create_vendor_bill(self):
        if self.agent_id:
            for each in self:
                inv_obj = self.env['account.move']
            supplier = self.agent_id
            inv_data = {
                'ref': supplier.name,
                'move_type': 'in_invoice',
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'invoice_origin': self.name,
                'custom_sale_order_id': self.custom_sale_order_id.id,
                'company_id': self.account_type.company_id.id,
                'invoice_date_due': self.create_date,
                'is_first_invoice': True,
            }
            inv_id = inv_obj.create(inv_data)

            # Update the clearance order state
            self.first_payment_inv = inv_id.id
            self.custom_state = 'pending_payment'  # Update the state to 'pending_payment'

            # Return the result to open the created vendor bill
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
            raise UserError(_("Please select vendor before creating a vendor bill!"))
        return result

    def compute_custom_order_vendor_bill_count(self):
        for record in self:
            record.custom_order_vendor_bill_count = self.env['account.move'].search_count(
                [('custom_sale_order_id', '=', self.custom_sale_order_id.id)])

    def action_get_vendor_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('custom_sale_order_id', '=', self.custom_sale_order_id.id)],
            'context': {'create': False},
        }
