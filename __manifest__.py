{
    'name': 'Integración GPS con e-Vision GPS',
    'version': '1.0',
    'summary': 'Integración del módulo Fleet de Odoo con e-Vision GPS para rastreo de vehículos.',
    'description': 'Este módulo permite conectar Odoo con e-Vision GPS para rastrear vehículos.',
    'author': 'Tu Nombre',
    'category': 'Fleet',
    'depends': ['fleet', 'base'],
    'data': [
        'views/gps_settings_views.xml',
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',  # Si tienes 
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}