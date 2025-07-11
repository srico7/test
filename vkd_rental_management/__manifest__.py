{
    "name": "Rental Management",
    "summary": "Manage rental order scope before create quotation",
    "description": """ 
        Manage rental order scope before create quotation.
    """,
    "version": "17.0.1.0.0",
    "category": "Sales",
    'author': "VK DATA ApS",
    'website': "https://vkdata.dk",
    'license': 'OPL-1',
    "depends": ['sale_renting', 'project', 'hr_timesheet', 'purchase', 'sale_approval_sf', 'transport_module', 'product', 'account', 'vkd_asset_registry'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_data_sequence.xml',
        'data/rental_data.xml',
        'views/account_analytic_line_views.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/account_move_views.xml',
        'wizard/rental_extend_views.xml',
        'wizard/rental_break_down_views.xml',
        'wizard/sale_make_invoices_advance_views.xml',
    ],
    "installable": True,
}