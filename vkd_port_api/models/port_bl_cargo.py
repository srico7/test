from odoo import models, fields, api


class PortBLCargo(models.Model):
    _name = 'port.bl.cargo'
    _description = 'Port BL Cargo'

    name = fields.Char(string='Name')
    bl_id = fields.Many2one(comodel_name='port.bl.details', string='Bill of Lading')

    container_no = fields.Char(string='Container Number')
    container_type = fields.Char(string='Container Type')
    container_term = fields.Integer(string='Container Term')
    in_container = fields.Boolean(string='In Container')
    size = fields.Integer(string='Size')

    cargo_type = fields.Char(string='Cargo Type')
    cargo_type_id = fields.Integer(string='Cargo Type ID')
    description = fields.Text(string='Description')
    package_type = fields.Char(string='Package Type')
    package_type_id = fields.Integer(string='Package Type ID')
    mark_nos = fields.Char(string='Mark Numbers')

    quantity = fields.Float(string='Quantity')
    cleared_qty = fields.Float(string='Cleared Quantity')
    tallied_qty = fields.Float(string='Tallied Quantity')
    container_tallied_qty = fields.Float(string='Container Tallied Quantity')
    packed_quantity = fields.Float(string='Packed Quantity')
    balance = fields.Float(string='Balance')

    cubic_meter = fields.Float(string='Cubic Meter')
    gross_weight = fields.Float(string='Gross Weight')
    freight_tonnage = fields.Float(string='Freight Tonnage')

    held = fields.Boolean(string='Held')
    held_by_mpl = fields.Boolean(string='Held by MPL')
    held_by_agent = fields.Boolean(string='Held by Agent')

    commodity_id = fields.Integer(string='Commodity ID')
    inward_list_id = fields.Integer(string='Inward List ID')
    profile_version_id = fields.Integer(string='Profile Version ID')

    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')

    @api.model
    def create_or_update(self, bl_record, vals):
        existing_cargo = self.env['port.bl.cargo'].search([('bl_id', '=', bl_record.id)])
        if existing_cargo:
            existing_cargo.write(vals)
        else:
            self.create(vals)
