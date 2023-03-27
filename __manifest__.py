# -*- coding: utf-8 -*-
{
    'name': "open_academy_controllers",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'open_academy'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/courses_template.xml',
        'views/course_id_template.xml',
        'views/sessions_template.xml',
        'views/session_id_template.xml',
        'views/joined_session_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
