#!/usr/bin/env python3
"""
Componente Footer
Renderiza indicadores de ambas plantas como tabla: Energía Día/Mes + otros indicadores
"""

from dash import html


def create_footer() -> html.Div:
    """
    Crea el footer con indicadores de PTE1 y PTE2 en formato tabla

    Layout:
    ┌─────────┬─────────────────┬─────────────────┬──────────┬─────────┬─────────┬──────────┬─────────────┬────────────┐
    │ Planta  │ Energía Día     │ Energía Mes     │ Tracking │ TFollow │ PFollow │ Temp>395 │ Rendimiento │
    ├─────────┼─────────────────┼─────────────────┼──────────┼─────────┼─────────┼──────────┼─────────────┼────────────┤
    │ PTE1    │ XXX.XX MWh      │ XXX.XX MWh      │    --    │   --    │   --    │  -- min  │     --%     │
    ├─────────┼─────────────────┼─────────────────┼──────────┼─────────┼─────────┼──────────┼─────────────┼────────────┤
    │ PTE2    │ XXX.XX MWh      │ XXX.XX MWh      │    --    │   --    │   --    │  -- min  │     --%     │
    └─────────┴─────────────────┴─────────────────┴──────────┴─────────┴─────────┴──────────┴─────────────┴────────────┘

    Returns:
        html.Div con estructura de tabla limpia y compacta
    """

    # Estilos para la tabla
    header_cell_style = {
        "padding": "8px 12px",
        "backgroundColor": "#1e3a5f",
        "color": "#ffffff",
        "fontSize": "0.85rem",
        "fontWeight": "600",
        "textAlign": "center",
        "borderRight": "1px solid #155a8a",
        "whiteSpace": "nowrap",
    }

    body_cell_style = {
        "padding": "8px 12px",
        "fontSize": "0.9rem",
        "textAlign": "center",
        "borderRight": "1px solid #dee2e6",
        "borderBottom": "1px solid #dee2e6",
        "minWidth": "100px",
    }

    plant_cell_style = {
        **body_cell_style,
        "fontWeight": "600",
        "backgroundColor": "#f8f9fa",
        "minWidth": "60px",
    }

    return html.Div([
        html.Table([
            # Header
            html.Thead([
                html.Tr([
                    html.Th("Planta", style={**header_cell_style, "minWidth": "60px"}),
                    html.Th("Energía Día", style={**header_cell_style, "minWidth": "130px"}),
                    html.Th("Energía Mes", style={**header_cell_style, "minWidth": "130px"}),
                    html.Th("Índice Tracking", style={**header_cell_style, "minWidth": "110px"}),
                    html.Th("TFollow", style={**header_cell_style, "minWidth": "90px"}),
                    html.Th("PFollow", style={**header_cell_style, "minWidth": "90px"}),
                    html.Th("Minutos >395°C", style={**header_cell_style, "minWidth": "110px"}),
                    html.Th("Rendimiento", style={**header_cell_style, "borderRight": "none", "minWidth": "100px"}),
                ])
            ]),
            # Body
            html.Tbody([
                # Fila PTE1
                html.Tr([
                    html.Td("PTE1", style=plant_cell_style),
                    html.Td(
                        "-- MWh",
                        id="indicator-energy-day-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "-- MWh",
                        id="indicator-energy-month-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-tracking-index-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-tfollow-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-pfollow-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "-- min",
                        id="indicator-minutes-high-temp-pte1",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--%",
                        id="indicator-efficiency-pte1",
                        style={**body_cell_style, "borderRight": "none"}
                    ),
                ]),
                # Fila PTE2
                html.Tr([
                    html.Td("PTE2", style=plant_cell_style),
                    html.Td(
                        "-- MWh",
                        id="indicator-energy-day-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "-- MWh",
                        id="indicator-energy-month-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-tracking-index-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-tfollow-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--",
                        id="indicator-pfollow-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "-- min",
                        id="indicator-minutes-high-temp-pte2",
                        style=body_cell_style
                    ),
                    html.Td(
                        "--%",
                        id="indicator-efficiency-pte2",
                        style={**body_cell_style, "borderRight": "none"}
                    ),
                ]),
            ]),
        ], style={
            "width": "100%",
            "borderCollapse": "collapse",
            "backgroundColor": "#ffffff",
            "fontSize": "0.9rem",
        }),
    ], id="footer-indicators", style={
        "position": "fixed",
        "bottom": "0",
        "left": "0",
        "width": "100%",
        "height": "auto",
        "backgroundColor": "#ffffff",
        "borderTop": "3px solid #1e3a5f",
        "boxShadow": "0 -2px 10px rgba(0,0,0,0.1)",
        "overflowX": "auto",
        "overflowY": "hidden",
        "padding": "0",
        "zIndex": "100",
    })
