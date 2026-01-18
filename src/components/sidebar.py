#!/usr/bin/env python3
"""
Componente Sidebar
Renderiza la barra lateral con selector de planta, estado de conexión y configuración
"""

from dash import html, dcc


def create_sidebar() -> html.Div:
    """
    Crea la barra lateral (sidebar) de la aplicación

    Returns:
        html.Div con estructura: [Selector | Estado | Config]
    """
    return html.Div([
        # Selector de Planta
        html.Div([
            html.H6("Planta", style={"marginTop": "20px", "marginBottom": "10px"}),
            dcc.RadioItems(
                id='plant-selector',
                options=[
                    {'label': ' PTE1', 'value': 'pte1'},
                    {'label': ' PTE2', 'value': 'pte2'}
                ],
                value='pte1',
                inline=False,
                style={"marginBottom": "15px"}
            ),
        ], style={"padding": "10px"}),

        html.Hr(style={"margin": "10px 0"}),

        # Estado de Conexiones
        html.Div([
            html.H6("Conexiones", style={"marginBottom": "10px"}),
            html.Div(
                id='connection-status',
                style={
                    "padding": "10px",
                    "backgroundColor": "#f8f9fa",
                    "borderRadius": "4px",
                    "minHeight": "80px"
                }
            ),
        ], style={"padding": "10px"}),

        html.Hr(style={"margin": "10px 0"}),

        # Configuración (placeholder)
        html.Div([
            html.H6("Configuración", style={"marginBottom": "10px"}),
            dcc.Dropdown(
                id='config-selector',
                options=[
                    {'label': 'config.yaml', 'value': 'default'}
                ],
                value='default',
                style={"width": "100%"}
            ),
        ], style={"padding": "10px"}),

    ], id="sidebar", style={
        "position": "fixed",
        "left": "0",
        "top": "70px",
        "width": "250px",
        "height": "calc(100vh - 70px - 120px)",
        "backgroundColor": "#ffffff",
        "borderRight": "2px solid #dee2e6",
        "boxShadow": "2px 0 10px rgba(0,0,0,0.05)",
        "overflowY": "auto",
        "transition": "all 0.3s ease",
        "zIndex": "999",
        "padding": "20px"
    })
