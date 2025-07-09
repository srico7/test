
{
    'name': 'Clearance Process Management',
    'version': '17.0.2.0.0',
    'category': 'Sales',
    'description': """
        This module manage clearance process.
    """,
    'summary': """
        This module manage clearance process.
    """,
    'author': 'VK DATA ApS',
    'website': 'https://vkdata.dk',
    'depends': ['sale', 'portal', 'utm', 'purchase', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_data_sequence.xml',
        'data/clearance_order_data.xml',
        'data/mail_template.xml',
        'views/sale_order_views.xml',
        'views/delivery_order_views.xml',
        'views/clearance_order_views.xml',
        'views/custom_order_views.xml',
        'views/delivery_order_views.xml',
        'views/port_order_views.xml',
        'views/menu_item_views.xml',
        'views/custom_order_portal_views.xml',
        'wizard/advanced_payment_views.xml',
        'wizard/clarification_wizard_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'vkd_clearance_process/static/src/scss/style.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
