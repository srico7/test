from odoo import models, fields
from odoo.exceptions import UserError, AccessError


class RentalBreakdownWizard(models.TransientModel):
    _name = 'rental.breakdown.wizard'
    _description = 'Rental Breakdown Wizard'

    breakdown_type = fields.Selection([
        ('replace', 'Replace'),
        ('service', 'Service')
    ], string='Breakdown Type', required=True, default='service')

    def confirm_action(self):
        active_id = self.env.context.get('active_id')
        rental_order = self.env['sale.order'].browse(active_id)
        if not rental_order:
            raise UserError("No active rental order found.")

        if self.breakdown_type == 'replace':
            # Create a new rental order without any lines
            new_order_vals = {
                'partner_id': rental_order.partner_id.id,  # Corrected field name
                'state': 'draft',  # Default state for a new order
                'origin': rental_order.name,
                'replacement_order_id': rental_order.id,
                'is_rental_order': True,
                'has_pickable_lines': True,
                'has_rented_products': True,
                'has_breakdown_lines': True,
            }
            new_order = self.env['sale.order'].create(new_order_vals)
            rental_order.message_post(
                body=f"A new rental order {new_order.name} has been created as a replacement."
            )
        elif self.breakdown_type == 'service':
            rental_order.write({
                'rental_status': 'breakdown',
                'has_breakdown_lines': True
            })
        return True
