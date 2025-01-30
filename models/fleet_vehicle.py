from odoo import models, fields, api
import requests

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    has_gps = fields.Boolean(string="Tiene GPS", default=False, help="Activar si el vehículo tiene un dispositivo GPS.")
    gps_imei = fields.Char(string='IMEI del GPS', help="El número IMEI único del dispositivo GPS.")
    gps_sim_number = fields.Char(string='Número SIM del GPS', help="El número SIM asociado al GPS.")
    gps_online_status = fields.Selection([
        ('online', 'En línea'),
        ('offline', 'Desconectado'),
    ], string='Estado del GPS', readonly=True, default='offline', help="Estado del dispositivo GPS.")
    gps_last_location = fields.Char(string='Última Ubicación (Lat, Lon)', readonly=True, help="Última ubicación conocida del GPS.")
    gps_last_update = fields.Datetime(string='Última Actualización', readonly=True, help="Fecha y hora de la última actualización del GPS.")

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_sync_gps(self):
        """Busca el GPS en e-Vision GPS y lo crea si no existe."""
        config = self.env['evisiongps.settings'].search([], limit=1)
        if not config or not config.user_api_hash:
            raise ValueError("El Hash de Usuario no está configurado en e-Vision GPS.")

        if not self.gps_imei:
            raise ValueError("El IMEI del GPS no está configurado para este vehículo.")

        url_get = "https://go.evisiongps.com/api/get_devices"
        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': config.user_api_hash,
        }

        try:
            # Buscar el dispositivo en e-Vision GPS
            response = requests.get(url_get, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Si la respuesta es una lista, tomamos el primer elemento
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]

                if isinstance(data, dict) and 'imei' in data:
                    self.gps_online_status = 'online'
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'GPS Encontrado',
                            'message': f'El IMEI {self.gps_imei} está registrado en e-Vision GPS.',
                            'type': 'success',
                        },
                    }

            # Si el GPS no está registrado, crearlo
            url_create = "https://go.evisiongps.com/api/add_device"
            payload = {
                'imei': self.gps_imei,
                'name': self.name or f"Vehículo {self.id}",
                'sim_number': self.gps_sim_number or '',
                'user_api_hash': config.user_api_hash,
            }

            response_create = requests.post(url_create, json=payload, timeout=10)

            if response_create.status_code == 200:
                self.gps_online_status = 'online'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'GPS Registrado',
                        'message': f'El GPS con IMEI {self.gps_imei} ha sido registrado en e-Vision GPS.',
                        'type': 'success',
                    },
                }
            else:
                self.gps_online_status = 'offline'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error al Crear GPS',
                        'message': 'No se pudo registrar el GPS en e-Vision GPS.',
                        'type': 'danger',
                    },
                }
        except Exception as e:
            self.gps_online_status = 'offline'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Ocurrió un error: {str(e)}',
                    'type': 'danger',
                },
            }
