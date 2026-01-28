#!/usr/bin/env python3
"""
Servicio de Índice de Tracking
Ejecuta el script calculadora-indice-tracking-termosolar/calcular_it_completo.py
"""

import subprocess
import re
from pathlib import Path
from datetime import date
import logging

logger = logging.getLogger(__name__)


class TrackingITService:
    """Servicio para calcular el Índice de Tracking ejecutando el script externo"""

    def __init__(self, config_loader, pi_data_service):
        """
        Inicializa el servicio de IT

        Args:
            config_loader: ConfigLoader con path al módulo calculadora
            pi_data_service: PIDataService (no usado en esta versión, pero mantenido para compatibilidad)
        """
        self.config = config_loader
        self.pi_service = pi_data_service

        # Caché de IT por día: {fecha: {'pte1': valor_it, 'pte2': valor_it}}
        self._cache_it = {}

        # Obtener path del script calculadora
        self.calculadora_script_path = self._get_calculadora_script_path()

    def _get_calculadora_script_path(self) -> Path:
        """Obtiene el path absoluto al script calcular_it_completo.py"""
        try:
            external_modules = self.config.config.get('external_modules', {})
            calculadora_config = external_modules.get('calculadora_tracking', {})
            relative_path = calculadora_config.get('path')

            if not relative_path:
                logger.warning("Path a calculadora-tracking no configurado en config.yaml")
                return None

            # Resolver path relativo desde la raíz del analizador
            base_path = Path(__file__).parent.parent.parent  # Sube a raíz de analizador
            script_path = (base_path / relative_path / "calcular_it_completo.py").resolve()

            if not script_path.exists():
                logger.error(f"Script calculadora no existe: {script_path}")
                return None

            logger.info(f"Script calculadora resuelto: {script_path}")
            return script_path

        except Exception as e:
            logger.error(f"Error obteniendo path calculadora: {e}")
            return None

    def get_it_dia_actual(self, plant: str) -> str:
        """
        Obtiene el IT General del día actual para una planta

        Args:
            plant: 'pte1' o 'pte2'

        Returns:
            String formateado "XX.XX%" o "--" si no disponible
        """
        # Verificar que script esté disponible
        if not self.calculadora_script_path:
            logger.warning("Script de tracking no disponible")
            return "--"

        # Solo PTE1 soportado por ahora
        if plant.lower() != 'pte1':
            logger.debug(f"IT no disponible para {plant.upper()} (solo PTE1 soportado)")
            return "--"

        fecha_hoy = date.today()

        # Verificar caché
        if fecha_hoy in self._cache_it and plant in self._cache_it[fecha_hoy]:
            cached_value = self._cache_it[fecha_hoy][plant]
            logger.debug(f"IT en caché para {plant.upper()}: {cached_value}")
            return cached_value

        # Calcular IT (primera vez del día o caché vacío)
        it_valor = self._ejecutar_calculadora(plant, fecha_hoy)

        # Guardar en caché (limpiar caché de días anteriores)
        if fecha_hoy not in self._cache_it:
            self._cache_it = {fecha_hoy: {}}

        self._cache_it[fecha_hoy][plant] = it_valor

        return it_valor

    def _ejecutar_calculadora(self, plant: str, fecha: date) -> str:
        """
        Ejecuta el script calcular_it_completo.py usando subprocess

        Args:
            plant: 'pte1' o 'pte2'
            fecha: Fecha para calcular IT

        Returns:
            String formateado "XX.XX%" o "--" si error
        """
        try:
            fecha_str = fecha.isoformat()  # YYYY-MM-DD

            logger.info(f"Ejecutando calculadora IT para {fecha_str} (puede tardar ~5 minutos para 640 SCAs)...")

            # Ejecutar script con Python
            result = subprocess.run(
                ['python', str(self.calculadora_script_path), fecha_str],
                cwd=str(self.calculadora_script_path.parent),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )

            if result.returncode != 0:
                logger.error(f"Script falló con código {result.returncode}")
                logger.error(f"STDERR: {result.stderr[:500]}")  # Primeros 500 chars
                return "--"

            # Parsear salida para extraer IT General
            # Buscar línea: "  >>> IT General:        87.50% (Excel: 87.5%) <<<"
            it_value = self._parse_it_from_output(result.stdout)

            if it_value:
                logger.info(f"IT General calculado: {it_value}%")
                return f"{it_value}%"
            else:
                logger.warning("No se pudo parsear IT General de la salida del script")
                return "--"

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando calculadora IT (>10 minutos)")
            return "--"
        except Exception as e:
            logger.error(f"Error ejecutando calculadora IT para {plant}: {e}", exc_info=True)
            return "--"

    def _parse_it_from_output(self, output: str) -> str:
        """
        Parsea la salida del script para extraer el valor de IT General

        Args:
            output: Salida stdout del script

        Returns:
            String con el valor numérico (ej: "87.50") o None si no se encuentra
        """
        try:
            # Buscar línea: "  >>> IT General:        87.50% (Excel: 87.5%) <<<"
            # Patrón regex: captura el número decimal antes del primer %
            pattern = r'>>>.*?IT General:\s*(\d+\.\d+)%'
            match = re.search(pattern, output)

            if match:
                return match.group(1)

            # Fallback: buscar cualquier línea con "IT General:" y número
            pattern_fallback = r'IT General[:\s]+(\d+\.\d+)'
            match_fallback = re.search(pattern_fallback, output, re.IGNORECASE)

            if match_fallback:
                return match_fallback.group(1)

            return None

        except Exception as e:
            logger.error(f"Error parseando IT de salida: {e}")
            return None
