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
        """Obtiene la ubicación actual del vehículo en tiempo real desde GPSWOX y muestra un mapa con Leaflet."""
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
                device_data = data[0]  # Tomar el primer dispositivo encontrado
                lat, lon = device_data.get('lat'), device_data.get('lng')
                self.gps_online_status = device_data.get('online', 'offline')
                self.gps_speed = device_data.get('speed', 0)
                self.gps_last_update = fields.Datetime.now()
                self.gps_device_id = device_data.get('id')

                if lat and lon:
                    self.gps_last_location = f"{lat}, {lon}"
                    self.gps_location_link = f"https://www.google.com/maps?q={lat},{lon}"

                    return {
                        'type': 'ir.actions.act_window',
                        'name': "Ubicación en tiempo real",
                        'view_mode': 'form',
                        'target': 'new',
                        'res_model': 'fleet.vehicle',
                        'context': {
                            'default_gps_location_link': self.gps_location_link,
                            'default_gps_last_location': self.gps_last_location,
                            'default_gps_online_status': self.gps_online_status,
                            'default_gps_speed': self.gps_speed,
                            'default_gps_last_update': self.gps_last_update,
                        }
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
