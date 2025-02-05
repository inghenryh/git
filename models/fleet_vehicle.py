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
    gps_device_id = fields.Char(string="ID del Dispositivo", readonly=True, help="ID único del dispositivo en GPSWOX.")
    gps_speed = fields.Float(string="Velocidad (km/h)", readonly=True, help="Velocidad actual del vehículo en km/h.")
    gps_location_link = fields.Char(string="Ubicación en Google Maps", readonly=True, help="Enlace a Google Maps con la ubicación actual.")

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_get_location(self):
        """Obtiene la ubicación actual del vehículo en tiempo real desde GPSWOX."""
        if not self.gps_imei:
            raise ValueError("Debe ingresar la IMEI del GPS antes de obtener la ubicación.")

        url = "https://go.evisiongps.com/api/get_devices"
        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if isinstance(data, list) and data:
                device_data = data[0]
                lat, lon = device_data.get('lat'), device_data.get('lng')
                self.gps_online_status = device_data.get('online', 'offline')
                self.gps_speed = device_data.get('speed', 0)
                self.gps_last_update = fields.Datetime.now()
                self.gps_device_id = device_data.get('id')

                if lat and lon:
                    self.gps_last_location = f"{lat}, {lon}"
                    self.gps_location_link = f"https://www.google.com/maps?q={lat},{lon}"

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Ubicación Actualizada',
                            'message': f'Ubicación: {self.gps_last_location} - Velocidad: {self.gps_speed} km/h',
                            'type': 'success',
                        },
                    }

            raise ValueError("No se pudo obtener datos de ubicación.")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Ocurrió un error: {str(e)}',
                    'type': 'danger',
                },
            }

    def action_sync_gps(self):
        """Verifica si el vehículo existe en GPSWOX y, si no, lo crea."""
        if not self.gps_imei:
            raise ValueError("Debe ingresar la IMEI del GPS antes de sincronizar.")

        url_get = "https://go.evisiongps.com/api/get_devices"
        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
        }

        try:
            response = requests.get(url_get, params=params, timeout=10)
            data = response.json()

            if isinstance(data, list) and data:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sincronización Exitosa',
                        'message': f'El vehículo con IMEI {self.gps_imei} ya está registrado.',
                        'type': 'success',
                    },
                }

            # Si no existe, lo creamos
            url_create = "https://go.evisiongps.com/api/add_device"
            payload = {
                'imei': self.gps_imei,
                'name': self.name,
                'lang': 'en',
                'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
            }
            response_create = requests.post(url_create, json=payload, timeout=10)
            if response_create.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'GPS Creado',
                        'message': f'El dispositivo con IMEI {self.gps_imei} ha sido registrado en GPSWOX.',
                        'type': 'success',
                    },
                }
            else:
                raise ValueError("No se pudo registrar el dispositivo en GPSWOX.")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Ocurrió un error: {str(e)}',
                    'type': 'danger',
                },
            }
