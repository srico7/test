
# Part of Alex Lyngsoe. See LICENSE file for full copyright and licensing details.

{
    'name': "Sale ID Invoice",
    'version': '18.0.2.0.0',
    'category': 'Sales',
    'license': 'Other proprietary',
    'summary': """Sale ID Invoice""",
    'description': """
  Sale ID Invoice
    """,
    'author': 'FlexERP',
    'website': 'www.flexerp.dk',
    'depends': [
        'sale_management',
    ],
    'data': [
        'views/account_invoice_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
