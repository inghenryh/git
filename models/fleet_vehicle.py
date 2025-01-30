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
        """Obtiene la ubicación actual del vehículo en tiempo real desde GPSWOX."""
        config = self.env['evisiongps.settings'].search([], limit=1)
        if not config or not config.user_api_hash:
            raise ValueError("El Hash de Usuario no está configurado en e-Vision GPS.")

        if not self.gps_imei:
            raise ValueError("El IMEI del GPS no está configurado para este vehículo.")

        url = "https://go.evisiongps.com/api/get_devices"
        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': config.user_api_hash,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.gps_last_location = f"{data.get('lat')}, {data.get('lng')}"
                self.gps_last_update = fields.Datetime.now()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Ubicación Actualizada',
                        'message': f'Ubicación: {self.gps_last_location}',
                        'type': 'success',
                    },
                }
            else:
                self.gps_last_location = "Error: No se pudo obtener datos"
        except Exception as e:
            self.gps_last_location = f"Error: {str(e)}"
