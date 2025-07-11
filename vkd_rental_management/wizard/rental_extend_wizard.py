from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class rental_extend_wizard(models.TransientModel):
    _name = 'rental.extend.wizard'
    _description = 'Rental Extend Wizard'

    rental_order_id = fields.Many2one('sale.order', string="Rental Order", required=True)
    new_start_date = fields.Datetime(string="New Start Date", required=True)
    new_return_date = fields.Datetime(string="New Return Date", required=True)
    reason = fields.Text(string="Reason for Extension", required=True)

    def action_confirm_extension(self):
        for wizard in self:
            rental_order = wizard.rental_order_id
            # Store the old dates in the history model
            if rental_order.rental_start_date and rental_order.rental_return_date:
                self.env['rental.extend.history'].create({
                    'rental_order_id': rental_order.id,
                    'start_date': rental_order.rental_start_date,
                    'return_date': rental_order.rental_return_date,
                    'reason': wizard.reason,
                })
            # Update the rental order with the new dates
            rental_order.write({
                'rental_start_date': wizard.new_start_date,
                'rental_return_date': wizard.new_return_date,
            })