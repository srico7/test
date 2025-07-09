from odoo import models, fields, api
from datetime import datetime


class PortBL(models.Model):
    _name = 'port.bl'
    _description = 'Bill of Lading'
    _rec_name = 'bl_number'

    bl_number = fields.Char(string='BL Number', required=True)
    bl_id = fields.Integer(string='BL ID')
    voyage_name = fields.Char(string='Voyage Name')
    voyage_id = fields.Integer(string='Voyage ID')
    bl_voyage_name = fields.Char(string='B/L Voyage Name')

    consignee_name = fields.Char(string='Consignee Name')
    formated_name = fields.Char(string='Formatted Name')
    mark_nos = fields.Char(string='Mark Numbers')

    created_at = fields.Datetime(string='Created At')
    approved_at = fields.Datetime(string='Approved At')
    arrival_at = fields.Datetime(string='Arrival At')
    date_received = fields.Datetime(string='Date Received')
    do_exp_date = fields.Date(string='DO Expiry Date')
    eta = fields.Char(string='ETA')
    clearing_date = fields.Date(string='Clearing Date')

    approved = fields.Integer(string='Approved')
    status = fields.Integer(string='Status')
    entry_status = fields.Integer(string='Entry Status')
    invoice_raised = fields.Boolean(string='Invoice Raised')
    is_sea_to_air = fields.Boolean(string='Is Sea to Air')

    cargo_count = fields.Integer(string='Cargo Count')
    total_volume = fields.Float(string='Total Volume')
    remaining_quantity = fields.Float(string='Remaining Quantity')
    country_of_origin = fields.Integer(string='Country of Origin')

    file_id = fields.Integer(string='File ID')
    broker_id = fields.Integer(string='Broker ID')
    profile_version_id = fields.Integer(string='Profile Version ID')

    blvoyage = fields.Char(string='BL Voyage Reference')
    port_api_config_id = fields.Many2one('port.api.config')

    def _parse_date(self, date_str):
        """
        - '01 Feb 2025 19:33'
        - '2025-02-01 19:33:00'
        """
        if not date_str:
            return False

        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d %b %Y %H:%M')
            except ValueError:
                return False

    @api.model
    def create_or_update(self, api_data, api_config=None):
        created_records = self.env['port.bl']
        for bl_data in api_data:
            vals = {
                'bl_id': bl_data.get('id'),
                'bl_number': bl_data.get('bill_of_lading_number') or bl_data.get('biloflading_document_no'),
                'voyage_name': bl_data.get('voyage_name'),
                'voyage_id': bl_data.get('voyage_id'),
                'bl_voyage_name': bl_data.get('bl_voyage_name'),
                'consignee_name': bl_data.get('consignee_name'),
                'formated_name': bl_data.get('formated_name'),
                'mark_nos': bl_data.get('mark_nos'),
                'created_at': self._parse_date(bl_data.get('created_at')),
                'approved_at': self._parse_date(bl_data.get('approved_at')),
                'arrival_at': self._parse_date(bl_data.get('arrival_at')),
                'date_received': self._parse_date(bl_data.get('date_received')),
                'do_exp_date': bl_data.get('do_exp_date'),
                'eta': bl_data.get('eta'),
                'clearing_date': bl_data.get('clearing_date'),
                'approved': bl_data.get('approved'),
                'status': bl_data.get('status'),
                'entry_status': bl_data.get('entry_status'),
                'invoice_raised': bool(bl_data.get('invoice_raised')),
                'is_sea_to_air': bl_data.get('is_sea_to_air'),
                'cargo_count': bl_data.get('cargo_count'),
                'total_volume': bl_data.get('total_volume'),
                'remaining_quantity': bl_data.get('remaining_quantity'),
                'country_of_origin': bl_data.get('country_of_origin'),
                'file_id': bl_data.get('file_id'),
                'broker_id': bl_data.get('broker_id'),
                'profile_version_id': bl_data.get('profile_version_id'),
                'blvoyage': bl_data.get('blvoyage'),
                'port_api_config_id': api_config
            }

            existing_bl = self.search([('bl_number', '=', vals['bl_number'])])
            if existing_bl:
                existing_bl.write(vals)
                created_records |= existing_bl
            else:
                record = self.create(vals)
                created_records |= record

        for record in created_records:
            if record.port_api_config_id:
                record.port_api_config_id.fetch_bl_details(bl_id=record.bl_id, port_bl_id=record.id)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.bl_number} - {record.voyage_name}" if record.voyage_name else record.bl_number
            result.append((record.id, name))
        return result

    def fetch_bl_list(self):
        api_config = self.env['port.api.config'].search([], limit=1)
        if api_config:
            api_config.fetch_bl_list()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bills of Lading',
                'res_model': 'port.bl',
                'view_mode': 'tree,form',
                'target': 'main',
            }

    def fetch_bl_details(self, bl_id=None, port_bl_id=None):
        self.ensure_one()
        if self.port_api_config_id:
            self.port_api_config_id.fetch_bl_details(bl_id=self.bl_id or bl_id, port_bl_id=self.id or port_bl_id, )
            return {
                'type': 'ir.actions.act_window',
                'name': 'BL Details',
                'res_model': 'port.bl.details',
                'view_mode': 'tree,form',
                'target': 'main',
            }
