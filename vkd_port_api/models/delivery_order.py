from odoo import api, fields, models, _


class DeliveryOrder(models.Model):
    _inherit = 'delivery.order'

    approved_at = fields.Datetime(string='DO Approval')

    def action_status_check(self):
        for record in self:
            bl_id = record.delivery_sale_order_id.port_bl_id.bl_id
            port_bl_id = record.delivery_sale_order_id.port_bl_id
            record.delivery_sale_order_id.port_bl_id.port_api_config_id.fetch_bl_details(bl_id=bl_id,
                                                                                         port_bl_id=port_bl_id)

            bl_details = self.env['port.bl.details'].search([
                ('document_id', '=', bl_id)
            ], limit=1)

            record.approved_at = bl_details.approved_at if bl_details.approved_at else False
            record.arrived_date = port_bl_id.arrival_at if port_bl_id.arrival_at else False

            if record.arrived_date and record.arrived_date <= fields.Datetime.now():
                record.write({'delivery_state': 'arrived'})
            if record.approved_at and record.approved_at <= fields.Datetime.now():
                record.write({'delivery_state': 'do_approved'})

    @api.model
    def cron_action_status_check(self):
        delivery_orders = self.search([('delivery_state', '!=', 'do_approved')])
        if delivery_orders:
            delivery_orders.action_status_check()
