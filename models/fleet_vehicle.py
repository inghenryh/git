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
    gps_last_location = fields.Char(string='Última Ubicación', readonly=True, help="Última ubicación conocida del GPS.")
    gps_last_update = fields.Datetime(string='Última Actualización', readonly=True, help="Fecha y hora de la última actualización del GPS.")
    gps_speed = fields.Float(string='Velocidad (km/h)', readonly=True, help="Velocidad actual del vehículo en km/h.")
    gps_device_id = fields.Char(string='ID del Dispositivo', readonly=True, help="ID del dispositivo en GPSWOX.")

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_get_location(self):
        """Obtiene la ubicación actual del vehículo y la muestra en un mapa en Odoo."""
        if not self.gps_imei:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Debe ingresar la IMEI del GPS antes de obtener la ubicación.',
                    'type': 'danger',
                },
            }

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
                device = data[0]
                lat, lon = device.get("lat"), device.get("lng")
                self.gps_last_location = f"{lat}, {lon}" if lat and lon else "No disponible"
                self.gps_speed = device.get("speed", 0)
                self.gps_last_update = fields.Datetime.now()

                google_maps_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "No disponible"

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ubicación en Mapa',
                    'res_model': 'fleet.vehicle',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_gps_last_location': self.gps_last_location,
                        'default_google_maps_link': google_maps_link
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
