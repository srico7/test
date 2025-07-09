from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    port_bl_id = fields.Many2one('port.bl', string='BL details')
    cargo_ids = fields.One2many('port.bl.cargo', 'sale_order_id',
                                string='Cargos', store=True)
    gate_pass_ids = fields.One2many('port.gate.pass', 'sale_order_id',
                                    string='Gate Passes', store=True)

    @api.onchange('port_bl_id')
    def _onchange_port_bl_id(self):
        if self.port_bl_id:
            if not isinstance(self.id, models.NewId):
                existing_order = self.env['sale.order'].search([
                    ('port_bl_id', '=', self.port_bl_id.id),
                    ('id', '!=', self.id)
                ], limit=1)
            else:
                existing_order = self.env['sale.order'].search([
                    ('port_bl_id', '=', self.port_bl_id.id)
                ], limit=1)

                if existing_order:
                    self.port_bl_id = False
                    return {
                        'warning': {
                            'title': _('Warning'),
                            'message': _('This BL is already linked to Sale Order: %s') % existing_order.name
                        }
                    }

            if existing_order:
                self.port_bl_id = False
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('This BL is already linked to Sale Order: %s') % existing_order.name
                    }
                }
            else:
                self.bl_number = self.port_bl_id.bl_number
                self.arrived_date = self.port_bl_id.arrival_at

                bl_details = self.env['port.bl.details'].search([
                    ('document_id', '=', self.port_bl_id.bl_id)
                ], limit=1)

                if bl_details:
                    cargo_records = [(6, 0, bl_details.cargo_ids.ids)]
                    gate_pass_records = [(6, 0, bl_details.gate_pass_ids.ids)]

                    self.update({
                        'cargo_ids': cargo_records,
                        'gate_pass_ids': gate_pass_records,
                        'register_form_number': bl_details.gate_pass_ids[
                            0].r_form_no if bl_details.gate_pass_ids else False,
                    })

                    bl_details.cargo_ids.write({'sale_order_id': self._origin.id})
                    bl_details.gate_pass_ids.write({'sale_order_id': self._origin.id})

                    # ---- Update Sale Order Lines based on Cargo Details ----
                    order_lines = []
                    for cargo in bl_details.cargo_ids:
                        # Example: Check cargo size and create sale order lines accordingly
                        size_20_product = self.env['product.product'].search([('default_code', '=', cargo.size)],
                                                                     limit=1)
                        size_40_product = self.env['product.product'].search([('default_code', '=', cargo.size)],
                                                                             limit=1)
                        if size_20_product:
                            order_lines.append((0, 0, {
                                'product_id': size_20_product.id,
                                'name': cargo.name,
                                'product_uom_qty': 1,  # Assuming `size` is the quantity
                                'product_uom': size_20_product.uom_id.id,
                                'price_unit': size_20_product.lst_price,
                                'container_no': cargo.container_no,
                                'volume': cargo.cubic_meter,
                            }))
                        else:
                            if size_40_product:
                                order_lines.append((0, 0, {
                                    'product_id': size_20_product.id,
                                    'name': cargo.name,
                                    'product_uom_qty': 1,  # Assuming `size` is the quantity
                                    'product_uom': size_40_product.uom_id.id,
                                    'price_unit': size_40_product.lst_price,
                                    'container_no': cargo.container_no,
                                    'volume': cargo.cubic_meter,
                                }))

                    # Remove existing lines and add new ones
                    self.order_line = [(5, 0, 0)] + order_lines
        else:
            self.update({
                'bl_number': False,
                'arrived_date': False,
                'cargo_ids': [(5, 0, 0)],
                'gate_pass_ids': [(5, 0, 0)],
                'order_line': [(5, 0, 0)],  # Clear order lines when BL is removed
            })

    @api.model
    def default_get(self, fields):
        res = super(SaleOrder, self).default_get(fields)
        context = self._context

        if context.get('default_port_bl_id'):
            bl_record = self.env['port.bl'].browse(context.get('default_port_bl_id'))
            bl_details = self.env['port.bl.details'].search([
                ('document_id', '=', bl_record.bl_id)
            ], limit=1)

            if bl_details:
                self.port_bl_id = bl_record
                self.bl_number = bl_record.bl_number
                self.arrived_date = bl_record.arrival_at

                cargo_records = [(6, 0, bl_details.cargo_ids.ids)]
                gate_pass_records = [(6, 0, bl_details.gate_pass_ids.ids)]

                self.update({
                    'cargo_ids': cargo_records,
                    'gate_pass_ids': gate_pass_records,
                })

                bl_details.cargo_ids.write({'sale_order_id': self._origin.id})
                bl_details.gate_pass_ids.write({'sale_order_id': self._origin.id})

        return res
