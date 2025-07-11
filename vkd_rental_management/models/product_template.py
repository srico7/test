# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import operator as py_operator
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    secondry_product_uom = fields.Many2one('uom.uom', 'Secondary UOM', store=True)
    secondary_uom_ids = fields.Many2many('uom.uom', compute='_compute_uom_id')
    secondary_uom_name = fields.Char(string='secondary UOM', related='secondry_product_uom.name', readonly=True)

    @api.depends('uom_id')
    def _compute_uom_id(self):
        if self.uom_id:
            self.secondary_uom_ids = self.uom_id.category_id.uom_ids or False

