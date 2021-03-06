# -*- coding: utf-8 -*-
{
    'name': "lty_operating_supply",

    'summary': """
        运营管理""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['operation_menu', 'lty_dispatch_desktop_widget'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/passengerFlow_views.xml',
        'views/satisfaction_views.xml',
        'views/service_views.xml',
        'views/line_bus_employee_shedule_views.xml',
		
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}