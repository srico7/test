from odoo import models, fields, api
from datetime import datetime


class PortBLDetails(models.Model):
    _name = 'port.bl.details'
    _description = 'Port BL Details'
    _rec_name = 'bl_number'

    bl_number = fields.Char(string='BL Number', required=True)
    bl_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string='BL Type')

    auction_session_shipment_id = fields.Integer(string='Auction Session Shipment ID')
    bill_of_lading_date = fields.Datetime(string='Bill of Lading Date')
    document_id = fields.Integer(string='Document ID')

    cargo_ids = fields.One2many(comodel_name='port.bl.cargo', inverse_name='bl_id', string='Cargos')
    gate_pass_ids = fields.One2many(comodel_name='port.gate.pass', inverse_name='bl_id', string='Gate Passes')
    port_bl_id = fields.Many2one(comodel_name='port.bl', string='Port BL')

    broker = fields.Char(string='Broker')
    consignee_id = fields.Many2one('port.api.config', string='Consignee')
    shipper = fields.Integer(string='Shipper')
    voyage = fields.Char(string='Voyage')
    voyage_id = fields.Integer(string='Voyage ID')
    user_id = fields.Integer(string='User ID')
    new_user_id = fields.Integer(string='New User ID')

    created_at = fields.Datetime(string='Created At')
    approved_at = fields.Datetime(string='Approved At')
    date_received = fields.Datetime(string='Date Received')
    clearing_date = fields.Date(string='Clearing Date')
    do_exp_date = fields.Date(string='DO Expiry Date')
    updated_at = fields.Datetime(string='Updated At')
    deleted_at = fields.Datetime(string='Deleted At')

    approved = fields.Integer(string='Approved')
    status = fields.Integer(string='Status')
    entry_status = fields.Integer(string='Entry Status')
    is_clear = fields.Boolean(string='Is Clear')
    is_sea_to_air = fields.Boolean(string='Is Sea to Air')
    tallied_status = fields.Integer(string='Tallied Status')
    cleared_status = fields.Integer(string='Cleared Status')
    personal_effects = fields.Boolean(string='Personal Effects')
    open = fields.Boolean(string='Open')
    transit = fields.Boolean(string='Transit')

    mark_nos = fields.Char(string='Mark Numbers')
    cargo_count = fields.Integer(string='Cargo Count')
    total_volume = fields.Float(string='Total Volume')
    tallied_quantity = fields.Float(string='Tallied Quantity')
    port_of_loading = fields.Integer(string='Port of Loading')
    country_of_origin = fields.Integer(string='Country of Origin')

    transhipment_port = fields.Char(string='Transhipment Port')
    transhipment_port_id = fields.Integer(string='Transhipment Port ID')

    file_id = fields.Integer(string='File ID')
    profile_version_id = fields.Integer(string='Profile Version ID')
    profileable_id = fields.Integer(string='Profileable ID')
    hw_payment_status = fields.Selection([
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid')
    ], string='HW Payment Status')


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
    def create_or_update(self, bl_data, port_bl_id):
        doc_data = bl_data.get('document', {})
        if not doc_data:
            doc_data = bl_data

        bl_vals = {
            'port_bl_id': port_bl_id,
            'bl_number': doc_data.get('bill_of_lading_number'),
            'bl_type': doc_data.get('bl_type'),
            'document_id': doc_data.get('id'),
            'auction_session_shipment_id': doc_data.get('auction_session_shipment_id'),
            'bill_of_lading_date': self._parse_date(doc_data.get('bill_of_lading_date')),

            'broker': doc_data.get('broker'),
            'consignee_id': doc_data.get('consignee_id'),
            'shipper': doc_data.get('shipper'),
            'voyage': doc_data.get('voyage'),
            'voyage_id': doc_data.get('voyage_id'),
            'user_id': doc_data.get('user_id'),
            'new_user_id': doc_data.get('new_user_id'),

            'created_at': self._parse_date(doc_data.get('created_at')),
            'approved_at': self._parse_date(doc_data.get('approved_at')),
            'date_received': self._parse_date(doc_data.get('date_received')),
            'clearing_date': doc_data.get('clearing_date'),
            'do_exp_date': doc_data.get('do_exp_date'),
            'updated_at': self._parse_date(doc_data.get('updated_at')),
            'deleted_at': self._parse_date(doc_data.get('deleted_at')),

            'approved': doc_data.get('approved'),
            'status': doc_data.get('status'),
            'entry_status': doc_data.get('entry_status'),
            'is_clear': doc_data.get('is_clear'),
            'is_sea_to_air': doc_data.get('is_sea_to_air'),
            'personal_effects': doc_data.get('personal_effects'),
            'open': doc_data.get('open'),
            'transit': doc_data.get('transit'),
            'cleared_status': bl_data.get('cleared_status'),
            'tallied_status': bl_data.get('tallied_status'),

            'mark_nos': doc_data.get('mark_nos'),
            'cargo_count': doc_data.get('cargo_count'),
            'total_volume': doc_data.get('total_volume'),
            'tallied_quantity': doc_data.get('tallied_quantity'),
            'port_of_loading': doc_data.get('port_of_loading'),
            'country_of_origin': doc_data.get('country_of_origin'),
            'transhipment_port': doc_data.get('transhipment_port'),
            'transhipment_port_id': doc_data.get('transhipment_port_id'),

            'file_id': doc_data.get('file_id'),
            'profile_version_id': doc_data.get('profile_version_id'),
            'profileable_id': doc_data.get('profileable_id'),
            'hw_payment_status': 'paid' if doc_data.get('hw_payment_details', {}).get('status') == 'Paid' else 'unpaid'
        }

        existing_bl = self.search([('bl_number', '=', bl_vals['bl_number'])])
        if existing_bl:
            existing_bl.write(bl_vals)
            bl_record = existing_bl
        else:
            bl_record = self.create(bl_vals)

        cargo_data = doc_data.get('cargo_view', []) or bl_data.get('cargos', [])
        if cargo_data:
            for cargo in cargo_data:
                cargo_vals = {
                    'bl_id': bl_record.id,
                    'name': cargo.get('name'),
                    'container_no': cargo.get('container_no'),
                    'container_type': cargo.get('container_type'),
                    'cargo_type': cargo.get('cargo_type'),
                    'description': cargo.get('description'),
                    'quantity': cargo.get('quantity'),
                    'cleared_qty': cargo.get('cleared_qty'),
                    'tallied_qty': cargo.get('tallied_qty'),
                    'container_tallied_qty': cargo.get('container_tallied_qty'),
                    'cubic_meter': cargo.get('cubic_meter'),
                    'gross_weight': cargo.get('gross_weight'),
                    'freight_tonnage': cargo.get('freight_tonnage'),
                    'mark_nos': cargo.get('mark_nos'),
                    'package_type': cargo.get('package_type'),
                    'package_type_id': cargo.get('package_type_id'),
                    'size': cargo.get('size'),
                    'in_container': cargo.get('in_container'),
                    'container_term': cargo.get('container_term'),
                    'held': cargo.get('held'),
                    'held_by_mpl': cargo.get('held_by_mpl'),
                    'held_by_agent': cargo.get('held_by_agent'),
                }
                self.env['port.bl.cargo'].create_or_update(bl_record, cargo_vals)

        gate_passes = bl_data.get('gate_passes', [])
        if gate_passes:
            for gate in gate_passes:
                gate_vals = {
                    'bl_id': bl_record.id,
                    'name': gate.get('seriel_no'),
                    'approved_by': gate.get('approved_by'),
                    'approved_date': self._parse_date(gate.get('approved_date')),
                    'r_form_no': gate.get('r_form_no'),
                    'seriel_no': gate.get('seriel_no'),
                    'transport_mode': gate.get('transport_mode'),
                    'transport_mode_name': gate.get('transport_mode_name'),
                    'status': gate.get('status'),
                }
                self.env['port.gate.pass'].create_or_update(bl_record, gate_vals)

        return bl_record