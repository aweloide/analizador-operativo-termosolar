#!/usr/bin/env python3
"""
Script de Prueba: Conectividad con Servidores PI
Verifica que los servicios PI están configurados y accesibles
"""

import logging
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config_loader import ConfigLoader
from src.core.pi_data_service import PIDataService


def test_config_loading():
    """Prueba carga de configuración"""
    print("\n" + "="*70)
    print("PRUEBA 1: CARGA DE CONFIGURACIÓN")
    print("="*70)

    try:
        config = ConfigLoader('config.yaml')
        logger.info("✓ Configuración cargada correctamente")

        # Validar configuración
        if config.validate_config():
            logger.info("✓ Configuración es válida")
        else:
            logger.error("✗ Configuración inválida")
            return False

        # Mostrar información de configuración
        print("\nInformación de Configuración:")
        print(f"  - Plantas configuradas: {config.get_all_plants()}")
        print(f"  - Métricas configuradas: {len(config.get_all_metrics())}")
        print(f"  - Métricas en tiempo real: {len(config.get_realtime_metrics())}")

        for plant in config.get_all_plants():
            server_config = config.get_pi_server(plant)
            print(f"\n  {plant.upper()}:")
            print(f"    - Host: {server_config.get('host')}")
            print(f"    - Nombre: {server_config.get('name')}")

        return True

    except Exception as e:
        logger.error(f"✗ Error cargando configuración: {str(e)}")
        return False


def test_pi_connectivity():
    """Prueba conectividad con servidores PI"""
    print("\n" + "="*70)
    print("PRUEBA 2: CONECTIVIDAD CON SERVIDORES PI")
    print("="*70)

    try:
        config = ConfigLoader('config.yaml')
        service = PIDataService(config)

        print("\nEstado de Conexión:")
        status = service.get_all_plants_status()

        all_connected = True
        for plant, connected in status.items():
            status_str = "✓ CONECTADO" if connected else "✗ DESCONECTADO"
            print(f"  {plant.upper()}: {status_str}")
            if not connected:
                all_connected = False

        if all_connected:
            logger.info("✓ Todos los servidores PI están conectados")
        else:
            logger.warning("✗ Algunos servidores PI no están disponibles")
            if service.last_error:
                print(f"\nÚltimo error: {service.last_error}")

        return all_connected

    except Exception as e:
        logger.error(f"✗ Error en prueba de conectividad: {str(e)}")
        return False


def test_snapshot_retrieval():
    """Prueba obtención de snapshots"""
    print("\n" + "="*70)
    print("PRUEBA 3: OBTENCIÓN DE SNAPSHOTS (VALORES ACTUALES)")
    print("="*70)

    try:
        config = ConfigLoader('config.yaml')
        service = PIDataService(config)

        # Obtener métricas configuradas para tiempo real
        realtime_metrics = config.get_realtime_metrics()

        if not realtime_metrics:
            logger.warning("✗ No hay métricas configuradas para tiempo real")
            return False

        print(f"\nIntentando obtener {len(realtime_metrics)} métrica(s) en tiempo real...")

        success_count = 0
        for metric_name, metric_config in realtime_metrics.items():
            print(f"\n  Métrica: {metric_config.get('name')}")

            for plant in config.get_all_plants():
                snapshot = service.get_snapshot(metric_name, plant, use_cache=False)

                if snapshot:
                    value = snapshot['value']
                    unit = snapshot['unit']
                    timestamp = snapshot['timestamp']
                    print(f"    {plant.upper()}: {value:.2f} {unit} (@ {timestamp})")
                    success_count += 1
                else:
                    plant_upper = plant.upper()
                    print(f"    {plant_upper}: ✗ No disponible")

        if success_count > 0:
            logger.info(f"✓ Se obtuvieron {success_count} snapshot(s) exitosamente")
            return True
        else:
            logger.warning("✗ No se pudo obtener ningún snapshot")
            if service.last_error:
                print(f"\nError: {service.last_error}")
            return False

    except Exception as e:
        logger.error(f"✗ Error obteniendo snapshots: {str(e)}")
        return False


def test_cache_manager():
    """Prueba gestor de caché"""
    print("\n" + "="*70)
    print("PRUEBA 4: GESTOR DE CACHÉ")
    print("="*70)

    try:
        from src.utils.cache_manager import DataCacheManager, CacheKey

        cache = DataCacheManager()
        logger.info("✓ DataCacheManager inicializado")

        # Pruebas básicas
        cache.set('test_key', {'data': 'test_value'})
        value = cache.get('test_key', max_age_seconds=60)

        if value == {'data': 'test_value'}:
            logger.info("✓ Cache set/get funcionando correctamente")
        else:
            logger.error("✗ Cache set/get no funcionando")
            return False

        # Pruebas de claves
        key1 = CacheKey.snapshot('pte1', 'electrical_power_net')
        key2 = CacheKey.historical('pte2', 'thermal_energy', '*-24h', '*')
        key3 = CacheKey.comparison('solar_radiation', '*-7d', '*')

        print(f"\n  Clave snapshot: {key1}")
        print(f"  Clave histórico: {key2}")
        print(f"  Clave comparación: {key3}")

        logger.info("✓ Gestor de caché funcionando correctamente")
        return True

    except Exception as e:
        logger.error(f"✗ Error en prueba de caché: {str(e)}")
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*70)
    print("PRUEBAS DE CONECTIVIDAD - THERMOSOLAR DASHBOARD")
    print("="*70)

    results = {
        'Carga de Configuración': test_config_loading(),
        'Conectividad PI': test_pi_connectivity(),
        'Obtención de Snapshots': test_snapshot_retrieval(),
        'Gestor de Caché': test_cache_manager(),
    }

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)

    for test_name, result in results.items():
        status = "✓ PASÓ" if result else "✗ FALLÓ"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("RESULTADO FINAL: ✓ TODAS LAS PRUEBAS PASARON")
        logger.info("Sistema listo para usar")
    else:
        print("RESULTADO FINAL: ✗ ALGUNAS PRUEBAS FALLARON")
        logger.warning("Revisa los errores anteriores")
    print("="*70 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
