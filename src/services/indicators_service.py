#!/usr/bin/env python3
"""
Service para obtener indicadores de energía desde PI
Extrae agregados diarios y mensuales usando PIConnect.summaries()
"""

import pandas as pd
from typing import Optional, Tuple
import logging

from .tracking_it_service import TrackingITService

logger = logging.getLogger(__name__)


class IndicatorsService:
    """Servicio para obtener indicadores del footer (Energía Día/Mes)"""

    # TAG del contador de energía principal (mismo para ambas plantas)
    ENERGY_COUNTER_TAG = "CONT_AM_PRINCIPAL"

    def __init__(self, pi_data_service, config_loader=None):
        """
        Inicializar servicio de indicadores

        Args:
            pi_data_service: Instancia de PIDataService para acceso a datos
            config_loader: ConfigLoader para acceder a configuración (opcional)
        """
        self.pi_service = pi_data_service

        # Inicializar servicio IT si config disponible
        if config_loader:
            try:
                self.tracking_it_service = TrackingITService(config_loader, pi_data_service)
                logger.info("TrackingITService inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando TrackingITService: {e}")
                self.tracking_it_service = None
        else:
            self.tracking_it_service = None
            logger.warning("ConfigLoader no proporcionado, IT no disponible")

    def get_footer_indicators(self, plant: str) -> Tuple[str, str, str, str, str, str, str]:
        """
        Obtiene los 7 indicadores formateados para el footer

        Args:
            plant: Planta seleccionada ('pte1' o 'pte2')

        Returns:
            Tuple con 7 strings (energía día, energía mes, tracking, tfollow, pfollow,
            minutos >395°C, rendimiento)
        """
        try:
            # Asegurar conexión a la planta requerida
            if not self.pi_service._ensure_connected(plant):
                logger.warning(f"No se pudo conectar a planta {plant}")
                return ("--", "--", "--", "--", "--", "-- min", "--%")

            # Obtener connector de la planta
            connector = self.pi_service.connectors.get(plant.lower())
            if not connector:
                logger.warning(f"No hay connector para {plant}")
                return ("--", "--", "--", "--", "--", "-- min", "--%")

            # Calcular energía del día (desde 08:00 de hoy hasta ahora)
            energy_day = self._calculate_energy_diff(
                connector,
                self.ENERGY_COUNTER_TAG,
                start_time="t+8h",  # Hoy a las 08:00
                description="día"
            )

            # Calcular energía del mes (desde día 1 del mes a las 08:00 hasta ahora)
            from datetime import datetime
            month_start = datetime.now().replace(day=1, hour=8, minute=0, second=0)
            month_start_str = month_start.strftime("%Y-%m-%d %H:%M:%S")

            energy_month = self._calculate_energy_diff(
                connector,
                self.ENERGY_COUNTER_TAG,
                start_time=month_start_str,
                description="mes"
            )

            # Resto permanecen como placeholders (por ahora)
            return (
                energy_day,      # Energía Día
                energy_month,    # Energía Mes
                "--",            # Tracking Index
                "--",            # TFollow
                "--",            # PFollow
                "-- min",        # Minutos >395°C
                "--%"            # Rendimiento
            )

        except Exception as e:
            logger.error(f"Error obteniendo indicadores para {plant}: {e}")
            return ("--", "--", "--", "--", "--", "-- min", "--%")

    def _calculate_energy_diff(self, connector, tag: str, start_time: str, description: str) -> str:
        """
        Calcula energía como diferencia entre valor actual y valor inicial del contador

        Args:
            connector: PIConnector conectado
            tag: TAG del contador (ej: CONT_AM_PRINCIPAL)
            start_time: Tiempo inicial en formato PI (ej: "t+8h", "2026-01-25 08:00:00")
            description: Descripción para logs (ej: "día", "mes")

        Returns:
            String formateado "XXX.XX MWh" o "--" si no hay datos/inválidos
        """
        try:
            # Obtener valor actual del contador (usando recorded_value con "*" = ahora)
            valor_actual = connector.get_value_at_time(tag, "*")
            if valor_actual is None:
                logger.warning(f"No hay valor actual para {tag}")
                return "--"

            # Obtener valor al inicio del período
            valor_inicio = connector.get_value_at_time(tag, start_time)
            if valor_inicio is None:
                logger.warning(f"No hay valor inicial para {tag} en {start_time}")
                return "--"

            # Calcular diferencia (contador en kWh)
            energia_kwh = valor_actual - valor_inicio

            # Validar que sea positivo
            if energia_kwh < 0:
                logger.warning(f"Energía negativa calculada para {description}: {energia_kwh:.2f} kWh. "
                             f"Podría indicar reinicio de contador en PI.")
                return "--"

            # Convertir kWh a MWh
            energia_mwh = energia_kwh / 1_000

            logger.debug(f"Energía {description}: {energia_mwh:.2f} MWh "
                        f"(contador: {valor_actual:.0f} - {valor_inicio:.0f} kWh)")

            return f"{energia_mwh:.2f} MWh"

        except Exception as e:
            logger.error(f"Error calculando energía {description}: {e}")
            return "--"
