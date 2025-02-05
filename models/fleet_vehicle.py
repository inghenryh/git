from odoo import models, fields, api
import requests

API_HASH = "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    has_gps = fields.Boolean(string="Tiene GPS", default=False)
    gps_imei = fields.Char(string='IMEI del GPS', help="Número IMEI del dispositivo GPS.")
    gps_sim_number = fields.Char(string='Número SIM del GPS')
    gps_online_status = fields.Selection([
        ('online', 'En línea'),
        ('offline', 'Desconectado'),
    ], string='Estado del GPS', readonly=True, default='offline')
    gps_last_location = fields.Char(string='Última Ubicación', readonly=True)
    gps_last_update = fields.Datetime(string='Última Actualización', readonly=True)

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_get_location(self):
        """Obtiene la ubicación actual del vehículo en tiempo real."""
        if not self.gps_imei:
            return self._show_notification("Error", "El IMEI del GPS no está configurado.", "danger")

        url = "https://go.evisiongps.com/api/get_devices"
        params = {'imei': self.gps_imei, 'lang': 'en', 'user_api_hash': API_HASH}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.gps_last_location = f"{data.get('lat')}, {data.get('lng')}"
                self.gps_last_update = fields.Datetime.now()
                return self._show_notification("Ubicación Actualizada", f"Ubicación: {self.gps_last_location}", "success")
            else:
                return self._show_notification("Error", "No se pudo obtener datos del GPS.", "danger")
        except Exception as e:
            return self._show_notification("Error", f"Ocurrió un error: {str(e)}", "danger")

    def action_sync_gps(self):
        """Sincroniza la existencia del GPS en GPSWOX."""
        if not self.gps_imei:
            return self._show_notification("Error", "El IMEI del GPS no está configurado.", "danger")

        url = "https://go.evisiongps.com/api/get_devices"
        params = {'imei': self.gps_imei, 'lang': 'en', 'user_api_hash': API_HASH}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('imei'):
                    self.gps_online_status = 'online'
                    return self._show_notification("GPS Encontrado", f"El IMEI {self.gps_imei} está registrado en GPSWOX.", "success")
            self.gps_online_status = 'offline'
            return self._show_notification("GPS No Encontrado", "No se encontró el IMEI en GPSWOX.", "danger")
        except Exception as e:
            self.gps_online_status = 'offline'
            return self._show_notification("Error", f"Ocurrió un error: {str(e)}", "danger")

    def _show_notification(self, title, message, notification_type):
        """Genera una notificación en Odoo."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': title, 'message': message, 'type': notification_type},
        }
