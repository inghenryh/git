from odoo import models, fields, api
import requests
import json

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
                data = data[0]  # Si la API devuelve una lista, tomamos el primer elemento.

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
        """Sincroniza el vehículo con GPSWOX. Si no existe, lo crea en GPSWOX."""
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
        url_create = "https://go.evisiongps.com/api/add_device"

        params = {
            'imei': self.gps_imei,
            'lang': 'en',
            'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
        }

        try:
            # Consultamos si ya existe el dispositivo
            response = requests.get(url_get, params=params, timeout=10)
            data = response.json()

            if isinstance(data, list) and any(d.get('imei') == self.gps_imei for d in data):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sincronización',
                        'message': 'El GPS ya está registrado en GPSWOX.',
                        'type': 'success',
                    },
                }

            # Si no existe, intentamos crearlo
            payload = {
                'imei': self.gps_imei,
                'name': self.display_name,
                'icon_id': 1,  # ID de icono por defecto, se puede cambiar
                'user_api_hash': "$2y$10$tS7LNxOjhnsqzNkyXKqAke4MHtGUSZE0ZEQS.M9IpDwkuOgfnABPO"
            }
            create_response = requests.post(url_create, json=payload, timeout=10)

            if create_response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Sincronización Exitosa',
                        'message': 'El GPS ha sido registrado correctamente en GPSWOX.',
                        'type': 'success',
                    },
                }
            else:
                raise ValueError("No se pudo crear el GPS en GPSWOX.")

        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error de Sincronización',
                    'message': f'Ocurrió un error: {str(e)}',
                    'type': 'danger',
                },
            }
