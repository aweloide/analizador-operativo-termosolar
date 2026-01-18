#!/usr/bin/env python3
"""
Cargador de Configuración
Lee y proporciona acceso a la configuración desde config.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Carga y gestiona la configuración desde config.yaml"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializar el cargador de configuración

        Args:
            config_path: Ruta al archivo config.yaml
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"Configuración cargada desde: {self.config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Carga el archivo YAML

        Returns:
            Dict con la configuración
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if config is None:
                raise ValueError("Archivo de configuración vacío")

            logger.info("Configuración cargada exitosamente")
            return config

        except yaml.YAMLError as e:
            logger.error(f"Error parseando YAML: {str(e)}")
            raise

    def get_pi_server(self, plant: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene configuración de servidor PI para una planta

        Args:
            plant: 'pte1' o 'pte2'

        Returns:
            Dict con configuración del servidor
        """
        servers = self.config.get('pi_servers', {})
        return servers.get(plant.lower())

    def get_metric(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene configuración de una métrica

        Args:
            metric_name: Nombre de la métrica (ej: 'electrical_power_net')

        Returns:
            Dict con configuración de la métrica
        """
        metrics = self.config.get('metrics', {})
        return metrics.get(metric_name)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene todas las métricas configuradas

        Returns:
            Dict {metric_name: metric_config}
        """
        return self.config.get('metrics', {})

    def get_realtime_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene solo métricas configuradas para tiempo real

        Returns:
            Dict {metric_name: metric_config} solo con realtime=true
        """
        all_metrics = self.get_all_metrics()
        return {
            k: v for k, v in all_metrics.items()
            if v.get('realtime', False)
        }

    def get_historical_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene solo métricas configuradas para histórico

        Returns:
            Dict {metric_name: metric_config} solo con historical=true
        """
        all_metrics = self.get_all_metrics()
        return {
            k: v for k, v in all_metrics.items()
            if v.get('historical', False)
        }

    def get_tag_for_metric(self, metric_name: str, plant: str) -> Optional[str]:
        """
        Obtiene el tag PI específico para una métrica y planta

        Args:
            metric_name: Nombre de la métrica
            plant: 'pte1' o 'pte2'

        Returns:
            Tag PI (ej: "13WSH10CT999A.Out") o None
        """
        metric = self.get_metric(metric_name)
        if not metric:
            logger.warning(f"Métrica no encontrada: {metric_name}")
            return None

        tags = metric.get('tags', {})
        tag = tags.get(plant.lower())

        if tag and tag.startswith('PTE') or tag.startswith('13'):
            # Es un tag válido, no un placeholder
            return tag

        logger.warning(f"Tag no configurado para {metric_name}/{plant}")
        return None

    def get_update_interval(self, interval_type: str) -> int:
        """
        Obtiene intervalo de actualización en milisegundos

        Args:
            interval_type: 'realtime', 'historical_recent' o 'historical_long'

        Returns:
            Intervalo en milisegundos
        """
        intervals = self.config.get('update_intervals', {})
        interval_config = intervals.get(interval_type, {})
        interval_value = interval_config.get('interval_ms', 5000)

        # Debug logging
        logger.debug(f"get_update_interval('{interval_type}')")
        logger.debug(f"  intervals keys: {list(intervals.keys())}")
        logger.debug(f"  interval_config: {interval_config}")
        logger.debug(f"  interval_value: {interval_value}")

        return interval_value

    def is_interval_enabled(self, interval_type: str) -> bool:
        """
        Verifica si un intervalo está habilitado

        Args:
            interval_type: Tipo de intervalo

        Returns:
            bool
        """
        intervals = self.config.get('update_intervals', {})
        interval_config = intervals.get(interval_type, {})
        return interval_config.get('enabled', False)

    def get_cache_ttl(self, data_type: str) -> int:
        """
        Obtiene TTL (Time To Live) de caché en segundos

        Args:
            data_type: Tipo de dato ('snapshot', 'historical_1h', 'historical_24h', etc)

        Returns:
            TTL en segundos
        """
        cache = self.config.get('cache', {})
        key = f'{data_type}_ttl'
        return cache.get(key, 300)

    def get_app_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración de la aplicación

        Returns:
            Dict con config de la app
        """
        return self.config.get('app', {})

    def get_app_title(self) -> str:
        """Obtiene título de la aplicación"""
        app_config = self.get_app_config()
        return app_config.get('title', 'Thermosolar Dashboard')

    def get_app_debug(self) -> bool:
        """Obtiene modo debug"""
        app_config = self.get_app_config()
        return app_config.get('debug', False)

    def get_app_host(self) -> str:
        """Obtiene host de la aplicación"""
        app_config = self.get_app_config()
        return app_config.get('host', '127.0.0.1')

    def get_app_port(self) -> int:
        """Obtiene puerto de la aplicación"""
        app_config = self.get_app_config()
        return app_config.get('port', 8050)

    def get_data_limits(self) -> Dict[str, Any]:
        """Obtiene límites de datos"""
        return self.config.get('data_limits', {})

    def get_max_historical_points(self) -> int:
        """Obtiene máximo de puntos históricos a retornar"""
        limits = self.get_data_limits()
        return limits.get('max_historical_points', 10000)

    def get_aggregation_threshold(self) -> int:
        """Obtiene threshold para agregar datos"""
        limits = self.get_data_limits()
        return limits.get('aggregation_threshold', 5000)

    def get_timeout_seconds(self) -> int:
        """Obtiene timeout para consultas a PI"""
        limits = self.get_data_limits()
        return limits.get('timeout_seconds', 10)

    def get_chart_config(self) -> Dict[str, Any]:
        """Obtiene configuración de gráficos"""
        return self.config.get('charts', {})

    def get_all_plants(self) -> List[str]:
        """
        Obtiene lista de plantas configuradas

        Returns:
            Lista ['pte1', 'pte2']
        """
        servers = self.config.get('pi_servers', {})
        return list(servers.keys())

    def validate_config(self) -> bool:
        """
        Valida que la configuración sea válida

        Returns:
            bool: True si es válida
        """
        # Verificar secciones obligatorias
        required_sections = ['pi_servers', 'update_intervals', 'cache', 'app']

        # Secciones opcionales (puede usar schematic_elements o metrics)
        optional_sections = ['metrics', 'schematic_elements']

        for section in required_sections:
            if section not in self.config:
                logger.error(f"Sección faltante en configuración: {section}")
                return False

        # Verificar que al menos una de las secciones opcionales exista
        has_optional = any(section in self.config for section in optional_sections)
        if not has_optional:
            logger.error(f"Se requiere al menos una de estas secciones: {optional_sections}")
            return False

        # Verificar que haya al menos una planta configurada
        if not self.get_all_plants():
            logger.error("No hay plantas configuradas en pi_servers")
            return False

        logger.info("Configuración validada correctamente")
        return True

    def __repr__(self) -> str:
        """Representación en string"""
        plants = self.get_all_plants()
        metrics = len(self.get_all_metrics())
        return f"ConfigLoader(plants={plants}, metrics={metrics})"
