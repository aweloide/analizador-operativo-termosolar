# 🌡️ Thermosolar Dashboard

Sistema de monitorización de plantas termosolares **PTE1** y **PTE2** con datos en tiempo real desde servidores PI (OSIsoft).

## 📋 Descripción

Dashboard web que muestra un diagrama esquemático SVG con inyección dinámica de datos de temperatura desde servidores PI. Permite seleccionar entre dos plantas (PTE1 y PTE2) y visualizar sus componentes principales.

## 🚀 Inicio Rápido

### Requisitos
- Python 3.9+
- Virtual environment activado
- Dependencias instaladas

### Instalación

```bash
# 1. Clona el repositorio
cd thermosolar-dashboard

# 2. Activa el virtual environment
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate.bat  # Windows

# 3. Instala dependencias (si es necesario)
pip install -r requirements.txt

# 4. Ejecuta la aplicación
python app.py

# 5. Abre en navegador
http://127.0.0.1:8050
```

## 📁 Estructura del Proyecto

```
analizador-operativo-termosolar/
├── app.py                          # Aplicación principal Dash
├── config.yaml                     # Configuración central
│
├── src/
│   ├── pages/
│   │   └── cycle_analysis.py      # Página principal con layout
│   ├── components/
│   │   ├── thermosolar_schematic.py # Componente SVG con inyección de datos
│   │   ├── header.py              # Header con logo y navegación
│   │   ├── sidebar.py             # Sidebar con selector de planta
│   │   └── footer.py              # Footer con indicadores KPI
│   ├── core/
│   │   ├── pi_connector.py        # Conector a servidores PI
│   │   └── pi_data_service.py     # Servicio de datos PI
│   ├── services/
│   │   ├── indicators_service.py  # Servicio de indicadores (energía, IT)
│   │   └── tracking_it_service.py # Servicio de Índice de Tracking ⭐ NUEVO
│   └── utils/
│       └── config_loader.py       # Cargador de configuración YAML
│
├── assets/
│   └── schematic_diagram.svg      # Diagrama esquemático
│
├── tests/
│   └── test_pi_connection.py      # Tests de conexión a PI
│
├── PLANNING.md                     # Plan de implementación IT
├── DESARROLLO.md                   # Estado del desarrollo
├── DIRECTRICES.md                  # Guía de desarrollo
└── README.md                       # Este archivo
```

## ⚙️ Configuración

### config.yaml

Archivo central que define:

1. **Servidores PI**
```yaml
pi_servers:
  pte1:
    host: "EWIS-PTE1.solclef.local"
    name: "Termosol 1 (PTE1)"
  pte2:
    host: "EWIS-PTE2.solclef.local"
    name: "Termosol 2 (PTE2)"
```

2. **Elementos del Diagrama**
```yaml
schematic_elements:
  hot_tank:
    name: "Tanque Sales Calientes"
    svg_element_id: "3WSH10CT999A.Out"
    tags:
      pte1: "13WSH10CT999A.Out"
      pte2: "23WSH10CT999A.Out"
    format: "{value:.1f}°C"
```

3. **Intervalos de Actualización**
```yaml
update_intervals:
  realtime:
    interval_ms: 30000  # 30 segundos (energía, conexiones)

  historical_recent:
    interval_ms: 60000  # 60 segundos (gráficos históricos)

  indicators_calculated:
    interval_ms: 600000  # 10 minutos (IT, rendimiento)
```

4. **Módulos Externos** ⭐ NUEVO
```yaml
external_modules:
  calculadora_tracking:
    enabled: true
    path: "../calculadora-indice-tracking-termosolar"
    plantas_soportadas: ["pte1"]
```

## 🔄 Cómo Agregar un Nuevo Elemento

### Paso 1: Editar config.yaml

```yaml
schematic_elements:
  # ... elementos existentes ...

  # NUEVO ELEMENTO
  hot_pump:
    name: "Bomba Sales Calientes"
    unit: "RPM"
    svg_element_id: "3WSH10AP001"
    tags:
      pte1: "13WSH10AP001.PV"
      pte2: "23WSH10AP001.PV"
    format: "{value:.0f} RPM"
```

### Paso 2: Agregar elemento al SVG

En `assets/schematic_diagram.svg`:
```xml
<text id="3WSH10AP001">--</text>
```

**¡Listo!** El sistema automáticamente:
1. Lee la configuración
2. Obtiene el valor de PI
3. Inyecta el valor en el SVG

## 📊 Componentes Principales

### [thermosolar_schematic.py](src/components/thermosolar_schematic.py)

Componente que renderiza el diagrama SVG con inyección de datos:

- `create_thermosolar_schematic(plant)` - Función principal
- `_load_config()` - Carga YAML
- `_build_pi_tag_mapping()` - Mapeo dinámico según planta
- `_fetch_temperatures_from_pi()` - Obtiene valores de PI
- `_format_temperatures()` - Aplica formato
- `_inject_values_into_svg()` - Inyecta en SVG
- `_create_svg_container()` - Crea contenedor HTML

### [pi_connector.py](src/core/pi_connector.py)

Conector a servidores PI:
- Conexión a EWIS-PTE1 y EWIS-PTE2
- Obtiene snapshots de datos
- Maneja errores de conexión

### [config_loader.py](src/utils/config_loader.py)

Cargador de configuración YAML con validación

## 🎯 Flujo de Datos

```
Usuario selecciona planta
    ↓
cycle_analysis.py actualiza
    ↓
create_thermosolar_schematic() se ejecuta
    ↓
config.yaml → schematic_elements
    ↓
build_pi_tag_mapping() → mapeo dinámico
    ↓
PI Server → fetch valores
    ↓
_inject_values_into_svg() → SVG con datos
    ↓
Base64 encode → HTML img tag
    ↓
Usuario ve diagrama actualizado
```

## 🔧 Tecnologías

- **Backend**: Python 3.9+
- **Framework**: Dash (Plotly)
- **Estilos**: Bootstrap 5
- **Conexión PI**: OSIsoft PI Connector
- **Configuración**: YAML

## 📝 Logs

Los logs se muestran en la terminal donde ejecutas `python app.py`:

```
2026-01-13 10:30:45 - root - INFO - Conectando a EWIS-PTE1...
2026-01-13 10:30:46 - root - INFO - Conexión exitosa
2026-01-13 10:30:46 - root - INFO - 13WSH10CT999A.Out: 385.2°C
```

## 🐛 Troubleshooting

### "SVG no encontrado"
- Verifica que `assets/schematic_diagram.svg` exista
- Revisa la ruta en `thermosolar_schematic.py`

### "No se pudo conectar al servidor PI"
- Verifica que `EWIS-PTE1.solclef.local` está accesible
- Revisa configuración en `config.yaml`
- Ejecuta: `python tests/test_pi_connection.py`

### "Elemento no encontrado en SVG"
- El sistema lo inyecta automáticamente
- Verifica que el `svg_element_id` es correcto en config.yaml

## 🎯 Indicadores de Rendimiento (Footer)

El dashboard muestra indicadores clave en el footer para ambas plantas (PTE1 y PTE2):

| Indicador | Descripción | Estado | Intervalo Actualización |
|-----------|-------------|--------|------------------------|
| **Energía Día** | Generación neta acumulada desde 08:00 hasta ahora | ✅ Implementado | 30 segundos |
| **Energía Mes** | Generación neta acumulada desde día 1 a las 08:00 | ✅ Implementado | 30 segundos |
| **Índice Tracking (IT)** | Eficiencia operacional del campo solar | ✅ Implementado ⭐ | 10 minutos |
| **TFollow** | Movimientos a TFollow | ⏸️ Placeholder | - |
| **PFollow** | Movimientos a PFollow | ⏸️ Placeholder | - |
| **Minutos >395°C** | Tiempo con temperatura alta en SCAs | ⏸️ Placeholder | - |
| **Rendimiento** | Eficiencia global de planta | ⏸️ Placeholder | - |

### Índice de Tracking (IT) ⭐

**Implementación**: 2026-01-25

El dashboard ejecuta el script `calcular_it_completo.py` del proyecto [`calculadora-indice-tracking-termosolar`](../calculadora-indice-tracking-termosolar/) usando subprocess:

**Características**:
- ✅ Cálculo completo de IT para PTE1 (640 SCAs)
- ✅ Actualización configurable (por defecto: 10 minutos)
- ✅ Caché diario (primera carga ~3-5 min, luego instantáneo)
- ✅ Persistencia en Store entre actualizaciones
- ✅ Ejecución aislada (subprocess): robusta y simple
- ⏸️ PTE2 pendiente (muestra "--" por ahora)

**Fórmula**:
```
IT = (DII_total - Pérdidas_operacionales) / DII_total × 100%

Pérdidas_operacionales = Orto→PrimerTracking + ÚltimoTracking→Ocaso +
                        PFollow + GestiónTransitorios + Otros
```

**NO incluye**: Pérdidas por desapuntamiento angular ni SCA no disponible

**Valor típico**: 87-95% (valores bajos indican problemas operacionales)

**Ver más**: [PLANNING.md](PLANNING.md) para detalles de implementación

### Energía Día y Energía Mes ✅

**Implementación**: 2026-01-26

Los indicadores de energía se calculan mediante diferencia de contadores acumulativos (TAG: `CONT_AM_PRINCIPAL`):

**Características**:
- ✅ Cálculo por diferencia de contadores (no por agregados de potencia)
- ✅ Períodos alineados con operación solar (desde 08:00, no medianoche)
- ✅ Unidades: kWh en PI, convertido a MWh para display
- ✅ Validación: Rechaza valores negativos (indicaría reinicio de contador)
- ✅ Método homogéneo: Usa `recorded_value()` con `AT_OR_BEFORE` para ambos valores

**Fórmula**:
```python
# Energía Día (desde hoy 08:00 hasta ahora)
valor_actual = get_value_at_time("CONT_AM_PRINCIPAL", "*")        # kWh ahora
valor_inicio = get_value_at_time("CONT_AM_PRINCIPAL", "t+8h")     # kWh a las 08:00
energia_dia = (valor_actual - valor_inicio) / 1000  # MWh

# Energía Mes (desde día 1 a las 08:00 hasta ahora)
mes_inicio = "2026-01-01 08:00:00"
energia_mes = (valor_actual - valor_inicio_mes) / 1000  # MWh
```

**Valores típicos**:
- Día: 0-50 MWh (dependiendo de radiación solar)
- Mes: 400-1000 MWh (plantas de ~50 MW)

---

## 🔧 Configuración Avanzada

### Cambiar Intervalo de Actualización del IT

Edita `config.yaml`:
```yaml
indicators_calculated:
  interval_ms: 300000  # 5 minutos (en vez de 10)
```

Valores recomendados:
- **5 minutos**: `300000` ms (más frecuente)
- **10 minutos**: `600000` ms (por defecto, equilibrado)
- **15 minutos**: `900000` ms (menor carga)

### Deshabilitar IT Temporalmente

```yaml
external_modules:
  calculadora_tracking:
    enabled: false
```

---

## 📞 Contacto

Para preguntas o reportar problemas, contacta al equipo de desarrollo.

---

**Última actualización**: 2026-01-26
**Versión**: 2.3
**Status**: ✅ Operacional + IT Integrado + Energía por Contadores
