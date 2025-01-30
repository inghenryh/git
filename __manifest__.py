{
    'name': 'Integración GPS con e-Vision GPS',
    'version': '1.0',
    'summary': 'Integración del módulo Fleet de Odoo con e-Vision GPS para rastreo de vehículos.',
    'description': 'Este módulo permite conectar Odoo con e-Vision GPS para rastrear vehículos en tiempo real.',
    'author': 'Tu Nombre',
    'category': 'Fleet',
    'depends': ['fleet', 'base'],
    'data': [
        'security/ir.model.access.csv',  # Asegura los permisos
        'views/fleet_vehicle_views.xml',  # Vista del formulario de vehículo
        'views/gps_settings_views.xml',  # Configuración del GPS
        'views/fleet_vehicle_map.xml',  # Mapa de ubicación
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
