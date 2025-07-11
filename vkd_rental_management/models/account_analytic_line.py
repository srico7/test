from odoo import fields, models, api
from datetime import timedelta


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    timesheet_type = fields.Selection([
        ('working_time', 'Working Time'),
        ('break_down', 'Break Down'),
        ('idling', 'Idling'),
    ], string='Timesheet Type')
    location = fields.Many2one('route.locations', string='Location')
    is_invoiceable_entry = fields.Boolean('Is invoiceable')

    def _update_secondary_uom_quantity(self, sale_line, new_qty):
        """
        Update the secondary_uom_quantity in sale order line.
        If a previous quantity was entered, update instead of replacing.
        """
        if sale_line:
            sale_line.secondary_uom_quantity += new_qty  # Adjust quantity
            sale_line._compute_secondry_product_uom()  # Ensure correct conversion

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to update secondary_uom_quantity on the sale order line.
        """
        records = super().create(vals_list)
        for record in records:
            if record.so_line:
                self._update_secondary_uom_quantity(record.so_line, record.unit_amount)
        return records

    @api.constrains('unit_amount')
    def _check_unit_amount(self):
        order_lines = self.project_id.rental_sale_order_id.order_line.filtered(lambda r: isinstance(r, models.Model))
        for rec in order_lines:
            total_hours = sum(self.task_id.timesheet_ids.mapped('unit_amount'))
            if rec.secondary_product_uom_qty < total_hours:
                balance_hours = total_hours - rec.secondary_product_uom_qty
                rec.secondary_product_uom_qty += balance_hours
                rec.product_uom_qty += balance_hours

