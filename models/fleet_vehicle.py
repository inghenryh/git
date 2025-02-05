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

    def action_get_location(self):
        """Obtiene la ubicación actual del vehículo en tiempo real desde GPSWOX y la muestra en un mapa."""
        if not self.gps_imei:
            raise ValueError("El IMEI del GPS no está configurado para este vehículo.")

        url = "https://go.evisiongps.com/api/get_devices"
        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                lat, lon = data.get('lat'), data.get('lng')
                if lat and lon:
                    self.gps_last_location = f"{lat}, {lon}"
                    self.gps_last_update = fields.Datetime.now()
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Ubicación en Mapa',
                        'res_model': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_latitude': lat,
                            'default_longitude': lon,
                        },
                        'view_id': self.env.ref('evisiongps-odoo.view_gps_map').id,
                    }
                else:
                    raise ValueError("No se pudo obtener la ubicación del GPS.")
            else:
                raise ValueError("Error en la API: No se pudo obtener la ubicación.")
        except Exception as e:
            raise ValueError(f"Error: {str(e)}")
