from odoo import models, fields, api
import requests


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    # Campos adicionales para la integración GPS
    gps_imei = fields.Char(
        string='IMEI del GPS', 
        help="El número IMEI único del dispositivo GPS."
    )
    gps_sim_number = fields.Char(
        string='Número SIM del GPS', 
        help="El número SIM asociado al GPS."
    )
    gps_online_status = fields.Selection([
        ('online', 'En línea'),
        ('offline', 'Desconectado'),
    ], string='Estado del GPS', readonly=True, default='offline', 
       help="Estado del dispositivo GPS.")
    
    gps_last_location = fields.Char(
        string='Última Ubicación (Lat, Lon)', 
        readonly=True, 
        help="Última ubicación conocida del vehículo en formato 'latitud, longitud'."
    )

    gps_last_update = fields.Datetime(
        string='Última Actualización', 
        readonly=True, 
        help="Fecha y hora de la última actualización de ubicación."
    )

    # Método para actualizar el estado GPS de un vehículo
    def update_gps_status(self):
        """Consulta el estado del vehículo en e-Vision GPS y actualiza los campos correspondientes."""
        # Obtener la configuración de e-Vision GPS
        config = self.env['evisiongps.settings'].search([], limit=1)
        if not config or not config.user_api_hash:
            raise ValueError("El Hash de Usuario no está configurado en las opciones de e-Vision GPS.")

        # Llamada a la API para cada vehículo
        for vehicle in self:
            if vehicle.gps_imei:
                url = "https://go.evisiongps.com/api/get_devices"
                params = {
                    'imei': vehicle.gps_imei,
                    'lang': 'en',
                    'user_api_hash': config.user_api_hash,
                }
                try:
                    # Realiza la solicitud a la API
                    response = requests.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # Actualiza los campos con los datos obtenidos
                        vehicle.gps_online_status = 'online' if data.get('online') else 'offline'
                        if data.get('lat') and data.get('lng'):
                            vehicle.gps_last_location = f"{data.get('lat')}, {data.get('lng')}"
                        vehicle.gps_last_update = fields.Datetime.now()
                    else:
                        # Manejo de errores HTTP
                        vehicle.gps_online_status = 'offline'
                        vehicle.gps_last_location = "Error: No se pudo obtener datos"
                except Exception as e:
                    # Manejo de errores en la solicitud
                    vehicle.gps_online_status = 'offline'
                    vehicle.gps_last_location = f"Error: {str(e)}"
