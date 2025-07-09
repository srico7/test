from odoo import fields, models, api


class PortGatePass(models.Model):
    _name = 'port.gate.pass'
    _description = 'Port Gate Pass'

    name = fields.Char(string='Serial No', required=True)
    bl_id = fields.Many2one('port.bl.details', string='Bill of Lading')

    approved_by = fields.Char(string='Approved By')
    approved_date = fields.Datetime(string='Approved Date')
    mfda_approved_by = fields.Char(string='MFDA Approved By')
    mndf_approved_by = fields.Char(string='MNDF Approved By')
    pharmaceutical_approved_by = fields.Char(string='Pharmaceutical Approved By')
    quarantine_released_by = fields.Char(string='Quarantine Released By')

    r_form_no = fields.Char(string='R Form Number')
    seriel_no = fields.Char(string='Serial Number')
    transport_mode = fields.Selection([
        ('0', 'Vehicle'),
        ('1', 'Other')
    ], string='Transport Mode')
    transport_mode_name = fields.Char(string='Transport Mode Name')
    remarks = fields.Text(string='Remarks')
    status = fields.Integer(string='Status')

    location_id = fields.Integer(string='Location ID')
    delivery_order_assignment_id = fields.Integer(string='Delivery Order Assignment ID')

    sale_order_id = fields.Many2one('sale.order', string='Sale Order Reference')

    @api.model
    def create_or_update(self, bl_record, vals):
        existing_gp = self.env['port.gate.pass'].search([('bl_id', '=', bl_record.id)])
        if existing_gp:
            existing_gp.write(vals)
        else:
            self.create(vals)
