#!/usr/bin/env python3
"""
PI Data Archive Connector
Adaptado para usarse en la aplicación Thermosolar Dashboard
Usa PIconnect para conectar directamente al servidor PI
"""

import PIconnect as PI
import pandas as pd
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PIConnector:
    """Conector a PI Data Archive usando PIconnect"""

    def __init__(self, server_name: Optional[str] = None):
        """
        Inicializar conector PI

        Args:
            server_name: Nombre del servidor PI (opcional)
                        Si no se proporciona, conecta al servidor por defecto
        """
        self.server = None
        self.server_name = server_name
        self.connected = False

    def connect(self) -> bool:
        """
        Conectar al servidor PI

        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            logger.info(f"Conectando al servidor PI: {self.server_name or 'default'}")

            if self.server_name:
                self.server = PI.PIServer(self.server_name)
            else:
                self.server = PI.PIServer()

            logger.info(f"Conectado a: {self.server.server_name}")
            logger.info(f"Versión: {self.server.version}")

            self.connected = True
            return True

        except Exception as e:
            logger.error(f"Error conectando a PI: {str(e)}")
            self.connected = False
            return False

    def is_connected(self) -> bool:
        """Verificar si está conectado al servidor PI"""
        return self.connected and self.server is not None

    def search_points(self, query: str = "*", limit: int = 10) -> List:
        """
        Buscar puntos en el servidor

        Args:
            query: Patrón de búsqueda (ej: "13WSH*" o "PTE1*")
            limit: Número máximo de resultados a retornar

        Returns:
            Lista de puntos encontrados
        """
        if not self.is_connected():
            logger.error("No hay conexión activa al servidor PI")
            return []

        try:
            logger.debug(f"Buscando puntos con query: '{query}'")

            resultados = self.server.search(query)
            logger.info(f"Se encontraron {len(resultados)} punto(s)")

            # Retornar solo los primeros N
            return resultados[:limit]

        except Exception as e:
            logger.error(f"Error buscando puntos: {str(e)}")
            return []

    def get_point_data(
        self,
        point_name: str,
        start: str = "*-24h",
        end: str = "*"
    ) -> Optional[pd.DataFrame]:
        """
        Obtener datos históricos de un punto

        Args:
            point_name: Nombre del punto (ej: "13WSH10CT999A.Out")
            start: Hora de inicio en formato PI (ej: "*-24h", "*-7d")
            end: Hora de fin en formato PI (ej: "*")

        Returns:
            DataFrame con columnas ['timestamp', 'value'] o None si hay error
        """
        if not self.is_connected():
            logger.error("No hay conexión activa al servidor PI")
            return None

        try:
            logger.debug(f"Obteniendo datos de: {point_name}")
            logger.debug(f"Rango: {start} a {end}")

            # Buscar el punto
            resultados = self.server.search(point_name)

            if not resultados:
                logger.warning(f"Punto no encontrado: {point_name}")
                return None

            point = resultados[0]
            logger.debug(f"Punto encontrado: {point.name}")

            # Obtener datos históricos
            # Nota: Los parámetros son posicionales, no nombrados
            valores = point.recorded_values(start, end)

            logger.info(f"Se obtuvieron {len(valores)} registros")

            # Convertir a DataFrame
            if len(valores) > 0:
                datos = []
                for timestamp, value in valores.items():
                    datos.append({
                        'timestamp': timestamp,
                        'value': float(value)
                    })

                df = pd.DataFrame(datos)
                df = df.sort_values('timestamp').reset_index(drop=True)

                return df
            else:
                logger.warning("No hay datos para el rango especificado")
                return None

        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {str(e)}")
            return None

    def get_snapshot(self, point_name: str) -> Optional[dict]:
        """
        Obtener valor actual (snapshot) de un punto

        Args:
            point_name: Nombre del punto (ej: "13WSH10CT999A.Out")

        Returns:
            Dict con {'value': float, 'timestamp': datetime} o None si hay error
        """
        if not self.is_connected():
            logger.error("No hay conexión activa al servidor PI")
            return None

        try:
            logger.debug(f"Obteniendo snapshot de: {point_name}")

            # Buscar punto
            resultados = self.server.search(point_name)

            if not resultados:
                logger.warning(f"Punto no encontrado: {point_name}")
                return None

            point = resultados[0]

            # Obtener valor actual
            snapshot = point.current_value

            if snapshot is None:
                logger.warning(f"No hay snapshot disponible para: {point_name}")
                return None

            # snapshot puede ser un float directo o un objeto PISnapshot
            # Intentar obtener timestamp del objeto, sino usar ahora
            # IMPORTANTE: No usar "if snapshot" porque 0.0 es falsy en Python
            try:
                snapshot_value = float(snapshot)
            except (ValueError, TypeError):
                logger.warning(f"No se pudo convertir snapshot a float: {snapshot} (type: {type(snapshot).__name__})")
                snapshot_value = None
            snapshot_time = None

            try:
                # Intentar acceder a timestamp si existe
                if hasattr(snapshot, 'timestamp'):
                    snapshot_time = snapshot.timestamp
                else:
                    snapshot_time = pd.Timestamp.now()
            except:
                snapshot_time = pd.Timestamp.now()

            logger.debug(f"Snapshot obtenido - Valor: {snapshot_value}, Timestamp: {snapshot_time}")

            return {
                'value': snapshot_value,
                'timestamp': snapshot_time,
                'name': point.name,
                'raw_snapshot': snapshot
            }

        except Exception as e:
            logger.error(f"Error obteniendo snapshot: {str(e)}")
            return None

    def get_point_info(self, point_name: str) -> Optional[dict]:
        """
        Obtener información sobre un punto (nombre, descripción, etc)

        Args:
            point_name: Nombre del punto

        Returns:
            Dict con información del punto o None si hay error
        """
        if not self.is_connected():
            logger.error("No hay conexión activa al servidor PI")
            return None

        try:
            resultados = self.server.search(point_name)

            if not resultados:
                logger.warning(f"Punto no encontrado: {point_name}")
                return None

            point = resultados[0]

            return {
                'name': point.name,
                'description': getattr(point, 'description', 'N/A'),
                'eng_units': getattr(point, 'eng_units', 'N/A'),
                'point_class': getattr(point, 'point_class', 'N/A')
            }

        except Exception as e:
            logger.error(f"Error obteniendo información del punto: {str(e)}")
            return None

    def get_summaries(self, point_name: str, start: str, end: str,
                      interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Obtiene agregados (TOTAL) de PI para un período especificado
        Usa TIME_WEIGHTED para integración correcta de potencia

        Args:
            point_name: Nombre del punto PI
            start: Tiempo inicial (ej: "*-1d", "2026-01-16 00:00:00")
            end: Tiempo final (ej: "*", "2026-01-17 00:00:00")
            interval: Intervalo para agregados (ej: "1d" para diario, "1mo" para mensual)

        Returns:
            DataFrame con columna 'TOTAL' con los agregados, o None si hay error
        """
        if not self.is_connected():
            logger.error("No hay conexión activa al servidor PI")
            return None

        try:
            resultados = self.server.search(point_name)

            if not resultados:
                logger.warning(f"Punto no encontrado: {point_name}")
                return None

            point = resultados[0]

            # PIConnect.summaries() retorna DataFrame con agregados
            # TIME_WEIGHTED es crucial para integración correcta de energía
            from PIconnect import PIConsts
            result = point.summaries(
                start_time=start,
                end_time=end,
                interval=interval,
                summary_types=PIConsts.SummaryType.TOTAL,
                calculation_basis=PIConsts.CalculationBasis.TIME_WEIGHTED
            )

            logger.debug(f"Agregados obtenidos para {point_name}: {len(result)} filas")
            return result

        except Exception as e:
            logger.error(f"Error obteniendo agregados para {point_name}: {str(e)}")
            return None

    def export_to_csv(self, df: pd.DataFrame, filename: str) -> bool:
        """
        Exportar DataFrame a CSV

        Args:
            df: DataFrame a exportar
            filename: Ruta del archivo destino

        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Datos exportados a: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exportando a CSV: {str(e)}")
            return False

    def close(self):
        """Cerrar la conexión con el servidor PI"""
        try:
            if self.server:
                self.server = None
                self.connected = False
                logger.info("Conexión cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión: {str(e)}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
