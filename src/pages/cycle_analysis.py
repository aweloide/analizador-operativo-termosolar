#!/usr/bin/env python3
"""
Página: Analizador de Ciclo Termodinámico
Visualización del diagrama esquemático SVG con datos en tiempo real desde PI
"""

import dash
from dash import html, callback, Input, Output
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.components.thermosolar_schematic import create_thermosolar_schematic

logger = logging.getLogger(__name__)


dash.register_page(__name__, path='/')


def layout():
    """
    Layout simplificado: solo el contenedor del diagrama SVG
    Header, sidebar y footer están en app.py
    """
    return html.Div(
        id='schematic-container',
        style={
            'height': 'calc(100vh - 200px)',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '8px',
            'padding': '20px',
            'border': '1px solid #dee2e6',
            'overflow': 'auto',
            'margin': '10px'
        }
    )


@callback(
    Output('schematic-container', 'children'),
    [
        Input('interval-fast', 'n_intervals'),
        Input('plant-selector', 'value'),
    ],
)
def update_schematic(n_intervals, selected_plant):
    """Actualizar el diagrama esquemático con datos en tiempo real desde PI"""
    try:
        logger.info(f"[update_schematic] Callback triggered: n_intervals={n_intervals}, plant={selected_plant}")

        if not selected_plant:
            logger.warning(f"[cycle_analysis] selected_plant es None o vacío")
            return html.Div(
                "Error: Planta no seleccionada",
                style={"color": "red", "textAlign": "center", "padding": "20px"}
            )

        result = create_thermosolar_schematic(plant=selected_plant)
        logger.debug(f"[cycle_analysis] Diagrama actualizado exitosamente para {selected_plant}")
        return result

    except Exception as e:
        logger.error(f"[cycle_analysis] Error actualizando diagrama: {str(e)}", exc_info=True)
        return html.Div([
            html.H4("Error actualizando diagrama", style={"color": "red", "textAlign": "center"}),
            html.P(str(e), style={"textAlign": "center", "color": "#666"}),
            html.P(f"Planta: {selected_plant}", style={"textAlign": "center", "color": "#999", "fontSize": "12px"})
        ], style={"padding": "20px"})
