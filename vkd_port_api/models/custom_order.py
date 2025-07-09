from odoo import fields, models, api


class ClearanceOrder(models.Model):
    _inherit = 'custom.order'

    register_form_number = fields.Char(string='R-Form Number', related='custom_sale_order_id.register_form_number')

