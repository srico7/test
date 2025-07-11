from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError

JOB_ORDER_STATE = [
    ('draft', "Draft"),
    ('pending_approval', "Pending Approval"),
    ('approve', "Approved"),
    ('confirm', "Confirmed"),
    ('cancel', "Cancel"),
]


class RentalJob(models.Model):
    _name = 'rental.job'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Rental Job"
    _check_company_auto = True

    name = fields.Char(
        string="job Reference",
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
        required=True, change_default=True, index=True,
        tracking=1,
        domain="[('company_id', 'in', (False, company_id))]")
    create_date = fields.Datetime(string="Creation Date", index=True, readonly=True)
    state = fields.Selection(
        selection=JOB_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    rental_type = fields.Selection([
        ('cont_rnt', 'CONT. RNT'),
        ('stand_by', 'STND BY'),
        ('brk_down', 'BRK DOWN'),
        ('idling', 'IDLING'),
        ('hrnt', 'HRNT'),
        ('trnt', 'TRNT'),
    ], string='Rental Type', required=True, index=True,
        default=False)
    attachment_detail_line = fields.One2many(
        comodel_name='rental.attachment.line',
        inverse_name='rental_job_id',
        string="Attachment Details",
        copy=True, auto_join=True)
    rental_order_count = fields.Integer(string="Rental",
                                        compute='compute_sale_order_count',
                                        default=0)
    rental_detail = fields.Html(string='Rental Scope', translate=True)
    rental_scope_line = fields.One2many(
        comodel_name='rental.scope.line',
        inverse_name='rental_id',
        string="Rental Details",
        copy=True, auto_join=True)
    rental_order_line = fields.One2many(
        comodel_name='rental.order.line',
        inverse_name='rental_id',
        string="Rental Order Lines",
        copy=True, auto_join=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the clearance model """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'rental.job') or _("New")
        return super().create(vals_list)

    def action_confirm_rental_order(self):
        if not self.rental_order_line:
            raise UserError("No rentable products found in the order lines.")
        self.write({'state': 'confirm'})

        rental_orders = []
        rental_order_model = self.env['sale.order']

        # Loop through each order line and create a separate rental order
        for line in self.rental_order_line:
            if line.product_id.rent_ok:
                # Set the context as 'in_rental_app' for the order line
                order_line_context = line.env.context.copy()
                order_line_context.update({'in_rental_app': True})

                # Create the rental order with the updated context
                rental_order = rental_order_model.with_context(order_line_context).create({
                    'partner_id': self.partner_id.id,
                    'rental_status': 'draft',
                    'rental_job_id': self.id,
                    'is_rental_order': True,
                    'has_pickable_lines': True,
                    'has_rented_products': True,
                    'order_line': [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'is_rental': True,
                        'price_unit': line.price_unit,
                        'is_product_rentable': True
                    })],
                })
                rental_orders.append(rental_order)

        # Check if any rental orders were created
        if not rental_orders:
            raise UserError("No rentable products found in the order lines.")

        # Open the first created rental order in the form view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': rental_orders[0].id if rental_orders else False,
            'target': 'current',
        }

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_send_approval(self):
        if not self.rental_scope_line:
            raise UserError("Can Not Find Rental Scope...!")
        self.write({'state': 'pending_approval'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_get_rental_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('rental_job_id', '=', self.id)],
            'context': {'create': False},
        }

    def compute_sale_order_count(self):
        for record in self:
            record.rental_order_count = self.env['sale.order'].search_count(
                [('rental_job_id', '=', self.id)])

