from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import ast
from collections import defaultdict
from odoo.fields import Command

CLEARANCE_ORDER_STATE = [
    ('Pending_arrival', "Pending Arrival"),
    ('arrived', "Arrived"),
    ('discharged', "Discharged"),
    ('pending_box_return', "Pending Box Return"),
    ('complete', 'Complete')
]

CUSTOM_ORDER_STATE = [
    ('new_request', "New Request"),
    ('assign_to_broker', "Assign To Broker"),
    ('pending_custom', "Pending Custom"),
    ('clarification', "Clarification"),
    ('pending_payment', "Pending Payment"),
    ('assign_to_broker_again', "Assign to Broker"),
    ('paid', "Paid"),
]

DELIVERY_ORDER_STATE = [
    ('pending_arrival', "Pending Arrival"),
    ('arrived', "Arrived"),
    ('do_approved', "DO Approved"),
]

class ClearanceOrder(models.Model):
    _name = 'clearance.order'
    _description = 'Clearance Order'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc'
    _check_company_auto = True


    name = fields.Char(
        string="Name",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    clearance_sale_order_id = fields.Many2one('sale.order')
    custom_order_id = fields.Many2one('custom.order')
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
    create_date = fields.Datetime(string="Creation Date", index=True, readonly=True)
    container_no = fields.Char(string='Container No.')
    number_of_package = fields.Float(string='Number of Packages')
    volume = fields.Float(string='Volume (CBM)')
    weight = fields.Float(string='Weight (Kg)')
    arrival_date = fields.Datetime(string='Arrival Date', related='clearance_sale_order_id.arrived_date')
    discharge_date = fields.Date(string='Discharge Date')
    cleared_date = fields.Date(string='Cleared Date')
    container_returned_date = fields.Date(string='Returned Date')
    loaded_to = fields.Char(string='Loaded To')
    container_type = fields.Selection([('box', 'Box'),
                                       ('loose', 'Loose')], string='Clearance Type', required=True)
    bl_number = fields.Char(string='BL Number', copy=False, required=True)
    clearance_state = fields.Selection(
        selection=CLEARANCE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='Pending_arrival')
    custom_state = fields.Selection(
        selection=CUSTOM_ORDER_STATE, compute='_compute_custom_state',  readonly=True, string="Custom Status",)
    delivery_state = fields.Selection(
        selection=DELIVERY_ORDER_STATE,
        string="Delivery Status",
        compute='_compute_delivery_state',  readonly=True,)
    origin = fields.Char('Source Document', copy=False,
                         help="Reference of the document that generated this sales order "
                              "request (e.g. a sales order)")
    clearance_order_count = fields.Integer(string="Sale",
                                           compute='compute_sale_order_count',
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
    clearance_order_vendor_bill_count = fields.Integer(string="Vendor Bill",
                                                       compute='compute_clearance_order_vendor_bill_count',
                                                       default=0)
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')

    @api.depends('custom_state')
    def _compute_custom_state(self):
        for record in self:
            # Ensure the correct field is used for filtering
            if record.clearance_sale_order_id:
                custom_orders = self.env['custom.order'].search([
                    ('custom_sale_order_id', '=', record.clearance_sale_order_id.id)
                ])
                # Handle multiple custom orders and assign the first matching state
                record.custom_state = custom_orders[:1].custom_state or False
            else:
                record.custom_state = False

    @api.depends('delivery_state')
    def _compute_delivery_state(self):
        for record in self:
            # Ensure the correct field is used for filtering
            if record.clearance_sale_order_id:
                delivery_orders = self.env['delivery.order'].search([
                    ('delivery_sale_order_id', '=', record.clearance_sale_order_id.id)
                ])
                # Handle multiple custom orders and assign the first matching state
                record.delivery_state = delivery_orders[:1].delivery_state or False
            else:
                record.delivery_state = False

    def action_discharged(self):
        self.write({'clearance_state': 'discharged'})

    def action_release(self):
        self.write({'clearance_state': 'pending_box_return'})

    def action_return(self):
        self.write({'clearance_state': 'complete'})

    def action_complete(self):
        self.write({'clearance_state': 'complete'})

    def action_pending_payment(self):
        self.write({'clearance_state': 'paid'})

    def compute_sale_order_count(self):
        for record in self:
            record.clearance_order_count = self.env['sale.order'].search_count(
                [('order_line.order_id', '=', self.clearance_sale_order_id.id)])

    def action_get_clearance_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('order_line.order_id', '=', self.clearance_sale_order_id.id)],
            'context': {'create': False},
        }

    def action_create_vendor_bill(self):
        if self.vendor_id:
            for each in self:
                inv_obj = self.env['account.move']
            supplier = self.vendor_id
            inv_data = {
                'ref': supplier.name,
                'move_type': 'in_invoice',
                'partner_id': supplier.id,
                'currency_id': self.account_type.company_id.currency_id.id,
                'journal_id': self.journal_type.id,
                'invoice_origin': self.name,
                'clearance_sale_order_id': self.clearance_sale_order_id.id,
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
            raise UserError(_("Please select vendor before vendor bill.....!"))
        return result

    def compute_clearance_order_vendor_bill_count(self):
        for record in self:
            record.clearance_order_vendor_bill_count = self.env['account.move'].search_count(
                [('clearance_sale_order_id', '=', self.clearance_sale_order_id.id)])

    def action_get_vendor_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('clearance_sale_order_id', '=', self.clearance_sale_order_id.id)],
            'context': {'create': False},
        }

    @api.onchange('discharge_date')
    def change_state(self):
        for rec in self:
            if rec.discharge_date:
                rec.write({'clearance_state': 'discharged'})
            else:
                rec.write({'clearance_state': 'arrived'})

    @api.onchange('arrival_date', 'clearance_sale_order_id.arrival_date')
    def _onchange_arrival_date(self):
        for rec in self:
            if rec.arrival_date:
                rec.write({'clearance_state': 'arrived'})
            else:
                rec.write({'clearance_state': 'Pending_arrival'})

    def write(self, vals):
        if 'discharge_date' in vals:
            vals['clearance_state'] = 'discharged' if vals['discharge_date'] else 'arrived'
        if 'arrival_date' in vals:
            vals['clearance_state'] = 'arrived' if vals['arrival_date'] else 'Pending_arrival'
        for record in self:
            if record.clearance_sale_order_id:
                # Update sale order lines if needed
                sale_order = record.clearance_sale_order_id
                for line in sale_order.order_line:
                    if line.container_no == record.container_no:
                        # Update corresponding sale order line fields
                        line.write({
                            'number_of_package': record.number_of_package,
                            'volume': record.volume,
                            'weight': record.weight,
                            'arrival_date': record.arrival_date,
                            'discharge_date': record.discharge_date,
                            'cleared_date': record.cleared_date,
                            'container_returned_date': record.container_returned_date,
                        })
        return super(ClearanceOrder, self).write(vals)
