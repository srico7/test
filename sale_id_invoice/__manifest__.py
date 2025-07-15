{
    'name': "Sale ID Invoice",
    'version': '18.0.2.0.1',
    'category': 'Sales',
    'license': 'OPL-1',
    'summary': """Links customer invoices back to the sales order they originated from.""",
    'description': """
  Links customer invoices back to the sales order they originated from.
    """,
    'author': 'FlexERP',
    'website': 'www.flexerp.dk',
    'depends': [
        'sale_management',
        'account',
    ],
    'data': [
        'views/account_invoice_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
