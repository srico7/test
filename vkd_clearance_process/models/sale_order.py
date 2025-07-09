from odoo import _, api, fields, models
from odoo.osv.expression import OR, AND
import ast
from collections import defaultdict
from odoo.fields import Command

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    clearance_order_count = fields.Integer(string='Number of Clearance', compute='_compute_clearance_order_count')
    custom_order_count = fields.Integer(string='Number of Custom', compute='_compute_custom_order_count')
    delivery_order_count = fields.Integer(string='Number of Delivery', compute='_compute_delivery_order_count', default=0)
    is_clearance = fields.Boolean(string='Is Clearance', default=False,)
    is_clearance_visible = fields.Boolean(compute="_compute_is_clearance_visible", store=False)
    advanced_order_count = fields.Integer(string='Number of Advanced', compute='_compute_advanced_count')
    port_order_count = fields.Integer(string='Number of Port', compute='_compute_port_order_count')

    @api.depends('is_clearance')
    def _compute_is_clearance_visible(self):
        for record in self:
            if self.env.user.has_group('vkd_clearance_process.group_clearance_manager'):
                record.is_clearance_visible = True
            else:
                record.is_clearance_visible = False



    # custom details

    arrived_date = fields.Datetime(string="Arrived Date", index=True)
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
        ('bulk_at_port', 'Bulk at port'),
        ('bulk_at_anchore', 'Bulk at Anchore'),
    ], string='Sea Shipment', default=False)
    air_shipment_type = fields.Selection([
        ('direct', 'Direct'),
        ('hand_carrier', 'Hand Carrier'),
        ('courier', 'Courier')
    ], string='Air Shipment', default=False)
    register_form_number = fields.Char(string='R-Form Number', requiured=True)
    agent_id = fields.Many2one(comodel_name='res.partner', string='Agent Name')
    agent_email = fields.Char(string='Email', related='agent_id.email')
    agent_contact = fields.Char(string='Contact', related='agent_id.phone')

    # documents

    bl_number = fields.Char(string='BL Number', copy=False)
    bl_number_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bl_number_attachment_rel',  # Unique relation table
        'bl_number_id',  # Column for this model
        'attachment_id',  # Column for ir.attachment
        string='BL Number Attachments',
        help='Attachments related to BL Number'
    )

    packing_list = fields.Float(string='Packing List')
    packing_list_attachment_ids = fields.Many2many(
        'ir.attachment',
        'packing_list_attachment_rel',  # Unique relation table
        'packing_list_id',  # Column for this model
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
        'commercial_invoice_attachment_rel',  # Unique relation table
        'commercial_invoice_id',  # Column for this model
        'attachment_id',  # Column for ir.attachment
        string='Commercial Invoice Attachments',
        help='Attachments related to Invoice Number'
    )
    cargo_detail = fields.Html(string='Cargo Details', translate=True)
    is_processed = fields.Boolean(string="Is Processed", default=False)
    is_get_advanced_payment = fields.Boolean(string="Is Processed", compute='_get_advanced_payment')

    def _get_advanced_payment(self):
        for rec in self:
            advanced_payment = self.env['account.payment'].search_count(
                [('clearance_sale_order_id', '=', self.id)])
            if advanced_payment:
                rec.is_get_advanced_payment = advanced_payment > 0
            else:
                rec.is_get_advanced_payment = 0

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        for rec in record:
            if rec.is_clearance == True:
                rec.write({
                    'name': self.env['ir.sequence'].next_by_code('clearance.order.sequence') or _("New")
                })
        return record

    def _compute_clearance_order_count(self):
        for record in self:
            record.clearance_order_count = self.env['clearance.order'].search_count(
                [('clearance_sale_order_id', '=', record.id)])

    def _compute_advanced_count(self):
        for record in self:
            record.advanced_order_count = self.env['account.payment'].search_count(
                [('clearance_sale_order_id', '=', record.id)])

    def _compute_custom_order_count(self):
        for record in self:
            record.custom_order_count = self.env['custom.order'].search_count(
                [('custom_sale_order_id', '=', record.id)])

    def _compute_port_order_count(self):
        for record in self:
            record.port_order_count = self.env['port.order'].search_count(
                [('port_sale_order_id', '=', record.id)])

    def _compute_delivery_order_count(self):
        for record in self:
            record.delivery_order_count = self.env['delivery.order'].search_count(
                [('delivery_sale_order_id', '=', self.id)])

    def action_get_delevrey_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Deliver Order',
            'view_mode': 'tree,form',
            'res_model': 'delivery.order',
            'domain': [('delivery_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_get_clearance_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Clearance Order',
            'view_mode': 'tree,form',
            'res_model': 'clearance.order',
            'domain': [('clearance_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_get_custom_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Order',
            'view_mode': 'tree,form',
            'res_model': 'custom.order',
            'domain': [('custom_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_get_port_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Port Order',
            'view_mode': 'tree,form',
            'res_model': 'port.order',
            'domain': [('port_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_get_advanced_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Advanced Payment',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('clearance_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_process_creation(self):
        """Create, update, or delete Clearance Job records for each line in clearance_order_ids."""
        clearance_order_obj = self.env['clearance.order']  # Object to match clearance orders
        custom_order_obj = self.env['custom.order']  # Object to match custom orders
        delivery_order_obj = self.env['delivery.order']  # Object to match delivery orders
        port_order_obj = self.env['port.order']  # Object to match port orders

        for order in self:
            # Track existing clearance and custom orders for cleanup
            clearance_records_to_keep = []
            custom_records_to_keep = []
            delivery_records_to_keep = []
            port_records_to_keep = []

            # Process clearance orders
            for line in order.order_line:  # Iterate through order lines
                if line.container_no:  # Ensure the line belongs to the current sale order
                    # Search for an existing clearance order line based on the sale order and container number
                    clearance_record = clearance_order_obj.search([
                        ('clearance_sale_order_id', '=', order.id),
                        ('container_no', '=', line.container_no)
                    ], limit=1)

                    # Prepare values
                    clearance_job_vals = {
                        'name': clearance_record.name if clearance_record else self.env['ir.sequence'].next_by_code(
                            'clearance.order') or _('New'),
                        'container_no': line.container_no,
                        'bl_number': order.bl_number,
                        'number_of_package': line.number_of_package,
                        'volume': line.volume,
                        'weight': line.weight,
                        'arrival_date': line.arrival_date,
                        'cleared_date': line.cleared_date,
                        'container_returned_date': line.container_returned_date,
                        'loaded_to': line.loaded_to,
                        'container_type': line.container_type,
                        'partner_id': order.partner_id.id,  # Include partner ID (customer)
                        'clearance_sale_order_id': order.id,  # Link back to the sale order
                        'origin': order.name,  # Link back to the sale order
                    }

                    # Update the record if it exists, or create a new one
                    if clearance_record:
                        clearance_record.write(clearance_job_vals)
                    else:
                        clearance_record = clearance_order_obj.create(clearance_job_vals)

                    # Keep track of clearance records
                    clearance_records_to_keep.append(clearance_record.id)

            # Remove clearance records that are no longer needed
            clearance_order_obj.search([
                ('clearance_sale_order_id', '=', order.id),
                ('id', 'not in', clearance_records_to_keep)
            ]).unlink()

            # Process custom orders
            custom_record = custom_order_obj.search([
                ('custom_sale_order_id', '=', order.id),
                ('bl_number', '=', order.bl_number)
            ], limit=1)

            # Prepare values for the custom order
            custom_order_vals = {
                'name': self.env['ir.sequence'].next_by_code('custom.order') or _('New'),
                'arrived_date': order.arrived_date,
                'clearance_type': order.clearance_type,
                'shipment_type': order.shipment_type,
                'sea_shipment_type': order.sea_shipment_type,
                'air_shipment_type': order.air_shipment_type,
                'register_form_number': order.register_form_number,
                'agent_id': order.agent_id.id,
                'agent_email': order.agent_email,
                'agent_contact': order.agent_contact,
                'bl_number': order.bl_number,  # Include BL number
                'packing_list': order.packing_list,  # Link back to the sale order
                'commercial_invoice_number': order.commercial_invoice_number,
                'partner_id': order.partner_id.id,  # Include partner ID (customer)
                'custom_sale_order_id': order.id,
                'origin': order.name,  # Link back to the sale order
                'packing_list_attachment_ids': [(6, 0, order.packing_list_attachment_ids.ids)],# Pass packing list attachments
                'commercial_invoice_attachment_ids': [(6, 0, order.commercial_invoice_attachment_ids.ids)],# Pass commercial invoice attachments
                'bl_number_attachment_ids': [(6, 0, order.bl_number_attachment_ids.ids)],# Pass BL attachments

            }

            # Update the record if it exists, or create a new one
            if custom_record:
                custom_record.write(custom_order_vals)
                custom_records_to_keep.append(custom_record.id)
            else:
                custom_record = custom_order_obj.create(custom_order_vals)
                custom_records_to_keep.append(custom_record.id)

            # Remove custom records that are no longer needed
            custom_order_obj.search([
                ('custom_sale_order_id', '=', order.id),
                ('id', 'not in', custom_records_to_keep)
            ]).unlink()

            # Process custom orders
            delivery_order_record = delivery_order_obj.search([
                ('delivery_sale_order_id', '=', order.id),
                ('bl_number', '=', order.bl_number)
            ], limit=1)

            # Prepare values for the custom order
            delivery_order_vals = {
                'name': self.env['ir.sequence'].next_by_code('delivery.order') or _('New'),
                'arrived_date': order.arrived_date,
                'agent_id': order.agent_id.id,
                'agent_email': order.agent_email,
                'agent_contact': order.agent_contact,
                'bl_number': order.bl_number,  # Include BL number
                'partner_id': order.partner_id.id,  # Include partner ID (customer)
                'delivery_sale_order_id': order.id,
                'origin': order.name,  # Link back to the sale order
            }

            # Update the record if it exists, or create a new one
            if delivery_order_record:
                delivery_order_record.write(delivery_order_vals)
                delivery_records_to_keep.append(delivery_order_record.id)
            else:
                delivery_order_record = delivery_order_obj.create(delivery_order_vals)
                delivery_records_to_keep.append(delivery_order_record.id)

            port_order_record = port_order_obj.search([
                ('port_sale_order_id', '=', order.id),
                ('bl_number', '=', order.bl_number)
            ], limit=1)

            # Prepare values for the custom order
            port_order_vals = {
                'name': self.env['ir.sequence'].next_by_code('port.order') or _('New'),
                'arrived_date': order.arrived_date,
                'agent_id': order.agent_id.id,
                'agent_email': order.agent_email,
                'agent_contact': order.agent_contact,
                'bl_number': order.bl_number,  # Include BL number
                'partner_id': order.partner_id.id,  # Include partner ID (customer)
                'port_sale_order_id': order.id,
                'origin': order.name,  # Link back to the sale order
            }

            if port_order_record:
                port_order_record.write(port_order_vals)
                port_records_to_keep.append(port_order_record.id)
            else:
                port_order_record = port_order_obj.create(port_order_vals)
                port_records_to_keep.append(port_order_record.id)
            order.is_processed = True

    def action_open_advanced_payment_wizard(self):
        """Open the wizard for advanced payment"""
        return {
            'name': 'Advanced Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'advanced.payment',
            'view_mode': 'form',
            'target': 'new',  # Opens as a popup
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    @api.onchange('arrived_date', 'order_line', 'register_form_number', 'commercial_invoice_attachment_ids',
                  'packing_list_attachment_ids', 'bl_number_attachment_ids')
    def _onchange_update_values(self):
        clearance_order_obj = self.env['clearance.order']  # Object to match clearance orders
        custom_order_obj = self.env['custom.order']  # Object to match custom orders
        delivery_order_obj = self.env['delivery.order']  # Object to match delivery orders
        port_order_obj = self.env['port.order']  # Object to match port orders

        for line in self.order_line:
            clearance_record = clearance_order_obj.search([('container_no', '=', line.container_no)])
            custom_record = custom_order_obj.search([('bl_number', '=', self.bl_number)], limit=1)

            for rec in clearance_record:
                if clearance_record:
                    rec.update({
                        'container_no': line.container_no,
                        'bl_number': self.bl_number,
                        'number_of_package': line.number_of_package,
                        'volume': line.volume,
                        'weight': line.weight,
                        'arrival_date': self.arrived_date,
                        'cleared_date': line.cleared_date,
                        'container_returned_date': line.container_returned_date,
                        'loaded_to': line.loaded_to,
                        'container_type': line.container_type,
                    })
                else:
                    rec.update({
                        'container_no': line.container_no,
                        'bl_number': self.bl_number,
                        'number_of_package': line.number_of_package,
                        'volume': line.volume,
                        'weight': line.weight,
                        'arrival_date': self.arrived_date,
                        'cleared_date': line.cleared_date,
                        'container_returned_date': line.container_returned_date,
                        'loaded_to': line.loaded_to,
                        'container_type': line.container_type,
                    })

            if custom_record:
                for custom_rec in custom_record:
                    custom_rec.update({
                        'arrived_date': self.arrived_date,
                    })
