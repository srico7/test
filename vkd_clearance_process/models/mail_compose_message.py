from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        # Call the original _action_send_mail method
        res = super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)

        # Check if context contains a custom state to update
        if self.env.context.get('custom_state_to_update'):
            model = self.env.context.get('default_model')
            res_ids = self.env.context.get('default_res_ids')
            if model and res_ids:
                # Ensure res_ids is a list
                if not isinstance(res_ids, list):
                    res_ids = [res_ids]
                records = self.env[model].browse(res_ids)
                if records:
                    records.write({'custom_state': self.env.context['custom_state_to_update']})

        # Return the result as expected
        return res
