from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BLSelectionWizard(models.TransientModel):
    _name = 'bl.search'
    _description = 'BL Search'

    bl_number = fields.Char(string='BL Number', required=True)
    api_config_id = fields.Many2one('port.api.config', string='Consignee', required=True)

    def fetch_bl_by_search(self):
        api_config = self.api_config_id
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')

        if api_config:
            api_config.fetch_bl_by_search(bl_name=self.bl_number)

            bl_record = self.env['port.bl'].search([('bl_number', '=', self.bl_number)], limit=1)

            if not bl_record:
                raise UserError(_("No Bill of Lading found with number: %s") % self.bl_number)

            if bl_record and active_id and active_model == 'sale.order':
                sale_order = self.env['sale.order'].browse(active_id)
                if not sale_order:
                    raise UserError(_("Sale order not found"))

                bl_details = self.env['port.bl.details'].search([
                    ('document_id', '=', bl_record.bl_id)
                ], limit=1)

                if bl_details:
                    values = {
                        'port_bl_id': bl_record.id,
                        'bl_number': bl_record.bl_number,
                        'arrived_date': bl_record.arrival_at,
                        'cargo_ids': [(6, 0, bl_details.cargo_ids.ids)],
                        'gate_pass_ids': [(6, 0, bl_details.gate_pass_ids.ids)],
                    }

                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'sale.order',
                        'res_id': active_id,
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'current',
                        'context': {'default_port_bl_id': bl_record.id},
                    }

        return False
