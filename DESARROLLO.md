# DESARROLLO.md

## Fase 0: Estado Inicial (2026-01-19)

Proyecto iniciado con un dashboard Dash que muestra un diagrama SVG del proceso termosolar con inyección de datos en tiempo real desde servidores PI (EWIS-PTE1 y EWIS-PTE2). La interfaz cuenta con un header (logo SOLCLEF, título y tabs de navegación), un sidebar colapsable (selector de planta PTE1/PTE2 y estado de conexiones) y un footer con tabla de indicadores para ambas plantas. Los indicadores de Energía Día y Energía Mes obtienen datos reales de PI; el resto (Índice Tracking, TFollow, PFollow, Minutos >395°C y Rendimiento) son placeholders pendientes de implementación. El config.yaml define 25 elementos del diagrama con sus tags PI correspondientes.

---

## Fase 1: Integración Índice de Tracking (2026-01-25)

### Objetivo
Integrar el cálculo del Índice de Tracking (IT) General desde el proyecto `calculadora-indice-tracking-termosolar` al footer del dashboard, con actualización configurable cada 10 minutos.

### Cambios Implementados

#### 1. Nuevo Servicio: `tracking_it_service.py`
- **Ubicación**: `src/services/tracking_it_service.py`
- **Funcionalidad**: Wrapper del módulo externo `calculadora-indice-tracking-termosolar`
- **Características**:
  - Importación dinámica de módulos externos vía `sys.path`
  - Caché diario (limpiar automáticamente al cambio de día)
  - Manejo robusto de errores y logging detallado
  - Solo PTE1 soportado inicialmente (PTE2 retorna "--")

#### 2. Configuración Ampliada: `config.yaml`
- **Nueva sección `external_modules`**: Define path relativo al proyecto calculadora-indice-tracking
- **Nuevo intervalo `indicators_calculated`**: 10 minutos (600,000 ms) configurable
- Documentación mejorada con descripciones de cada intervalo

#### 3. Actualización de Servicios Existentes
- **`indicators_service.py`**:
  - Constructor ahora acepta `config_loader` (opcional)
  - Inicializa `TrackingITService` si config está disponible
  - Import de `TrackingITService`

#### 4. Callbacks en `app.py`
- **Nuevo callback `update_tracking_index()`**:
  - Ejecuta cada 10 minutos (configurable)
  - Actualiza indicadores IT para PTE1 y PTE2
  - Persiste valores en `tracking-index-store` (dcc.Store)
  - Maneja errores sin bloquear UI

- **Modificado callback `update_footer_indicators()`**:
  - Removidos outputs de tracking index (manejados por callback dedicado)
  - Actualiza solo Energía Día/Mes cada 30 segundos
  - Comentarios claros sobre separación de responsabilidades

#### 5. Nuevos Componentes Dash
- **`dcc.Interval(id='interval-indicators-calculated')`**: Intervalo dedicado para IT
- **`dcc.Store(id='tracking-index-store')`**: Almacenamiento persistente de IT entre actualizaciones

### Arquitectura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│ analizador-operativo-termosolar (Dashboard)                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ app.py                                               │  │
│  │  - Callback update_tracking_index() [10 min]        │  │
│  │  - Callback update_footer_indicators() [30 seg]     │  │
│  └────────┬────────────────────────────┬────────────────┘  │
│           │                            │                   │
│  ┌────────▼──────────┐       ┌─────────▼──────────┐       │
│  │ IndicatorsService │       │ PIDataService      │       │
│  │ - Energía Día/Mes │       │ - Conexión PI      │       │
│  │ - TrackingITService│      │ - PTE1/PTE2        │       │
│  └────────┬──────────┘       └────────────────────┘       │
│           │                                                │
│  ┌────────▼──────────────────────────────────────────┐    │
│  │ TrackingITService                                 │    │
│  │  - Caché diario {fecha: {'pte1': IT}}            │    │
│  │  - Importación dinámica de módulos               │    │
│  │  - Path relativo: ../calculadora-indice-tracking │    │
│  └────────┬──────────────────────────────────────────┘    │
└───────────┼─────────────────────────────────────────────────┘
            │ sys.path.insert()
            ▼
┌─────────────────────────────────────────────────────────────┐
│ calculadora-indice-tracking-termosolar                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ src/tracking/                                        │  │
│  │  - tracking_index.py (TrackingIndexCalculator)      │  │
│  │  - solar_calculator.py                              │  │
│  │  - dumping_calculator.py                            │  │
│  │  - plant_data_loader.py                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Actualización

```
Dashboard inicia
    ↓
Carga config.yaml
    ↓
Inicializa TrackingITService
    ↓
Importa módulos calculadora-indice-tracking
    ↓
Dashboard ready → Footer muestra IT: "--"
    ↓
Callback update_tracking_index() se dispara (t=0)
    ↓
Primera vez → Caché vacío
    ↓
Calcula IT completo (~40 segundos, 640 SCAs)
    ↓
Retorna IT: "87.67%" → Guarda en Store
    ↓
Footer muestra: "87.67%"
    ↓
[Próximos 10 minutos]
    ↓
Callback update_footer_indicators() (cada 30s)
    ↓
Actualiza solo Energía Día/Mes
    ↓
IT permanece "87.67%" (del Store, sin recalcular)
    ↓
t=10 min → Callback update_tracking_index()
    ↓
Busca en caché → Existe valor del mismo día
    ↓
Retorna "87.67%" desde caché (instantáneo)
    ↓
Repite cada 10 min...
```

### Performance

| Operación | Primera Carga | Subsiguientes (mismo día) |
|-----------|---------------|---------------------------|
| Cálculo IT completo | ~40 segundos | <1 ms (caché) |
| Actualización footer (30s) | No bloquea | Instantáneo (Store) |
| Memoria | ~5 MB (módulos) | ~5 MB (persistente) |

### Estado Actual de Indicadores

| Indicador | Estado | Planta | Intervalo |
|-----------|--------|--------|-----------|
| Energía Día | ✅ Implementado | PTE1, PTE2 | 30 seg |
| Energía Mes | ✅ Implementado | PTE1, PTE2 | 30 seg |
| **Índice Tracking (IT)** | ✅ **Implementado** | **PTE1** | **10 min** |
| TFollow | ⏸️ Placeholder | - | - |
| PFollow | ⏸️ Placeholder | - | - |
| Minutos >395°C | ⏸️ Placeholder | - | - |
| Rendimiento | ⏸️ Placeholder | - | - |

### Próximos Pasos

1. **IT para PTE2**: Cuando se implemente en calculadora-indice-tracking
2. **Minutos >395°C**: Calcular tiempo con temperatura alta en SCAs
3. **Rendimiento Global**: Eficiencia planta (DNI → kWh neto)
4. **TFollow/PFollow**: Depende de definición de contadores en PI

### Documentación

- **Plan Completo**: [PLANNING.md](PLANNING.md) (26 KB)
- **README Actualizado**: Sección "Indicadores de Rendimiento"
- **Lecciones Aprendidas**: [LECCIONES_APRENDIDAS.md](LECCIONES_APRENDIDAS.md)

---

**Última actualización**: 2026-01-25
**Fase actual**: Fase 1 - IT Integrado ✅
