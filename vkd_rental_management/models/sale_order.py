from odoo import _, api, fields, models
from odoo.osv.expression import OR, AND
import ast
from collections import defaultdict
from odoo.fields import Command

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    rental_job_id = fields.Many2one(
        comodel_name='rental.job',
        string="Rental Reference",
        ondelete='cascade', index=True, copy=False)
    purchase_order_ids = fields.One2many('purchase.order', 'sale_order_id', string="Purchase Orders")
    rental_terms = fields.Selection([('per_hour', 'Per Hour'),
                                     ('per_day', 'Per Day'),
                                     ('per_month', 'Per Month'),
                                     ('per_year', 'Per Year')], string='Rental Terms', required=True, default='per_hour')
    advanced_payment_line_ids = fields.One2many(
        comodel_name='advanced.payment.line',
        inverse_name='sale_order_id',
        string="Advanced Payment",
        copy=True, auto_join=True)
    rental_status = fields.Selection(
        selection_add=[('breakdown', 'Break Down')], ondelete={'breakdown': 'cascade'})
    has_breakdown_lines = fields.Boolean(default=False)

    previous_time_period = fields.Char(string="Previous Time Period")
    new_extended_time_period = fields.Char(string="New Extended Time Period")
    attachment_detail_sale_line = fields.One2many(
        comodel_name='rental.attachment.line',
        inverse_name='sale_order_id',
        string="Attachment Details",
        copy=True, auto_join=True)
    rental_project_count = fields.Integer(string='Number of Projects', compute='_compute_project_count')
    rental_tasks_count = fields.Integer(string='Tasks', compute='_compute_task_count')
    project_created = fields.Boolean(default=False)
    rental_period_history_ids = fields.One2many(
        'rental.extend.history', 'rental_order_id', string="Rental Period History"
    )
    rental_scope_line_ids = fields.One2many(
        'rental.scope.line', 'sale_order_id', string="Rental Scope"
    )
    rental_replacement_order_count = fields.Integer(string='Replacement Orders', compute='_compute_replacement_order_count')
    replacement_order_id = fields.Many2one('sale.order')

    state = fields.Selection(
        selection_add=[('draft', 'Quotation'),  ('waiting_approve', 'Waiting For Approval'), ('approved', 'Approved'), ('sent', 'Quotation Sent'), ('sale', 'Sales Order'),
                       ('reject', 'Rejected')],
        ondelete={
            'waiting_approve': 'cascade',
            'approved': 'cascade',
            'sale': 'cascade',
            'reject': 'cascade'
        })
    rental_status = fields.Selection(
        selection_add=[('draft', 'Quotation'),
                       ('waiting_approve', 'Waiting For Approval'),
                       ('approved', 'Approved'),
                       ('sent', 'Quotation Sent'),
                       ('sale', 'Sales Order'),
                       ('reject', 'Rejected')],
        ondelete={
            'waiting_approve': 'cascade',
            'approved': 'cascade',
            'sale': 'cascade',
            'reject': 'cascade'
        })

    is_rental_order_check = fields.Boolean(string='Is Rental Order')
    is_rental_state_check = fields.Boolean(string="Is Rental State Check")


    def action_advanced_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'context': {
                'active_model': 'account.move.line',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_rental_break_down(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Breakdown',
            'res_model': 'rental.breakdown.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_rental_order_id': self.id},
        }
    # for rec in self:
    #     rec.write({'has_breakdown_lines': True,
    #                'rental_status': 'breakdown'
    #                })

    def action_extend_rental(self):
        return {
            'name': 'Extend Rental Period',
            'type': 'ir.actions.act_window',
            'res_model': 'rental.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_rental_order_id': self.id,
            },
        }

    def _prepare_confirmation_values(self):
        """override"""
        if self.is_rental_order:
            for product in self.order_line:
                if product.product_template_id.rent_ok:
                    if self.project_created == False:
                        rental_project = self.env['project.project'].sudo().create({
                            'rental_sale_order_id': self.id,
                            'is_rental_project': True,
                            'name': 'Rental -'+self.name,
                            'analytic_account_id': self.analytic_account_id.id,
                            'privacy_visibility': 'employees',
                            'rating_status': 'stage',
                            'rating_status_period': 'monthly',
                            'last_update_status': 'on_track',
                            'partner_id': self.partner_id.id,
                        })
                        self.env['project.task'].sudo().create({
                            'name': 'Rental '+product.product_template_id.name,
                            'project_id': rental_project.id,
                            'is_rental_task': True,
                            'rental_sale_order_id': self.id,
                            'user_ids': None,
                        })
                        self.project_created == True
        return {
            'state': 'sale',
            'date_order': fields.Datetime.now()
        }

    def _compute_project_count(self):
        for record in self:
            record.rental_project_count = self.env['project.project'].search_count(
                [('rental_sale_order_id', '=', self.id), ('is_rental_project', '=', True)])

    def _compute_replacement_order_count(self):
        for record in self:
            record.rental_replacement_order_count = self.env['sale.order'].search_count(
                [('replacement_order_id', '=', self.id)])

    def _compute_task_count(self):
        for record in self:
            record.rental_tasks_count = self.env['project.task'].search_count([('project_id.rental_sale_order_id', '=', self.id)])

    def action_get_rental_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Project',
            'view_mode': 'tree,form',
            'res_model': 'project.project',
            'domain': [('rental_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_get_rental_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Task',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'domain': [('project_id.rental_sale_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_open_return(self):
        self.ensure_one()
        res = super(SaleOrder, self).action_open_return()
        if self.is_rental_order:
            if self.rental_terms:
                hours_spent = 0
                monthly_hours = 0
                total_hours_spent = 0
                rental_project = self.env['project.project'].search([('rental_sale_order_id', '=', self.id)])
                if self.rental_terms == 'per_hour':
                    timesheet_lines = rental_project.task_ids.timesheet_ids
                    if timesheet_lines:
                        total_break_down_hours = sum(
                            unit.amount for unit in timesheet_lines if unit.timesheet_type == 'break_down')
                        total_idling_hours = sum(
                            unit.unit_amount for unit in timesheet_lines if unit.timesheet_type == 'idling')
                        total_hours_spent = sum(unit.unit_amount for unit in timesheet_lines if
                                                unit.timesheet_type not in ['break_down', 'idling'])

                    # Add the service product to the sale order line
                    if total_hours_spent > 0:
                        # Retrieve the product
                        rental_service_product = self.env['product.product'].search(
                            [('default_code', '=', 'RENT_001')], limit=1)
                        if rental_service_product:
                            # Search for an existing order line with the product
                            existing_lines = self.order_line
                            for existing_line in existing_lines:
                                if existing_line:
                                    # If the product exists in the order line, update its name
                                    existing_product_names = existing_line.name or rental_service_product.name
                                    new_line_name = f"Rental Service Charge for {existing_product_names}"
                                    existing_line.name = new_line_name
                                    # existing_driven_hours = existing_line.product_template_id.vehicle_id.driven_hours
                                    vehicle = existing_line.product_template_id.vehicle_id
                                    if vehicle:
                                        vehicle.driven_hours += total_hours_spent
                                    # total_driven_hours = existing_driven_hours + total_hours_spent

                                else:
                                    # If no existing line, create a new one
                                    self.order_line.create({
                                        'order_id': self.id,
                                        'product_id': rental_service_product.id,
                                        'name': rental_service_product.name,
                                        'product_uom_qty': total_hours_spent,
                                        'price_unit': rental_service_product.lst_price,
                                        'product_uom': rental_service_product.uom_id.id,
                                    })

                elif self.rental_terms == 'per_day':
                    timesheet_lines = rental_project.task_ids.timesheet_ids
                    if timesheet_lines:
                        total_break_down_hours = sum(
                            unit.amount for unit in timesheet_lines if unit.timesheet_type == 'break_down')
                        total_idling_hours = sum(
                            unit.unit_amount for unit in timesheet_lines if unit.timesheet_type == 'idling')
                        total_hours_spent = sum(unit.unit_amount for unit in timesheet_lines if
                                                unit.timesheet_type not in ['break_down', 'idling'])

                    # Add the service product to the sale order line
                    if total_hours_spent > 0:
                        # Retrieve the product
                        rental_service_product = self.env['product.product'].search(
                            [('default_code', '=', 'RENT_004')], limit=1)
                        if rental_service_product:
                            # Search for an existing order line with the product
                            existing_lines = self.order_line
                            for existing_line in existing_lines:
                                if existing_line:
                                    # If the product exists in the order line, update its name
                                    existing_product_names = existing_line.name or rental_service_product.name
                                    new_line_name = f"Rental Service Charge for {existing_product_names}"
                                    existing_line.name = new_line_name
                                    # existing_driven_hours = existing_line.product_template_id.vehicle_id.driven_hours
                                    vehicle = existing_line.product_template_id.vehicle_id
                                    if vehicle:
                                        vehicle.driven_hours += total_hours_spent
                                    # total_driven_hours = existing_driven_hours + total_hours_spent

                                else:
                                    # If no existing line, create a new one
                                    self.order_line.create({
                                        'order_id': self.id,
                                        'product_id': rental_service_product.id,
                                        'name': rental_service_product.name,
                                        'product_uom_qty': total_hours_spent,
                                        'price_unit': rental_service_product.lst_price,
                                        'product_uom': rental_service_product.uom_id.id,
                                    })
                elif self.rental_terms == 'per_month':
                    timesheet_lines = rental_project.task_ids.timesheet_ids
                    if timesheet_lines:
                        total_break_down_hours = sum(
                            unit.amount for unit in timesheet_lines if unit.timesheet_type == 'break_down')
                        total_idling_hours = sum(
                            unit.unit_amount for unit in timesheet_lines if unit.timesheet_type == 'idling')
                        total_hours_spent = sum(unit.unit_amount for unit in timesheet_lines if
                                                unit.timesheet_type not in ['break_down', 'idling'])

                    # Add the service product to the sale order line
                    if total_hours_spent > 0:
                        # Retrieve the product
                        rental_service_product = self.env['product.product'].search(
                            [('default_code', '=', 'RENT_004')], limit=1)
                        if rental_service_product:
                            # Search for an existing order line with the product
                            existing_lines = self.order_line
                            for existing_line in existing_lines:
                                if existing_line:
                                    # If the product exists in the order line, update its name
                                    existing_product_names = existing_line.name or rental_service_product.name
                                    new_line_name = f"Rental Service Charge for {existing_product_names}"
                                    existing_line.name = new_line_name
                                    # existing_driven_hours = existing_line.product_template_id.vehicle_id.driven_hours
                                    vehicle = existing_line.product_template_id.vehicle_id
                                    if vehicle:
                                        vehicle.driven_hours += total_hours_spent
                                    # total_driven_hours = existing_driven_hours + total_hours_spent

                                else:
                                    # If no existing line, create a new one
                                    self.order_line.create({
                                        'order_id': self.id,
                                        'product_id': rental_service_product.id,
                                        'name': rental_service_product.name,
                                        'product_uom_qty': total_hours_spent,
                                        'price_unit': rental_service_product.lst_price,
                                        'product_uom': rental_service_product.uom_id.id,
                                    })
                else:
                    timesheet_lines = rental_project.task_ids.timesheet_ids
                    if timesheet_lines:
                        total_break_down_hours = sum(
                            unit.amount for unit in timesheet_lines if unit.timesheet_type == 'break_down')
                        total_idling_hours = sum(
                            unit.unit_amount for unit in timesheet_lines if unit.timesheet_type == 'idling')
                        total_hours_spent = sum(unit.unit_amount for unit in timesheet_lines if
                                                unit.timesheet_type not in ['break_down', 'idling'])

                    # Add the service product to the sale order line
                    if total_hours_spent > 0:
                        # Retrieve the product
                        rental_service_product = self.env['product.product'].search(
                            [('default_code', '=', 'RENT_004')], limit=1)
                        if rental_service_product:
                            # Search for an existing order line with the product
                            existing_lines = self.order_line
                            for existing_line in existing_lines:
                                if existing_line:
                                    # If the product exists in the order line, update its name
                                    existing_product_names = existing_line.name or rental_service_product.name
                                    new_line_name = f"Rental Service Charge for {existing_product_names}"
                                    existing_line.name = new_line_name
                                    # existing_driven_hours = existing_line.product_template_id.vehicle_id.driven_hours
                                    vehicle = existing_line.product_template_id.vehicle_id
                                    if vehicle:
                                        vehicle.driven_hours += total_hours_spent
                                    # total_driven_hours = existing_driven_hours + total_hours_spent

                                else:
                                    # If no existing line, create a new one
                                    self.order_line.create({
                                        'order_id': self.id,
                                        'product_id': rental_service_product.id,
                                        'name': rental_service_product.name,
                                        'product_uom_qty': total_hours_spent,
                                        'price_unit': rental_service_product.lst_price,
                                        'product_uom': rental_service_product.uom_id.id,
                                    })
                return res

    def action_get_rental_breakdown_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Replacement Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('replacement_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def _action_cancel(self):
        res = super(SaleOrder, self)._action_cancel()
        rental_project = self.env['project.project'].search([('rental_sale_order_id', '=', self.id)])
        for rec in rental_project:
            if rental_project:
                if rec.id:
                    delete_query = "DELETE FROM project_project WHERE id=%s" % rental_project.id
                    rental_project = False
                    self.env.cr.execute(delete_query)
        return res

    def action_continue(self):
        for rec in self:
            rec.write({'rental_status': 'return'})



    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        res = super(SaleOrder, self).message_post()
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'draft' or o.state == 'approved').with_context(tracking_disable=True).write({'state': 'sent'})
        return res

    def _create_invoices(self, grouped=False, final=False, date=None):
        # Call the super method to create the invoices
        res = super()._create_invoices(grouped=grouped, final=final, date=date)

        # Retrieve the start and end dates from the context
        start_date = self.env.context.get('timesheet_start_date')
        end_date = self.env.context.get('timesheet_end_date')

        # Iterate over each sale order
        for order in self:
            # Find the rental project associated with the sale order
            rental_project = self.env['project.project'].search([('rental_sale_order_id', '=', order.id)])

            # Check if the dates and rental project are valid
            if start_date and end_date and rental_project:
                # Filter timesheets within the specified date range and check `is_invoiceable_entry`
                timesheet_lines = rental_project.task_ids.timesheet_ids.filtered(
                    lambda t: start_date <= t.date <= end_date and not t.is_invoiceable_entry
                )

                # Compute the total hours from the filtered timesheets
                total_timesheet_hours = sum(timesheet_lines.mapped('unit_amount'))

                # Update timesheet lines to mark them as invoiceable
                timesheet_lines.write({'is_invoiceable_entry': True})

                # Iterate over the created invoices
                for invoice in res:
                    invoice.write({'is_rental_invoice': True})
                    for line in invoice.invoice_line_ids:
                        if line.sale_line_ids and line.sale_line_ids[0].order_id == order:
                            secondary_uom_id = order.order_line[
                                0].secondry_product_uom.id if order.order_line else False
                            line.write({
                                'secondary_product_uom_qty': total_timesheet_hours or 0.0,
                                'secondry_product_uom': secondary_uom_id,
                            })
                for line in order.order_line:
                    total_timesheet_hours_product_uom = sum(rental_project.task_ids.timesheet_ids.mapped('unit_amount'))
                    line.write({
                        'product_uom_qty': total_timesheet_hours_product_uom or 0.0,
                        'secondary_product_uom_qty': total_timesheet_hours_product_uom or 0.0,
                    })

        # Ensure `moves` is valid before calling `_link_timesheets_to_invoice`
        moves = res.mapped('invoice_line_ids.move_id')
        if moves:
            moves._link_timesheets_to_invoice(start_date, end_date)

        return res
