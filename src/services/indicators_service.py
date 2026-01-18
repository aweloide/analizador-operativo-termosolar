#!/usr/bin/env python3
"""
Service para obtener indicadores de energía desde PI
Extrae agregados diarios y mensuales usando PIConnect.summaries()
"""

import pandas as pd
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class IndicatorsService:
    """Servicio para obtener indicadores del footer (Energía Día/Mes)"""

    # TAGs de generación neta por planta
    ENERGY_TAGS = {
        "pte1": "14BAY10GH001_XE08.OUT",
        "pte2": "24BAY10GH001_XE08.OUT"
    }

    def __init__(self, pi_data_service):
        """
        Inicializar servicio de indicadores

        Args:
            pi_data_service: Instancia de PIDataService para acceso a datos
        """
        self.pi_service = pi_data_service

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
            # Obtener TAG de generación neta para la planta
            tag = self.ENERGY_TAGS.get(plant.lower())
            if not tag:
                logger.warning(f"Planta desconocida: {plant}")
                return ("--", "--", "--", "--", "--", "-- min", "--%")

            # Asegurar conexión a la planta requerida
            if not self.pi_service._ensure_connected(plant):
                logger.warning(f"No se pudo conectar a planta {plant}")
                return ("--", "--", "--", "--", "--", "-- min", "--%")

            # Obtener connector de la planta
            connector = self.pi_service.connectors.get(plant.lower())
            if not connector:
                logger.warning(f"No hay connector para {plant}")
                return ("--", "--", "--", "--", "--", "-- min", "--%")

            # Energía Día (últimas 24 horas)
            day_result = connector.get_summaries(tag, "*-1d", "*", "1d")
            energy_day = self._format_energy(day_result)

            # Energía Mes (últimos 30 días agrupados por mes)
            month_result = connector.get_summaries(tag, "*-30d", "*", "1mo")
            energy_month = self._format_energy(month_result)

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

    def _format_energy(self, result: Optional[pd.DataFrame]) -> str:
        """
        Extrae y formatea valor de energía desde DataFrame de agregados

        Args:
            result: DataFrame retornado por get_summaries() con columna 'TOTAL'

        Returns:
            String formateado "XXX.XX MWh" o "--" si no hay datos/inválidos
        """
        try:
            if result is not None and not result.empty:
                # Último valor en el DataFrame (hoy para diario, mes actual para mensual)
                value = result['TOTAL'].iloc[-1]

                # Convertir a float si es necesario
                if pd.notna(value):
                    value_float = float(value)

                    # Validar que el valor sea positivo (energía no puede ser negativa)
                    # Si es negativo, indica un problema con el agregado en PI
                    if value_float < 0:
                        logger.warning(f"Valor negativo de energía detectado: {value_float:.2f} MWh. "
                                     f"Podría indicar reinicio de contador en PI.")
                        return "--"

                    return f"{value_float:.2f} MWh"

            logger.debug("DataFrame vacío o None para energy")
            return "--"

        except Exception as e:
            logger.warning(f"Error formateando energía: {e}")
            return "--"
