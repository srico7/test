from odoo import fields, models, _, api


class ClarificationWizard(models.TransientModel):
    _name = 'clarification.wizard'
    _description = 'Clarification Wizard'

    clarification_message = fields.Text(string="Message", required=True)

    def send_clarification_email(self):
        # Get the active record
        active_id = self.env.context.get('active_id')
        record = self.env['custom.order'].browse(active_id)

        # Send the email using the template
        template = self.env.ref('vkd_clearance_process.email_template_clarification')
        if template:
            # Render the email body dynamically
            body_html = template._render_template(template.body_html, 'custom.order', [record.id])[record.id]

            # Prepare email values
            email_values = {
                'subject': template.subject,
                'body_html': self.clarification_message or body_html,
                'email_from': template.email_from or self.env.user.email_formatted,
                'email_to': record.partner_id.email_formatted,
                'recipient_ids': [(4, record.partner_id.id)],
            }

            # Create and send the email
            self.env['mail.mail'].create(email_values).send()

            # Log the email in the chatter under "Send Message"
            record.message_post(
                body=self.clarification_message or body_html,
                subject=template.subject,
                partner_ids=[record.partner_id.id],
                message_type='email',
                email_from=email_values.get('email_from'),
            )

        # Update the state of the record
        record.write({'custom_state': 'clarification'})