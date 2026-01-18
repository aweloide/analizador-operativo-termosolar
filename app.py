#!/usr/bin/env python3
"""
Thermosolar Dashboard - Aplicación Principal
Monitorización de plantas termosolares PTE1 y PTE2
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

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc

from src.utils.config_loader import ConfigLoader
from src.core.pi_data_service import PIDataService
from src.services.indicators_service import IndicatorsService
from src.components.header import create_header
from src.components.sidebar import create_sidebar
from src.components.footer import create_footer

# Cargar configuración
try:
    config = ConfigLoader('config.yaml')
    if not config.validate_config():
        logger.error("Configuración inválida")
        sys.exit(1)

    # Log interval values
    realtime_interval = config.get_update_interval('realtime')
    historical_interval = config.get_update_interval('historical_recent')
    logger.info(f"Intervals loaded from config:")
    logger.info(f"  - Realtime (interval-fast): {realtime_interval}ms")
    logger.info(f"  - Historical (interval-slow): {historical_interval}ms")

except Exception as e:
    logger.error(f"Error cargando configuración: {str(e)}")
    sys.exit(1)

# Inicializar servicio de datos PI
try:
    pi_service = PIDataService(config)
except Exception as e:
    logger.error(f"Error inicializando servicio PI: {str(e)}")
    sys.exit(1)

# Inicializar servicio de indicadores
try:
    indicators_service = IndicatorsService(pi_service)
    logger.info("IndicatorsService inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando IndicatorsService: {str(e)}")
    indicators_service = None

# Crear aplicación Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    use_pages=True,
    pages_folder="src/pages",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ]
)

# Título de la aplicación
app.title = config.get_app_title()

# Layout principal con estructura: Header + Sidebar + Contenido + Footer
app.layout = html.Div([
    # Header compacto
    create_header(),

    # Cuerpo: Sidebar + Contenido principal
    dbc.Container([
        dbc.Row([
            # Sidebar colapsable
            dbc.Col(
                create_sidebar(),
                id="sidebar-col",
                width=2,
                style={"padding": 0}
            ),

            # Contenido principal (páginas)
            dbc.Col(
                dash.page_container,
                id="main-content-col",
                width=10,
                style={
                    "marginLeft": "250px",
                    "marginBottom": "120px",
                    "transition": "all 0.3s ease"
                }
            ),
        ], className="g-0", style={"margin": 0, "marginTop": "60px"}),
    ], fluid=True, style={"padding": 0, "margin": 0}),

    # Footer con indicadores
    create_footer(),

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

    # Stores para datos compartidos
    dcc.Store(id='shared-data-store', data={}),

], style={"minHeight": "100vh"})


# Callback para mostrar estado de conexión
@callback(
    Output('connection-status', 'children'),
    Input('interval-fast', 'n_intervals')
)
def update_connection_status(n_intervals):
    """Muestra el estado de conexión de los servidores PI"""
    logger.info(f"[update_connection_status] Callback triggered: n_intervals={n_intervals}")
    status = pi_service.get_all_plants_status()

    badges = []
    for plant, connected in status.items():
        plant_config = config.get_pi_server(plant)
        color = "success" if connected else "danger"
        status_text = "Conectado" if connected else "Desconectado"
        icon = "check-circle" if connected else "times-circle"

        badges.append(
            dbc.Badge(
                html.Div([
                    html.I(className=f"fas fa-{icon} me-2"),
                    f"{plant_config.get('name')}: {status_text}"
                ]),
                color=color,
                className="me-2 py-2 px-3",
                pill=True
            )
        )

    return html.Div(badges, className="text-center")


# Callback para toggle del sidebar (simplificado)
@callback(
    [Output('sidebar', 'style'),
     Output('main-content-col', 'style')],
    Input('sidebar-toggle', 'n_clicks'),
    prevent_initial_call=False
)
def toggle_sidebar(n_clicks):
    """Alterna entre sidebar visible (izquierda: 0px) y colapsado (izquierda: -250px)"""
    # Sidebar visible por defecto (n_clicks es None o par)
    if n_clicks is None or n_clicks % 2 == 0:
        sidebar_style = {
            "position": "fixed",
            "left": "0",
            "top": "70px",
            "width": "250px",
            "height": "calc(100vh - 70px - 120px)",
            "backgroundColor": "#f8f9fa",
            "borderRight": "1px solid #dee2e6",
            "overflowY": "auto",
            "transition": "all 0.3s ease",
            "zIndex": "999"
        }
        main_content_style = {
            "marginLeft": "250px",
            "marginBottom": "120px",
            "transition": "all 0.3s ease"
        }
    else:
        # Colapsado (mover fuera de pantalla)
        sidebar_style = {
            "position": "fixed",
            "left": "-250px",
            "top": "70px",
            "width": "250px",
            "height": "calc(100vh - 70px - 120px)",
            "backgroundColor": "#f8f9fa",
            "borderRight": "1px solid #dee2e6",
            "overflowY": "auto",
            "transition": "all 0.3s ease",
            "zIndex": "999"
        }
        main_content_style = {
            "marginLeft": "0",
            "marginBottom": "120px",
            "transition": "all 0.3s ease",
            "width": "100%"
        }

    return sidebar_style, main_content_style


# Callback para actualizar indicadores del footer
@callback(
    [Output('indicator-energy-day-pte1', 'children'),
     Output('indicator-energy-month-pte1', 'children'),
     Output('indicator-tracking-index-pte1', 'children'),
     Output('indicator-tfollow-pte1', 'children'),
     Output('indicator-pfollow-pte1', 'children'),
     Output('indicator-minutes-high-temp-pte1', 'children'),
     Output('indicator-efficiency-pte1', 'children'),
     Output('indicator-energy-day-pte2', 'children'),
     Output('indicator-energy-month-pte2', 'children'),
     Output('indicator-tracking-index-pte2', 'children'),
     Output('indicator-tfollow-pte2', 'children'),
     Output('indicator-pfollow-pte2', 'children'),
     Output('indicator-minutes-high-temp-pte2', 'children'),
     Output('indicator-efficiency-pte2', 'children')],
    Input('interval-fast', 'n_intervals')
)
def update_footer_indicators(n_intervals):
    """
    Actualiza los indicadores del footer cada 30 segundos
    Obtiene Energía Día/Mes para PTE1 y PTE2 desde PI
    Resto son placeholders por ahora
    """
    if indicators_service is None:
        logger.warning("[update_footer_indicators] IndicatorsService no inicializado")
        return (
            "-- MWh", "-- MWh", "--", "--", "--", "-- min", "--%",  # PTE1
            "-- MWh", "-- MWh", "--", "--", "--", "-- min", "--%"   # PTE2
        )

    try:
        logger.debug(f"[update_footer_indicators] Obteniendo indicadores para ambas plantas")

        # Obtener indicadores para PTE1
        indicators_pte1 = indicators_service.get_footer_indicators('pte1')

        # Obtener indicadores para PTE2
        indicators_pte2 = indicators_service.get_footer_indicators('pte2')

        # Retornar en orden: pte1 (energy_day, energy_month, tracking, tfollow, pfollow, high_temp, efficiency)
        #                    pte2 (energy_day, energy_month, tracking, tfollow, pfollow, high_temp, efficiency)
        return (
            # PTE1
            indicators_pte1[0],  # Energy day
            indicators_pte1[1],  # Energy month
            "--",               # Tracking Index (placeholder)
            "--",               # TFollow (placeholder)
            "--",               # PFollow (placeholder)
            "-- min",           # Minutos >395°C (placeholder)
            "--%",              # Rendimiento (placeholder)
            # PTE2
            indicators_pte2[0],  # Energy day
            indicators_pte2[1],  # Energy month
            "--",               # Tracking Index (placeholder)
            "--",               # TFollow (placeholder)
            "--",               # PFollow (placeholder)
            "-- min",           # Minutos >395°C (placeholder)
            "--%"               # Rendimiento (placeholder)
        )

    except Exception as e:
        logger.error(f"[update_footer_indicators] Error obteniendo indicadores: {e}")
        return (
            "-- MWh", "-- MWh", "--", "--", "--", "-- min", "--%",  # PTE1
            "-- MWh", "-- MWh", "--", "--", "--", "-- min", "--%"   # PTE2
        )


# Configurar servidor Flask
server = app.server


def main():
    """Función principal"""
    logger.info("="*70)
    logger.info("INICIANDO THERMOSOLAR DASHBOARD")
    logger.info("="*70)

    # Mostrar información de configuración
    logger.info(f"Título: {config.get_app_title()}")
    logger.info(f"Host: {config.get_app_host()}")
    logger.info(f"Puerto: {config.get_app_port()}")
    logger.info(f"Debug: {config.get_app_debug()}")

    # Mostrar estado de plantas
    logger.info("\nEstado de Plantas:")
    for plant, connected in pi_service.get_all_plants_status().items():
        status = "CONECTADO" if connected else "DESCONECTADO"
        logger.info(f"  - {plant.upper()}: {status}")

    # Mostrar métricas configuradas
    realtime_metrics = config.get_realtime_metrics()
    logger.info(f"\nMétricas en tiempo real: {len(realtime_metrics)}")
    for metric_name, metric_config in realtime_metrics.items():
        logger.info(f"  - {metric_config.get('name')}")

    logger.info("\n" + "="*70)
    logger.info(f"Dashboard disponible en: http://{config.get_app_host()}:{config.get_app_port()}")
    logger.info("="*70 + "\n")

    # Ejecutar aplicación
    app.run(
        debug=config.get_app_debug(),
        host=config.get_app_host(),
        port=config.get_app_port()
    )


if __name__ == "__main__":
    main()
