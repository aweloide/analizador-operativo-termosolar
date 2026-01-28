# Plan de Integración: Índice de Tracking (IT) en el Analizador Operativo

## Objetivo
Integrar el cálculo del Índice de Tracking (IT) General desde el proyecto `calculadora-indice-tracking-termosolar` al footer del `analizador-operativo-termosolar`, mostrando el IT del día actual para PTE1.

## Contexto

### Estado Actual
- **Analizador Operativo**: Dashboard Dash con footer mostrando 7 indicadores por planta
  - ✅ Energía Día/Mes: Implementados y funcionando
  - ❌ Tracking Index: Placeholder ("--")
  - ❌ TFollow/PFollow: Placeholders (no implementar por ahora)
  - ❌ Minutos >395°C: Placeholder (implementar después)
  - ❌ Rendimiento: Placeholder (implementar después)

- **Calculadora IT**: Sistema autónomo completo y validado
  - Script principal: `calcular_it_completo.py`
  - Módulo reutilizable: `src/tracking/tracking_index.py`
  - Clase: `TrackingIndexCalculator`
  - IT General validado: 87.67% vs 87.5% Excel (diferencia +0.17%)
  - Solo implementado para PTE1 (TER1)

### IT General - Definición
```
IT = (DII_total - Pérdidas_operacionales) / DII_total × 100%

Pérdidas_operacionales = Orto→PrimerTracking + ÚltimoTracking→Ocaso +
                        PFollow + GestiónTransitorios + Otros
```

**NO incluye**: Pérdidas por desapuntamiento angular ni SCA no disponible

## Arquitectura Propuesta

### Opción Elegida: Reutilización con Módulo Compartido

**Ventaja**:
- Código DRY (Don't Repeat Yourself)
- Usa el cálculo ya validado
- Fácil mantenimiento

**Estructura**:
```
01. TRABAJOS/03. IA/
├── calculadora-indice-tracking-termosolar/     # Proyecto fuente
│   └── src/tracking/                           # Módulos reutilizables
│       ├── tracking_index.py                   # Clase TrackingIndexCalculator
│       ├── solar_calculator.py
│       ├── dumping_calculator.py
│       └── plant_data_loader.py
│
└── analizador-operativo-termosolar/            # Proyecto destino
    ├── src/services/
    │   ├── indicators_service.py               # MODIFICAR: Agregar método IT
    │   └── tracking_it_service.py              # NUEVO: Wrapper del calculador IT
    └── config.yaml                             # MODIFICAR: Agregar path a calculadora
```

## Plan de Implementación

### Fase 1: Preparación del Entorno

#### 1.1. Actualizar config.yaml del analizador
**Archivo**: `analizador-operativo-termosolar/config.yaml`

**Agregar nueva sección para módulos externos**:
```yaml
# Configuración de módulos externos
external_modules:
  calculadora_tracking:
    enabled: true
    path: "../calculadora-indice-tracking-termosolar"
    plantas_soportadas: ["pte1"]  # Solo PTE1 por ahora
```

**Modificar sección de intervalos de actualización**:
```yaml
# Configuración de Intervalos de Actualización
update_intervals:
  realtime:
    enabled: true
    interval_ms: 30000  # 30 segundos para snapshots (energía día/mes, conexiones)
    description: "Actualización de datos en tiempo real y energía acumulada"

  historical_recent:
    enabled: true
    interval_ms: 60000  # 60 segundos para datos históricos recientes
    description: "Actualización de gráficos históricos recientes"

  historical_long:
    enabled: false  # Solo bajo demanda (cuando el usuario cambia selector)
    description: "Datos históricos de largo plazo"

  # NUEVO: Intervalo para indicadores calculados (IT, rendimiento, etc.)
  indicators_calculated:
    enabled: true
    interval_ms: 600000  # 10 minutos (600,000 ms)
    description: "Actualización de indicadores que requieren cálculos pesados (IT, rendimiento)"
```

#### 1.2. Verificar dependencias
Ambos proyectos usan PIconnect, pandas, numpy - ya están instalados.

---

### Fase 2: Crear Servicio de IT

#### 2.1. Crear tracking_it_service.py
**Archivo NUEVO**: `analizador-operativo-termosolar/src/services/tracking_it_service.py`

**Funcionalidad**:
```python
#!/usr/bin/env python3
"""
Servicio de Índice de Tracking
Integra el calculador IT del proyecto calculadora-indice-tracking-termosolar
"""

import sys
from pathlib import Path
from datetime import date
import logging

logger = logging.getLogger(__name__)


class TrackingITService:
    """Servicio para calcular el Índice de Tracking usando el módulo externo"""

    def __init__(self, config_loader, pi_data_service):
        """
        Args:
            config_loader: ConfigLoader con path al módulo calculadora
            pi_data_service: PIDataService para acceso a conectores PI
        """
        self.config = config_loader
        self.pi_service = pi_data_service

        # Agregar path del módulo calculadora al sys.path
        calculadora_path = self._get_calculadora_path()
        if calculadora_path and calculadora_path not in sys.path:
            sys.path.insert(0, str(calculadora_path))
            logger.info(f"Módulo calculadora-indice-tracking agregado: {calculadora_path}")

        # Importar módulo externo
        try:
            from src.tracking.tracking_index import TrackingIndexCalculator
            from src.tracking.plant_data_loader import cargar_planta_ter1
            self.TrackingIndexCalculator = TrackingIndexCalculator
            self.cargar_planta_ter1 = cargar_planta_ter1
            logger.info("Módulos de tracking importados correctamente")
        except ImportError as e:
            logger.error(f"Error importando módulos tracking: {e}")
            self.TrackingIndexCalculator = None
            self.cargar_planta_ter1 = None

    def _get_calculadora_path(self) -> Path:
        """Obtiene el path absoluto al módulo calculadora desde config"""
        try:
            relative_path = self.config.config.get('external_modules', {}) \
                .get('calculadora_tracking', {}).get('path')

            if not relative_path:
                logger.warning("Path a calculadora-tracking no configurado")
                return None

            # Resolver path relativo desde la raíz del analizador
            base_path = Path(__file__).parent.parent.parent  # Sube a raíz de analizador
            abs_path = (base_path / relative_path).resolve()

            if not abs_path.exists():
                logger.error(f"Path calculadora no existe: {abs_path}")
                return None

            return abs_path

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
        # Verificar que módulos estén cargados
        if not self.TrackingIndexCalculator:
            logger.warning("Módulo TrackingIndexCalculator no disponible")
            return "--"

        # Solo PTE1 soportado por ahora
        if plant.lower() != 'pte1':
            logger.debug(f"IT no disponible para {plant.upper()}")
            return "--"

        try:
            # Obtener connector PI de la planta
            connector = self.pi_service.connectors.get(plant.lower())
            if not connector:
                logger.warning(f"No hay connector PI para {plant}")
                return "--"

            # Cargar configuración de planta TER1
            planta_config = self.cargar_planta_ter1()

            # Crear calculador
            calculator = self.TrackingIndexCalculator(
                planta='TER1',
                pi_connector=connector.connector,  # Usar PIConnect.PIServer
                config_planta=planta_config
            )

            # Calcular IT del día actual
            fecha_hoy = date.today()
            logger.info(f"Calculando IT para {fecha_hoy}")

            indices = calculator.calcular_dia(fecha=fecha_hoy)

            # Extraer IT General
            if indices and hasattr(indices, 'it_general'):
                it_value = indices.it_general
                logger.info(f"IT General calculado: {it_value:.2f}%")
                return f"{it_value:.2f}%"
            else:
                logger.warning("No se pudo calcular IT General")
                return "--"

        except Exception as e:
            logger.error(f"Error calculando IT para {plant}: {e}", exc_info=True)
            return "--"
```

**Puntos clave**:
- Usa `sys.path.insert()` para importar módulos del proyecto calculadora
- Reutiliza `TrackingIndexCalculator` existente y validado
- Solo calcula para PTE1 (retorna "--" para PTE2)
- Manejo robusto de errores con logging
- Usa el connector PI ya existente del analizador

---

### Fase 3: Integrar en IndicatorsService

#### 3.1. Modificar indicators_service.py
**Archivo**: `analizador-operativo-termosolar/src/services/indicators_service.py`

**Cambios**:

1. **Importar TrackingITService**:
```python
from .tracking_it_service import TrackingITService
```

2. **Modificar constructor**:
```python
def __init__(self, pi_data_service, config_loader=None):
    """
    Args:
        pi_data_service: Instancia de PIDataService
        config_loader: ConfigLoader para acceder a configuración
    """
    self.pi_service = pi_data_service

    # Inicializar servicio IT si config disponible
    if config_loader:
        try:
            self.tracking_it_service = TrackingITService(config_loader, pi_data_service)
            logger.info("TrackingITService inicializado")
        except Exception as e:
            logger.error(f"Error inicializando TrackingITService: {e}")
            self.tracking_it_service = None
    else:
        self.tracking_it_service = None
        logger.warning("ConfigLoader no proporcionado, IT no disponible")
```

3. **Modificar get_footer_indicators()**:
```python
def get_footer_indicators(self, plant: str) -> Tuple[str, str, str, str, str, str, str]:
    """
    Obtiene los 7 indicadores formateados para el footer

    Returns:
        Tuple con 7 strings (energía día, energía mes, tracking IT,
        tfollow, pfollow, minutos >395°C, rendimiento)
    """
    try:
        # ... código existente para energía día/mes ...

        # Obtener IT General del día actual
        tracking_index = "--"
        if self.tracking_it_service:
            tracking_index = self.tracking_it_service.get_it_dia_actual(plant)

        return (
            energy_day,       # Energía Día
            energy_month,     # Energía Mes
            tracking_index,   # IT General ← NUEVO
            "--",             # TFollow (placeholder)
            "--",             # PFollow (placeholder)
            "-- min",         # Minutos >395°C (placeholder)
            "--%"             # Rendimiento (placeholder)
        )

    except Exception as e:
        logger.error(f"Error obteniendo indicadores para {plant}: {e}")
        return ("--", "--", "--", "--", "--", "-- min", "--%")
```

---

### Fase 4: Actualizar app.py

#### 4.1. Pasar ConfigLoader a IndicatorsService
**Archivo**: `analizador-operativo-termosolar/app.py`

**Modificar inicialización** (línea ~59):
```python
# Inicializar servicio de indicadores
try:
    indicators_service = IndicatorsService(pi_service, config_loader=config)  # ← Agregar config
    logger.info("IndicatorsService inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando IndicatorsService: {str(e)}")
    indicators_service = None
```

#### 4.2. Agregar intervalo dedicado para indicadores calculados

**Modificar sección de intervalos** (después de línea ~116):
```python
# Intervalos de actualización
dcc.Interval(
    id='interval-fast',
    interval=config.get_update_interval('realtime'),
    n_intervals=0,
    disabled=False
),

dcc.Interval(
    id='interval-slow',
    interval=config.get_update_interval('historical_recent'),
    n_intervals=0,
    disabled=False
),

# NUEVO: Intervalo para indicadores calculados (IT, rendimiento, etc.)
dcc.Interval(
    id='interval-indicators-calculated',
    interval=config.get_update_interval('indicators_calculated'),  # ← Lee de config.yaml
    n_intervals=0,
    disabled=False
),

# Stores para datos compartidos
dcc.Store(id='shared-data-store', data={}),

# NUEVO: Store para persistir valores de IT entre actualizaciones
dcc.Store(id='tracking-index-store', data={'pte1': '--', 'pte2': '--'}),
```

**Log de intervalos al inicio** (después de línea ~44):
```python
# Log interval values
realtime_interval = config.get_update_interval('realtime')
historical_interval = config.get_update_interval('historical_recent')
calculated_interval = config.get_update_interval('indicators_calculated')  # ← NUEVO
logger.info(f"Intervals loaded from config:")
logger.info(f"  - Realtime (interval-fast): {realtime_interval}ms")
logger.info(f"  - Historical (interval-slow): {historical_interval}ms")
logger.info(f"  - Calculated Indicators (interval-indicators-calculated): {calculated_interval}ms")  # ← NUEVO
```

#### 4.3. Crear callback dedicado para IT

**Agregar nuevo callback** (después del callback de update_footer_indicators):
```python
# Callback para actualizar Índice de Tracking cada 10 minutos
@callback(
    [Output('indicator-tracking-index-pte1', 'children'),
     Output('indicator-tracking-index-pte2', 'children'),
     Output('tracking-index-store', 'data')],
    Input('interval-indicators-calculated', 'n_intervals'),
    State('tracking-index-store', 'data')
)
def update_tracking_index(n_intervals, current_values):
    """
    Actualiza el Índice de Tracking cada X minutos (configurable en config.yaml)
    y persiste valores en Store para mostrar entre actualizaciones

    Args:
        n_intervals: Número de veces que se ha ejecutado el intervalo
        current_values: Valores actuales de IT en el Store

    Returns:
        Tuple (it_pte1, it_pte2, store_data)
    """
    if indicators_service is None or not hasattr(indicators_service, 'tracking_it_service'):
        logger.warning("[update_tracking_index] IndicatorsService o TrackingITService no disponible")
        return current_values.get('pte1', '--'), current_values.get('pte2', '--'), current_values

    try:
        logger.info(f"[update_tracking_index] Actualizando IT (intervalo #{n_intervals})")

        # Calcular IT para ambas plantas
        it_pte1 = indicators_service.tracking_it_service.get_it_dia_actual('pte1')
        it_pte2 = indicators_service.tracking_it_service.get_it_dia_actual('pte2')

        # Actualizar store con nuevos valores
        new_values = {'pte1': it_pte1, 'pte2': it_pte2}

        logger.info(f"[update_tracking_index] IT actualizado - PTE1: {it_pte1}, PTE2: {it_pte2}")

        return it_pte1, it_pte2, new_values

    except Exception as e:
        logger.error(f"[update_tracking_index] Error actualizando IT: {e}", exc_info=True)
        # Mantener valores anteriores en caso de error
        return current_values.get('pte1', '--'), current_values.get('pte2', '--'), current_values
```

#### 4.4. Modificar callback del footer

**Modificar update_footer_indicators** para NO incluir tracking index (líneas ~222-288):
```python
@callback(
    [Output('indicator-energy-day-pte1', 'children'),
     Output('indicator-energy-month-pte1', 'children'),
     # ELIMINADO: Output('indicator-tracking-index-pte1', 'children'),
     Output('indicator-tfollow-pte1', 'children'),
     Output('indicator-pfollow-pte1', 'children'),
     Output('indicator-minutes-high-temp-pte1', 'children'),
     Output('indicator-efficiency-pte1', 'children'),
     Output('indicator-energy-day-pte2', 'children'),
     Output('indicator-energy-month-pte2', 'children'),
     # ELIMINADO: Output('indicator-tracking-index-pte2', 'children'),
     Output('indicator-tfollow-pte2', 'children'),
     Output('indicator-pfollow-pte2', 'children'),
     Output('indicator-minutes-high-temp-pte2', 'children'),
     Output('indicator-efficiency-pte2', 'children')],
    Input('interval-fast', 'n_intervals')
)
def update_footer_indicators(n_intervals):
    """
    Actualiza los indicadores del footer cada 30 segundos
    NOTA: El Tracking Index se actualiza en su propio callback cada 10 minutos
    """
    if indicators_service is None:
        logger.warning("[update_footer_indicators] IndicatorsService no inicializado")
        return (
            "-- MWh", "-- MWh", "--", "--", "-- min", "--%",  # PTE1 (sin IT)
            "-- MWh", "-- MWh", "--", "--", "-- min", "--%"   # PTE2 (sin IT)
        )

    try:
        logger.debug(f"[update_footer_indicators] Obteniendo indicadores para ambas plantas")

        # Obtener indicadores para PTE1 (solo energía día/mes, el resto placeholders)
        indicators_pte1 = indicators_service.get_footer_indicators('pte1')

        # Obtener indicadores para PTE2
        indicators_pte2 = indicators_service.get_footer_indicators('pte2')

        # Retornar en orden (sin tracking index, lo maneja otro callback):
        return (
            # PTE1
            indicators_pte1[0],  # Energy day
            indicators_pte1[1],  # Energy month
            # indicators_pte1[2] es IT, pero ya NO se incluye aquí
            "--",               # TFollow (placeholder)
            "--",               # PFollow (placeholder)
            "-- min",           # Minutos >395°C (placeholder)
            "--%",              # Rendimiento (placeholder)
            # PTE2
            indicators_pte2[0],  # Energy day
            indicators_pte2[1],  # Energy month
            "--",               # TFollow (placeholder)
            "--",               # PFollow (placeholder)
            "-- min",           # Minutos >395°C (placeholder)
            "--%"               # Rendimiento (placeholder)
        )

    except Exception as e:
        logger.error(f"[update_footer_indicators] Error obteniendo indicadores: {e}")
        return (
            "-- MWh", "-- MWh", "--", "--", "-- min", "--%",  # PTE1
            "-- MWh", "-- MWh", "--", "--", "-- min", "--%"   # PTE2
        )
```

---

### Fase 5: Formato y Visualización

#### 5.1. Actualizar footer.py (si es necesario)
**Archivo**: `analizador-operativo-termosolar/src/components/footer.py`

El footer ya tiene el elemento `indicator-tracking-index-pte1` y `indicator-tracking-index-pte2`, así que **NO REQUIERE CAMBIOS**.

El formato será: "87.67%" (dos decimales con símbolo %)

---

## Validaciones y Manejo de Errores

### Escenarios a Manejar

| Escenario | Comportamiento | Display |
|-----------|----------------|---------|
| PTE1 con datos válidos | Calcular IT del día | "87.67%" |
| PTE1 sin datos PI | Registrar error, retornar placeholder | "--" |
| PTE2 solicitado | No calcular (no soportado aún) | "--" |
| Módulo calculadora no encontrado | Log error en inicialización | "--" |
| Error durante cálculo | Log error con stacktrace | "--" |
| Día sin operación (IT = 0%) | Mostrar valor real | "0.00%" |

### Logging
- **INFO**: Inicio de cálculo, valores calculados exitosamente
- **WARNING**: Planta no soportada, módulo no configurado
- **ERROR**: Errores de importación, cálculo, conexión PI

---

## Consideraciones de Performance

### Tiempo de Cálculo
El script `calcular_it_completo.py` procesa 640 SCAs en ~41 segundos.

**Problema**: El footer se actualiza cada 30 segundos, el cálculo tomaría más tiempo.

**Solución**: Caché diario
```python
class TrackingITService:
    def __init__(self, ...):
        self._cache_it = {}  # {fecha: {'pte1': valor_it}}
        self._ultima_fecha = None

    def get_it_dia_actual(self, plant: str) -> str:
        fecha_hoy = date.today()

        # Usar caché si existe para hoy
        if fecha_hoy in self._cache_it and plant in self._cache_it[fecha_hoy]:
            logger.debug(f"IT en caché para {plant}: {self._cache_it[fecha_hoy][plant]}")
            return self._cache_it[fecha_hoy][plant]

        # Calcular IT (solo una vez al día)
        it_valor = self._calcular_it_completo(plant, fecha_hoy)

        # Guardar en caché
        if fecha_hoy not in self._cache_it:
            self._cache_it = {fecha_hoy: {}}  # Limpiar caché de días anteriores

        self._cache_it[fecha_hoy][plant] = it_valor

        return it_valor
```

**Resultado**:
- Primera llamada del día: ~41 segundos (cálculo completo)
- Siguientes llamadas: <1ms (desde caché)
- Footer no se bloquea después de la primera carga

### Optimización Futura
- Calcular IT en background thread al inicio del día
- Actualizar cada hora automáticamente
- Pre-calentar caché al arrancar la aplicación

---

## Testing

### Test Manual
1. **Verificar importación de módulos**:
   ```python
   python -c "from src.services.tracking_it_service import TrackingITService; print('OK')"
   ```

2. **Verificar cálculo IT**:
   - Ejecutar dashboard
   - Observar logs de inicio (debe mostrar "TrackingITService inicializado")
   - Observar footer en navegador
   - Para PTE1: Debe mostrar valor tipo "87.67%" (tardará ~41s la primera vez)
   - Para PTE2: Debe mostrar "--"

3. **Verificar caché**:
   - Esperar 30 segundos (siguiente actualización del footer)
   - Verificar en logs que no se recalcula ("IT en caché...")
   - Verificar que valor persiste en footer

### Test de Errores
1. **Módulo no encontrado**:
   - Modificar path en config.yaml a path inválido
   - Verificar que dashboard arranca y muestra "--"
   - Verificar log de error

2. **Conexión PI perdida**:
   - Simular pérdida de conexión
   - Verificar que retorna "--" sin crashear

---

## Archivos Modificados/Creados

### Archivos NUEVOS
1. `analizador-operativo-termosolar/src/services/tracking_it_service.py`

### Archivos MODIFICADOS
1. `analizador-operativo-termosolar/config.yaml`
   - Agregar sección `external_modules`
   - Agregar intervalo `indicators_calculated` en `update_intervals`

2. `analizador-operativo-termosolar/src/services/indicators_service.py`
   - Importar TrackingITService
   - Modificar `__init__()` para aceptar config_loader
   - Modificar `get_footer_indicators()` para obtener IT

3. `analizador-operativo-termosolar/app.py`
   - Pasar `config_loader=config` a IndicatorsService
   - Agregar `dcc.Interval` para `interval-indicators-calculated`
   - Agregar `dcc.Store` para `tracking-index-store`
   - Agregar callback `update_tracking_index()`
   - Modificar callback `update_footer_indicators()` para remover tracking index
   - Agregar log de intervalo calculado al inicio

### Archivos NO MODIFICADOS
- `src/components/footer.py` (ya tiene los elementos necesarios)
- Proyecto `calculadora-indice-tracking-termosolar` (se usa as-is)

---

## Cronograma de Implementación

1. **Preparación** (15 min):
   - Actualizar config.yaml
   - Verificar paths

2. **Desarrollo** (45 min):
   - Crear tracking_it_service.py con caché
   - Modificar indicators_service.py
   - Modificar app.py

3. **Testing** (20 min):
   - Test de importación
   - Test de cálculo IT
   - Test de caché
   - Test de errores

4. **Refinamiento** (10 min):
   - Ajustar logging
   - Optimizar tiempos

**Total estimado**: ~1.5 horas

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Cálculo IT tarda >30s y bloquea footer | Alto | Implementar caché diario |
| Path relativo incorrecto entre proyectos | Medio | Validar path en init, fallar gracefully |
| Dependencias incompatibles entre proyectos | Bajo | Ambos usan mismas librerías |
| IT no se actualiza durante el día | Bajo | Documentar que IT es diario, actualizar cada hora |

---

## Escalabilidad: Otros Indicadores Calculados

La arquitectura con `interval-indicators-calculated` permite agregar fácilmente otros indicadores pesados:

```python
# En el futuro, el mismo callback puede manejar múltiples indicadores:
@callback(
    [Output('indicator-tracking-index-pte1', 'children'),
     Output('indicator-tracking-index-pte2', 'children'),
     Output('indicator-efficiency-pte1', 'children'),  # ← Rendimiento futuro
     Output('indicator-efficiency-pte2', 'children'),  # ← Rendimiento futuro
     Output('calculated-indicators-store', 'data')],
    Input('interval-indicators-calculated', 'n_intervals'),
    State('calculated-indicators-store', 'data')
)
def update_calculated_indicators(n_intervals, current_values):
    """Actualiza todos los indicadores que requieren cálculos pesados"""
    # IT
    it_pte1 = indicators_service.tracking_it_service.get_it_dia_actual('pte1')
    it_pte2 = indicators_service.tracking_it_service.get_it_dia_actual('pte2')

    # Rendimiento (cuando se implemente)
    efficiency_pte1 = indicators_service.get_efficiency('pte1')
    efficiency_pte2 = indicators_service.get_efficiency('pte2')

    return it_pte1, it_pte2, efficiency_pte1, efficiency_pte2, {...}
```

**Ventaja**: Un solo intervalo configurable para todos los indicadores pesados.

---

## Próximos Pasos (Post-IT)

Una vez implementado el IT, continuar con:
1. **Minutos >395°C**: Calcular tiempo con temperatura alta en SCAs (puede usar mismo intervalo)
2. **Rendimiento Global**: Eficiencia planta (DNI → kWh neto) (usar `interval-indicators-calculated`)
3. **TFollow/PFollow**: Depende de definición de contadores en PI

---

## Notas Finales

- El IT solo está disponible para PTE1 (TER1), PTE2 mostrará "--" hasta que se implemente
- El cálculo IT es pesado (~41s), usar caché es esencial
- El módulo calculadora es independiente y ya está validado (+0.17% vs Excel)
- No se modifican archivos del proyecto calculadora (solo importación)
- Logging detallado para debugging de producción
