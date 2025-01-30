from odoo import models, fields, api
import requests

class EvisionGPSSettings(models.Model):
    _name = 'evisiongps.settings'
    _description = 'Configuración de e-Vision GPS'
    _rec_name = 'email'
    _order = 'id desc'

    email = fields.Char(string='Correo Electrónico', required=True)
    password = fields.Char(string='Contraseña', required=True)
    user_api_hash = fields.Char(string='Hash de Usuario', readonly=True)
    connection_status = fields.Selection([
        ('not_tested', 'No probado'),
        ('connected', 'Conectado'),
        ('disconnected', 'Desconectado'),
    ], string='Estado de Conexión', readonly=True, default='not_tested')

    @api.model
    def get_config_record(self):
        """Obtiene la configuración guardada. Si no existe, la crea y la devuelve."""
        config = self.search([], limit=1)
        if not config:
            config = self.create({
                'email': '',
                'password': '',
                'user_api_hash': '',
                'connection_status': 'not_tested'
            })
        return config

    @api.model
    def create(self, vals):
        """Si ya existe una configuración, actualizarla en lugar de crear una nueva."""
        existing = self.search([], limit=1)
        if existing:
            existing.write(vals)
            return existing
        return super(EvisionGPSSettings, self).create(vals)

    def test_connection(self):
        """Prueba la conexión con e-Vision GPS y guarda el hash si es exitoso."""
        url = "https://go.evisiongps.com/api/login"
        payload = {
            'email': self.email,
            'password': self.password
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('user_api_hash'):
                    self.write({
                        'user_api_hash': data['user_api_hash'],
                        'connection_status': 'connected'
                    })
                    self.env.cr.commit()  # Guarda en la base de datos
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Conexión Exitosa',
                            'message': 'Conexión con e-Vision GPS satisfactoria.',
                            'type': 'success',
                        },
                    }
            self.write({'connection_status': 'disconnected'})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error de Conexión',
                    'message': 'No se pudo conectar con e-Vision GPS. Verifica tus credenciales.',
                    'type': 'danger',
                },
            }
        except Exception as e:
            self.write({'connection_status': 'disconnected'})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Ocurrió un error: {str(e)}',
                    'type': 'danger',
                },
            }
