#!/usr/bin/env python3
"""
Componente Header
Renderiza el header compacto con logo, título y navegación
"""

import dash_bootstrap_components as dbc
from dash import html


def create_header() -> dbc.Navbar:
    """
    Crea el header principal de la aplicación

    Returns:
        dbc.Navbar con estructura: [Hamburguesa | Título | Tabs]
    """
    return dbc.Navbar(
        dbc.Container([
            # Botón hamburguesa para toggle sidebar
            dbc.Button(
                "☰",
                id="sidebar-toggle",
                outline=True,
                color="light",
                size="lg",
                style={"marginRight": "20px"}
            ),

            # Logo SOLCLEF
            html.Img(
                src="/assets/logo_solclef.png",
                height="50px",
                style={"marginRight": "15px"}
            ),

            # Título principal
            html.H4(
                "Analizador Operativo",
                className="ms-2 text-white",
                style={"margin": 0, "flex": "1"}
            ),

            # Tabs de navegación (placeholder para futuro)
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Ciclo Actual", href="/", active=True)),
                dbc.NavItem(dbc.NavLink("Históricos", href="#", disabled=True)),
                dbc.NavItem(dbc.NavLink("Comparación", href="#", disabled=True)),
            ], navbar=True, className="ms-auto"),

        ], fluid=True, style={"display": "flex", "alignItems": "center"}),
        color="dark",
        dark=True,
        className="mb-2",
        sticky="top"
    )
