# -*- coding: utf-8 -*-

{
    'name': "Port API Integration",
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': """Integration with Port BL API""",

    'description': """""",

    'author': "VK Data ApS",
    'website': "https://vkdata.dk",

    'depends': ['base', 'sale', 'vkd_clearance_process'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/port_bl_views.xml',
        'views/port_bl_details_views.xml',
        'wizard/bl_selection.xml',
        'views/sale_order_views.xml',
        'views/delivery_order_views.xml',
        'data/ir_cron_data.xml',
    ],
    'assets': {
       'web.assets_backend': [
           'vkd_port_api/static/src/js/button.js',
           'vkd_port_api/static/src/xml/button.xml',
       ],
    },
    'license': 'OPL-1',
    'application': False,
    'installable': True,
    'auto_install': False,
}