#!/usr/bin/env python3
"""
Servicio de Datos PI
Proporciona API unificada para acceder a datos de múltiples plantas
Gestiona conexiones a PI
"""

from typing import Dict, Optional, Tuple, List
import pandas as pd
from datetime import datetime
import logging

from .pi_connector import PIConnector
from ..utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class PIDataService:
    """
    Servicio de alto nivel para gestionar datos de múltiples plantas
    Proporciona API unificada para callbacks de Dash
    """

    def __init__(self, config: ConfigLoader):
        """
        Inicializar el servicio de datos PI

        Args:
            config: Instancia de ConfigLoader
        """
        self.config = config
        self.connectors: Dict[str, PIConnector] = {}
        self.last_error: Optional[str] = None
        self.active_plant: Optional[str] = None  # Rastrear qué planta tiene conexión activa
        self.plant_configs: Dict[str, dict] = {}  # Almacenar configs sin conectar aún

        logger.info("Inicializando PIDataService...")
        self._load_plant_configs()
        logger.info("PIDataService inicializado (conexiones perezosas)")

    def _load_plant_configs(self) -> None:
        """
        Carga configuraciones de plantas sin conectar aún
        Las conexiones se crean bajo demanda (lazy loading)
        Esto evita el problema de múltiples conexiones simultáneas a PIconnect
        """
        plants = self.config.get_all_plants()

        for plant in plants:
            server_config = self.config.get_pi_server(plant)
            if not server_config:
                logger.warning(f"No hay configuración para planta: {plant}")
                continue

            self.plant_configs[plant] = server_config
            logger.info(f"Configuración cargada para: {plant.upper()} ({server_config.get('host')})")

    def _ensure_connected(self, target_plant: str) -> bool:
        """
        Asegura que estamos conectados a la planta requerida
        Si hay otra conexión activa, la cierra primero

        Args:
            target_plant: Planta a la que conectarse ('pte1' o 'pte2')

        Returns:
            bool: True si la conexión es exitosa
        """
        target_plant = target_plant.lower()

        # Si ya estamos conectados a la planta correcta, retornar True
        if self.active_plant == target_plant:
            connector = self.connectors.get(target_plant)
            if connector and connector.is_connected():
                logger.debug(f"Ya conectado a {target_plant.upper()}")
                return True

        # Si hay otra planta conectada, desconectarla primero
        if self.active_plant and self.active_plant != target_plant:
            logger.info(f"Desconectando de {self.active_plant.upper()} para conectar a {target_plant.upper()}")
            old_connector = self.connectors.get(self.active_plant)
            if old_connector:
                old_connector.close()
                if self.active_plant in self.connectors:
                    del self.connectors[self.active_plant]
            self.active_plant = None

        # Conectar a la planta requerida si aún no existe el conector
        if target_plant not in self.connectors:
            logger.info(f"Conectando a {target_plant.upper()}...")
            server_config = self.plant_configs.get(target_plant)
            if not server_config:
                logger.error(f"No hay configuración para: {target_plant}")
                self.last_error = f"No hay configuración para: {target_plant}"
                return False

            try:
                connector = PIConnector(server_name=server_config.get('host'))
                if connector.connect():
                    self.connectors[target_plant] = connector
                    self.active_plant = target_plant
                    logger.info(f"[OK] Conectado exitosamente a {target_plant.upper()}")
                    return True
                else:
                    logger.error(f"[ERROR] No se pudo conectar a {target_plant.upper()}")
                    self.last_error = f"No se pudo conectar a {target_plant.upper()}"
                    return False

            except Exception as e:
                logger.error(f"Excepción conectando a {target_plant.upper()}: {str(e)}")
                self.last_error = f"Excepción conectando a {target_plant.upper()}: {str(e)}"
                return False

        return True

    def is_plant_connected(self, plant: str) -> bool:
        """
        Verifica si una planta está conectada
        Intenta conectar bajo demanda si aún no está conectada

        Args:
            plant: 'pte1' o 'pte2'

        Returns:
            bool: True si está conectada o se puede conectar
        """
        plant = plant.lower()

        # Si ya tiene conector y está conectado, retornar True
        connector = self.connectors.get(plant)
        if connector and connector.is_connected():
            return True

        # Intentar conectar bajo demanda
        return self._ensure_connected(plant)

    def get_all_plants_status(self) -> Dict[str, bool]:
        """
        Obtiene estado de conexión de todas las plantas

        Returns:
            Dict {plant: connected_bool}
        """
        return {
            plant: self.is_plant_connected(plant)
            for plant in self.config.get_all_plants()
        }

    def get_snapshot(
        self,
        metric_name: str,
        plant: str
    ) -> Optional[Dict]:
        """
        Obtiene valor actual de una métrica para una planta
        Maneja automáticamente el cambio de conexión entre plantas

        Args:
            metric_name: Nombre de la métrica (ej: 'electrical_power_net')
            plant: 'pte1' o 'pte2'

        Returns:
            Dict con {'value': float, 'timestamp': datetime, 'unit': str, 'name': str}
        """
        plant = plant.lower()

        # Obtener tag desde configuración
        tag = self.config.get_tag_for_metric(metric_name, plant)
        if not tag:
            logger.warning(f"Tag no configurado para: {metric_name}/{plant}")
            self.last_error = f"Tag no configurado para: {metric_name}/{plant}"
            return None

        # Asegurar conexión a la planta correcta
        if not self._ensure_connected(plant):
            logger.error(f"No se pudo conectar a {plant} para obtener snapshot")
            self.last_error = f"No se pudo conectar a {plant} para obtener snapshot"
            return None

        # Obtener snapshot desde PI
        connector = self.connectors.get(plant)
        if not connector:
            logger.error(f"Conector no disponible para: {plant}")
            self.last_error = f"Conector no disponible para: {plant}"
            return None

        snapshot = connector.get_snapshot(tag)
        if snapshot:
            # Obtener información adicional de la métrica
            metric_config = self.config.get_metric(metric_name)
            result = {
                'value': snapshot['value'],
                'timestamp': snapshot['timestamp'],
                'unit': metric_config.get('unit', ''),
                'name': metric_config.get('name', metric_name),
                'metric_id': metric_name,
                'plant': plant
            }
            return result

        self.last_error = f"No se pudo obtener snapshot para: {metric_name}/{plant}"
        return None

    def get_all_realtime_snapshots(self, plant: str) -> Dict[str, Dict]:
        """
        Obtiene todos los snapshots configurados para tiempo real

        Args:
            plant: 'pte1' o 'pte2'

        Returns:
            Dict {metric_name: snapshot_data}
        """
        plant = plant.lower()
        metrics = self.config.get_realtime_metrics()

        if not metrics:
            logger.warning(f"No hay métricas configuradas para tiempo real en plant={plant}")
            return {}

        results = {}

        for metric_name in metrics.keys():
            snapshot = self.get_snapshot(metric_name, plant)
            if snapshot:
                results[metric_name] = snapshot
            else:
                logger.debug(f"No se pudo obtener snapshot para: {metric_name}/{plant}")

        return results

    def get_historical_data(
        self,
        metric_name: str,
        plant: str,
        start_time: str = "*-24h",
        end_time: str = "*"
    ) -> Optional[pd.DataFrame]:
        """
        Obtiene datos históricos de una métrica
        Maneja automáticamente el cambio de conexión entre plantas

        Args:
            metric_name: Nombre de la métrica
            plant: 'pte1' o 'pte2'
            start_time: Tiempo de inicio en formato PI
            end_time: Tiempo de fin en formato PI

        Returns:
            DataFrame con columnas ['timestamp', 'value'] o None
        """
        plant = plant.lower()

        # Obtener tag desde configuración
        tag = self.config.get_tag_for_metric(metric_name, plant)
        if not tag:
            logger.warning(f"Tag no configurado para: {metric_name}/{plant}")
            self.last_error = f"Tag no configurado para: {metric_name}/{plant}"
            return None

        # Asegurar conexión a la planta correcta
        if not self._ensure_connected(plant):
            logger.error(f"No se pudo conectar a {plant} para obtener datos históricos")
            self.last_error = f"No se pudo conectar a {plant} para obtener datos históricos"
            return None

        # Obtener datos desde PI
        connector = self.connectors.get(plant)
        if not connector:
            logger.error(f"Conector no disponible para: {plant}")
            self.last_error = f"Conector no disponible para: {plant}"
            return None

        df = connector.get_point_data(tag, start=start_time, end=end_time)

        if df is not None:
            return df

        self.last_error = f"No se pudieron obtener datos históricos para: {metric_name}/{plant}"
        return None

    def get_comparison_data(
        self,
        metric_name: str,
        start_time: str = "*-24h",
        end_time: str = "*"
    ) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Obtiene datos de ambas plantas para comparación

        Args:
            metric_name: Métrica a comparar
            start_time: Inicio
            end_time: Fin

        Returns:
            Tuple (df_pte1, df_pte2)
        """
        df_pte1 = self.get_historical_data(metric_name, 'pte1', start_time, end_time)
        df_pte2 = self.get_historical_data(metric_name, 'pte2', start_time, end_time)

        return df_pte1, df_pte2

    def get_metric_statistics(
        self,
        metric_name: str,
        plant: str,
        start_time: str = "*-24h",
        end_time: str = "*"
    ) -> Optional[Dict]:
        """
        Calcula estadísticas para una métrica

        Args:
            metric_name: Métrica
            plant: Planta
            start_time: Inicio
            end_time: Fin

        Returns:
            Dict con {'min', 'max', 'mean', 'median', 'std', 'count', 'sum'}
        """
        df = self.get_historical_data(metric_name, plant, start_time, end_time)

        if df is None or len(df) == 0:
            return None

        return {
            'count': len(df),
            'min': float(df['value'].min()),
            'max': float(df['value'].max()),
            'mean': float(df['value'].mean()),
            'median': float(df['value'].median()),
            'std': float(df['value'].std()),
            'sum': float(df['value'].sum()),
            'start_time': df['timestamp'].min(),
            'end_time': df['timestamp'].max()
        }

    def compare_plants(
        self,
        metric_name: str,
        start_time: str = "*-24h",
        end_time: str = "*"
    ) -> Optional[Dict]:
        """
        Compara una métrica entre ambas plantas

        Args:
            metric_name: Métrica a comparar
            start_time: Inicio
            end_time: Fin

        Returns:
            Dict con comparación
        """
        stats_pte1 = self.get_metric_statistics(metric_name, 'pte1', start_time, end_time)
        stats_pte2 = self.get_metric_statistics(metric_name, 'pte2', start_time, end_time)

        if not stats_pte1 or not stats_pte2:
            return None

        return {
            'pte1': stats_pte1,
            'pte2': stats_pte2,
            'difference': {
                'mean': stats_pte1['mean'] - stats_pte2['mean'],
                'min': stats_pte1['min'] - stats_pte2['min'],
                'max': stats_pte1['max'] - stats_pte2['max'],
            },
            'ratio_mean': stats_pte1['mean'] / stats_pte2['mean'] if stats_pte2['mean'] != 0 else 0,
            'ratio_max': stats_pte1['max'] / stats_pte2['max'] if stats_pte2['max'] != 0 else 0,
        }

    def get_service_status(self) -> Dict:
        """
        Obtiene estado general del servicio

        Returns:
            Dict con estado
        """
        return {
            'connected_plants': self.get_all_plants_status(),
            'last_error': self.last_error
        }

    def close(self) -> None:
        """Cierra todas las conexiones"""
        for plant, connector in self.connectors.items():
            try:
                connector.close()
                logger.info(f"Conexión cerrada para: {plant}")
            except Exception as e:
                logger.error(f"Error cerrando conexión para {plant}: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
