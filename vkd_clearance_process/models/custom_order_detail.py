from odoo import _, api, fields, models


class CustomOrderDetail(models.Model):
    _name = 'custom.order.detail'

    custom_sale_order_id = fields.Many2one('sale.order')
