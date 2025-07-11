from odoo import fields, models, _


class AttachmentLine(models.Model):
    _name = 'rental.attachment.line'

    rental_job_id = fields.Many2one(
        comodel_name='rental.job',
        string="Rental Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    sale_order_id = fields.Many2one('sale.order', ondelete='cascade', index=True, copy=False)
    # Attachments

    attachment_name = fields.Char(string='Name')
    attachment_type = fields.Char(string='Attachment Type')
    attachment_file = fields.Binary(string='Attachment Reference',
                                    help="Attache reference for clearance with any attachment type(ex: image, pdf, excel)")