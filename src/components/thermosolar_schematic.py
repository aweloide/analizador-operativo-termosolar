#!/usr/bin/env python3
"""
Componente: Diagrama Esquemático de la Planta Termosolar
Visualización del proceso completo con inyección de datos en tiempo real desde PI
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dash import html
import base64
import re
import yaml
import logging
from src.core.pi_data_service import PIDataService
from src.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


# ============================================================================
# FUNCIONES AUXILIARES - Carga de Configuración
# ============================================================================

def _load_config():
    """Carga la configuración desde config.yaml"""
    config_path = Path(__file__).parent.parent.parent / 'config.yaml'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error cargando config.yaml: {str(e)}")
        return {}


def _build_pi_tag_mapping(plant, schematic_config):
    """
    Construye el mapeo dinámico: PI Tag → SVG Element ID
    según la planta seleccionada

    Args:
        plant: Identificador de la planta ('pte1' o 'pte2')
        schematic_config: Configuración de elementos desde config.yaml

    Returns:
        Dict: {pi_tag: svg_element_id}
    """
    pi_tag_mapping = {}

    for element_key, element_config in schematic_config.items():
        # Saltar metadatos
        if element_key in ('enabled', 'description'):
            continue

        tags = element_config.get('tags', {})
        pi_tag = tags.get(plant.lower())
        svg_element_id = element_config.get('svg_element_id')

        if pi_tag and svg_element_id:
            pi_tag_mapping[pi_tag] = svg_element_id
            logger.info(f"Elemento {element_key}: PI Tag '{pi_tag}' → SVG Element '{svg_element_id}'")

    return pi_tag_mapping


def _fetch_temperatures_from_pi(plant, pi_tag_mapping, config_loader):
    """
    Obtiene valores de temperatura usando PIDataService
    Maneja automáticamente la conexión/desconexión según la planta

    Args:
        plant: Identificador de planta ('pte1' o 'pte2')
        pi_tag_mapping: Mapeo de tags PI
        config_loader: Instancia de ConfigLoader

    Returns:
        Dict: {pi_tag: temperatura}
    """
    temperatures = {}

    try:
        # Usar el servicio de datos que gestiona las conexiones exclusivas
        pi_service = PIDataService(config_loader)
        logger.info(f"Obteniendo temperaturas para planta {plant.upper()}...")

        # Asegurar conexión a la planta correcta (desconecta otras si es necesario)
        if pi_service.is_plant_connected(plant):
            logger.info(f"Conectado a {plant.upper()}, obteniendo temperaturas...")

            for pi_tag in pi_tag_mapping.keys():
                try:
                    # Buscar el punto en PI directamente con el conector
                    connector = pi_service.connectors.get(plant)
                    if connector:
                        snapshot = connector.get_snapshot(pi_tag)
                        if snapshot and snapshot.get('value') is not None:
                            temperatures[pi_tag] = snapshot['value']
                            logger.info(f"  {pi_tag}: {snapshot['value']:.1f}°C")
                        else:
                            logger.warning(f"  No se obtuvo snapshot para {pi_tag}")
                            temperatures[pi_tag] = None
                except Exception as tag_error:
                    logger.warning(f"  Error obteniendo {pi_tag}: {str(tag_error)}")
                    temperatures[pi_tag] = None

        else:
            logger.error(f"No se pudo conectar al servidor PI para {plant.upper()}")

    except Exception as e:
        logger.error(f"Error obteniendo temperaturas del PI: {str(e)}")

    return temperatures


def _format_temperatures(pi_tag_mapping, temperatures, schematic_config):
    """
    Formatea las temperaturas según el formato especificado en config.yaml

    Args:
        pi_tag_mapping: Mapeo PI Tag → SVG Element ID
        temperatures: Dict con valores de temperatura
        schematic_config: Configuración de elementos

    Returns:
        Dict: {svg_element_id: valor_formateado}
    """
    formatted_temps = {}

    # Crear mapeo inverso: svg_element_id → element_key
    element_by_id = {}
    for element_key, element_config in schematic_config.items():
        if element_key not in ('enabled', 'description'):
            svg_id = element_config.get('svg_element_id')
            if svg_id:
                element_by_id[svg_id] = element_config

    for pi_tag, svg_element_id in pi_tag_mapping.items():
        temp_value = temperatures.get(pi_tag)
        element_config = element_by_id.get(svg_element_id, {})
        format_str = element_config.get('format', '{value:.1f}°C')

        if temp_value is not None:
            formatted_temps[svg_element_id] = format_str.format(value=temp_value)
        else:
            formatted_temps[svg_element_id] = '--'

    return formatted_temps


def _inject_values_into_svg(svg_content, pi_tag_mapping, formatted_temps):
    """
    Inyecta los valores formateados en el SVG

    Args:
        svg_content: Contenido del SVG como string
        pi_tag_mapping: Mapeo PI Tag → SVG Element ID
        formatted_temps: Temperaturas formateadas

    Returns:
        String: SVG modificado
    """
    for pi_tag, svg_element_id in pi_tag_mapping.items():
        temp_str = formatted_temps[svg_element_id]

        # Patrón regex para encontrar el elemento en el SVG
        element_pattern = rf'(<text[^>]*id=["\']?{re.escape(svg_element_id)}["\']?[^>]*>).*?(<\/text>)'

        if re.search(element_pattern, svg_content, flags=re.DOTALL):
            # El elemento existe, reemplazamos su contenido
            def replace_temp(match):
                return match.group(1) + temp_str + match.group(2)

            svg_content = re.sub(
                element_pattern,
                replace_temp,
                svg_content,
                flags=re.DOTALL
            )
        else:
            # El elemento no existe, lo inyectamos como nuevo
            temp_element = f'''  <text
     id="{svg_element_id}"
     text-anchor="middle"
     font-size="11"
     font-weight="bold"
     fill="#ffffff">
    <tspan>{temp_str}</tspan>
  </text>
'''
            svg_content = svg_content.replace('</svg>', temp_element + '</svg>')

    return svg_content


def _create_svg_container(svg_data_url):
    """Crea el contenedor HTML con el SVG"""
    return html.Div([
        html.Div([
            html.Img(
                id='schematic-svg',
                src=svg_data_url,
                style={
                    'width': '100%',
                    'height': '100%',
                    'margin': '0 auto',
                    'display': 'block',
                    'objectFit': 'contain'
                }
            )
        ], style={
            'textAlign': 'center',
            'width': '100%',
            'height': '100%',
            'minHeight': '700px'
        })
    ], style={
        'width': '100%',
        'height': '100%'
    })


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def create_thermosolar_schematic(plant='pte1'):
    """
    Crea un diagrama esquemático SVG con inyección de datos en tiempo real
    Usa PIDataService para manejar conexiones exclusivas a PI

    Args:
        plant: Identificador de la planta ('pte1' o 'pte2')

    Returns:
        Componente Dash (html.Div con SVG)
    """
    # 1. Cargar configuración
    config_dict = _load_config()
    schematic_config = config_dict.get('schematic_elements', {})

    # 2. Crear ConfigLoader para PIDataService
    try:
        config_loader = ConfigLoader('config.yaml')
    except Exception as e:
        logger.error(f"Error cargando config.yaml: {str(e)}")
        return html.Div(f"Error: No se pudo cargar configuración", style={'color': 'red'})

    # 3. Construir mapeo dinámico
    pi_tag_mapping = _build_pi_tag_mapping(plant, schematic_config)

    if not pi_tag_mapping:
        logger.warning("No se encontraron elementos en schematic_elements")
        return html.Div("Error: No hay elementos configurados", style={'color': 'red'})

    # 4. Cargar SVG
    svg_path = Path(__file__).parent.parent.parent / 'assets' / 'schematic_diagram.svg'

    try:
        if not svg_path.exists():
            logger.error(f"SVG no encontrado en: {svg_path}")
            return html.Div(f"Error: SVG no encontrado", style={'color': 'red'})

        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()

        # 5. Obtener temperaturas de PI usando PIDataService
        # Esto maneja automáticamente desconectar de otras plantas si es necesario
        temperatures = _fetch_temperatures_from_pi(plant, pi_tag_mapping, config_loader)

        # 6. Formatear temperaturas
        formatted_temps = _format_temperatures(pi_tag_mapping, temperatures, schematic_config)

        # 7. Inyectar valores en SVG
        svg_content = _inject_values_into_svg(svg_content, pi_tag_mapping, formatted_temps)

        # 8. Convertir a base64 data URL
        svg_b64 = base64.b64encode(svg_content.encode()).decode()
        svg_data_url = f'data:image/svg+xml;base64,{svg_b64}'

        # 9. Retornar contenedor
        return _create_svg_container(svg_data_url)

    except Exception as e:
        logger.error(f"Error procesando SVG: {str(e)}")
        return html.Div(f"Error: {str(e)}", style={'color': 'red'})


def create_cycle_legend():
    """
    Crea una leyenda explicativa del ciclo personalizado para la planta real
    """
    legend_data = [
        {
            'title': 'Sistema Solar & HTF (6 Intercambiadores)',
            'items': [
                '🌞 1 Campo Solar único',
                '🔴 HTF entrada: 290°C desde colectores',
                '🔴 HTF salida: 390°C a 6 intercambiadores',
                '💨 Función: Transportar energía solar térmica'
            ],
            'color': '#FB8072'
        },
        {
            'title': 'Almacenamiento Térmico (2 Tanques)',
            'items': [
                '🔥 Tanque Caliente: 385°C (máx 550°C)',
                '❄️ Tanque Frío: 225°C (mín 250°C)',
                '📦 Capacidad: ~1.400 MWh térmicos',
                '⏱️ Autonomía: 6-8 horas sin radiación'
            ],
            'color': '#A6005C'
        },
        {
            'title': 'Generación Eléctrica (2 Trenes)',
            'items': [
                '💨 Gen. Vapor 1 & 2: 20-25 MW térmico c/u',
                '⚡ Turbina 1 & 2: Expansión de vapor',
                '🔌 Generador 1 & 2: ~20 MWe c/u',
                '📊 Potencia total nominal: 40-50 MWe'
            ],
            'color': '#377EB8'
        },
        {
            'title': 'Sistemas Auxiliares',
            'items': [
                '🔵 Bomba HTF: Circula aceite térmico',
                '🔴 Bombas Sales Calientes: Desde tanque caliente',
                '🔵 Bombas Sales Frías: Desde tanque frío',
                '❄️ Condensador: Recupera agua de condensado'
            ],
            'color': '#4D8FD9'
        },
    ]

    html_content = '<div style="padding: 20px; background-color: #f9f9f9; border-radius: 8px;">'

    for section in legend_data:
        html_content += f'''
        <h5 style="color: {section['color']}; margin-top: 15px; margin-bottom: 10px;">
            ◆ {section['title']}
        </h5>
        <ul style="margin-left: 20px; font-size: 13px; line-height: 1.6;">
        '''
        for item in section['items']:
            html_content += f'<li>{item}</li>'
        html_content += '</ul>'

    html_content += '</div>'

    return html_content


def create_operation_parameters():
    """
    Retorna un diccionario con los parámetros de operación críticos
    """
    return {
        'solar_radiation': {
            'min': 0,
            'optimal': 500,
            'max': 1000,
            'unit': 'W/m²',
            'description': 'Radiación solar incidente'
        },
        'htf_hot': {
            'min': 280,
            'optimal': 390,
            'max': 400,
            'unit': '°C',
            'description': 'Temperatura HTF caliente'
        },
        'htf_cold': {
            'min': 280,
            'optimal': 290,
            'max': 300,
            'unit': '°C',
            'description': 'Temperatura HTF fría'
        },
        'sales_hot': {
            'min': 250,
            'optimal': 385,
            'max': 550,
            'unit': '°C',
            'description': 'Temperatura sales calientes'
        },
        'sales_cold': {
            'min': 220,
            'optimal': 225,
            'max': 250,
            'unit': '°C',
            'description': 'Temperatura sales frías'
        },
        'vapor_pressure': {
            'min': 80,
            'optimal': 100,
            'max': 120,
            'unit': 'bar',
            'description': 'Presión del vapor'
        },
        'vapor_temp': {
            'min': 350,
            'optimal': 400,
            'max': 420,
            'unit': '°C',
            'description': 'Temperatura del vapor'
        },
        'power_output': {
            'min': 0,
            'optimal': 50,
            'max': 55,
            'unit': 'MWe',
            'description': 'Potencia eléctrica generada'
        },
    }
