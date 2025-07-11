from odoo import fields, models, _, api
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby


class ProjectProject(models.Model):
    _inherit = 'project.project'

    rental_sale_order_id = fields.Many2one('sale.order')
    is_rental_project = fields.Boolean(default=False)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    rental_sale_order_id = fields.Many2one('sale.order')
    is_rental_task = fields.Boolean(default=False)
    timesheet_type = fields.Selection([
        ('working_time', 'Working Time'),
        ('break_down', 'Break Down'),
        ('idling', 'Idling'),
    ], string='Timesheet Type')
