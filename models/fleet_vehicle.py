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
    gps_speed = fields.Float(string='Velocidad (km/h)', readonly=True, help="Velocidad actual del vehículo en km/h.")
    gps_device_id = fields.Char(string='ID del Dispositivo', readonly=True, help="ID del dispositivo en GPSWOX.")

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_sync_gps(self):
        """Sincroniza la información del GPS desde GPSWOX y actualiza los datos del vehículo."""
        if not self.gps_imei:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Debe ingresar la IMEI del GPS antes de sincronizar.',
                    'type': 'danger',
                },
            }

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
                device = data[0]  # Tomamos el primer dispositivo en la lista

                self.gps_device_id = device.get("id", "N/A")
                self.gps_online_status = "online" if device.get("online") == "online" else "offline"
                lat, lon = device.get("lat"), device.get("lng")
                self.gps_last_location = f"{lat}, {lon}" if lat and lon else "No disponible"
                self.gps_speed = device.get("speed", 0)
                self.gps_last_update = fields.Datetime.now()

                google_maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "No disponible"

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sincronización Exitosa',
                        'message': (
                            f'📡 Estado: {self.gps_online_status}\n'
                            f'📍 <a href="{google_maps_link}" target="_blank">Última ubicación</a>\n'
                            f'🚗 Velocidad: {self.gps_speed} km/h\n'
                            f'🆔 ID del dispositivo: {self.gps_device_id}\n'
                            f'🕒 Última actualización: {self.gps_last_update.strftime("%d-%m-%Y %H:%M:%S")}'
                        ),
                        'type': 'success',
                    },
                }

            # Si no existe, intentamos crearlo
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
