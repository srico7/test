from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    use_quotation_approval = fields.Boolean(string='Use Quotation Approvals',
                                            config_parameter='vkd_rental_management.use_quotation_approval')
    quotation_approval_user_id = fields.Many2one('res.users', string='Assign Approval to',
                                                 config_parameter='vkd_rental_management.quotation_approval_user_id')
    quotation_approval_additional_user_id = fields.Many2one('res.users', string='Assign Additional Approval to',
                                                            config_parameter='vkd_rental_management.quotation_approval_additional_user_id')
    quotation_confirm_group_id = fields.Many2one('res.groups', string='Quotation Confirm Approval Group',
                                                 config_parameter='vkd_rental_management.quotation_confirm_group_id')
    quotation_confirm_user_id = fields.Many2one('res.users', string='Confirm Quotation/Sale Order',
                                                domain="[('groups_id','in',quotation_confirm_group_id)]",
                                                config_parameter='vkd_rental_management.quotation_confirm_user_id')