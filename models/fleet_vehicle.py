from odoo import models, fields, api
import requests
import json

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    has_gps = fields.Boolean(string="Tiene GPS", default=False, help="Activar si el vehículo tiene un GPS.")
    gps_imei = fields.Char(string='IMEI del GPS', help="Número IMEI del GPS.")
    gps_sim_number = fields.Char(string='Número SIM del GPS', help="Número SIM asociado al GPS.")
    gps_online_status = fields.Selection([
        ('online', 'En línea'),
        ('offline', 'Desconectado'),
    ], string='Estado del GPS', readonly=True, default='offline')
    gps_last_location = fields.Char(string='Última Ubicación (Lat, Lon)', readonly=True)
    gps_last_update = fields.Datetime(string='Última Actualización', readonly=True)

    @api.onchange('has_gps')
    def _onchange_has_gps(self):
        """Habilita/deshabilita los campos IMEI y SIM al activar o desactivar el GPS."""
        if not self.has_gps:
            self.gps_imei = False
            self.gps_sim_number = False

    def action_get_location(self):
        """Obtiene la ubicación actual desde GPSWOX y la muestra en un mapa emergente."""
        if not self.gps_imei:
            return self._notify("Error", "Debe ingresar la IMEI del GPS.", "danger")

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
                data = data[0]

            if isinstance(data, dict) and 'lat' in data and 'lng' in data:
                lat, lon = data.get('lat'), data.get('lng')
                self.gps_last_location = f"{lat}, {lon}"
                self.gps_last_update = fields.Datetime.now()

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ubicación del Vehículo',
                    'res_model': 'fleet.vehicle',
                    'view_mode': 'form',
                    'views': [(self.env.ref('evisiongps-odoo.view_fleet_vehicle_map').id, 'form')],
                    'target': 'new',
                    'context': {'default_lat': lat, 'default_lon': lon}
                }
            else:
                raise ValueError("No se pudo obtener datos de ubicación.")

        except Exception as e:
            return self._notify("Error", f"Ocurrió un error: {str(e)}", "danger")

    def action_sync_gps(self):
        """Sincroniza el vehículo con GPSWOX. Si no existe, lo crea."""
        if not self.gps_imei:
            return self._notify("Error", "Debe ingresar la IMEI del GPS antes de sincronizar.", "danger")

        url_get = "https://go.evisiongps.com/api/get_devices"
        url_create = "https://go.evisiongps.com/api/add_device"

        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
        }

        try:
            response = requests.get(url_get, params=params, timeout=10)
            data = response.json()

            if isinstance(data, list) and any(d.get('imei') == self.gps_imei for d in data):
                return self._notify("Sincronización", "El GPS ya está registrado en GPSWOX.", "success")

            payload = {
                'imei': self.gps_imei,
                'name': self.display_name,
                'icon_id': 1,
                'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
            }
            create_response = requests.post(url_create, json=payload, timeout=10)

            if create_response.status_code == 200:
                return self._notify("Sincronización Exitosa", "El GPS ha sido registrado en GPSWOX.", "success")
            else:
                raise ValueError("No se pudo crear el GPS en GPSWOX.")

        except Exception as e:
            return self._notify("Error de Sincronización", f"Ocurrió un error: {str(e)}", "danger")

    def _notify(self, title, message, notif_type):
        """Método para mostrar notificaciones al usuario."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notif_type,
            },
        }
