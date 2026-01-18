# DIRECTRICES.md

## 1. Propósito del Proyecto
El Analizador Operativo es una plataforma de monitoreo en tiempo real para varias plantas de energía termosolar (en principio comenzaremos con PTE1 y PTE2, pero posteriormente puede que se expanda a más plantas). Su función es visualizar el estado actual de las instalaciones mostrando datos en reales en  un diagrama SVG y varios indicadores que se actualizan cada 5 segundos desde unos servidores PI (OSIsoft PI Data Archive).
La estructutra de la plataforma debe contener:
  - Un panel central que muestre el diagrama del proceso termosolar, donde se puedan mostrar datos importados de PI y calculados.
  - Una barra lateral a la izquierda donde se pueda seleccionar la planta a monitorear (PTE1 / PTE2), el estado de las conexiones con el servidor de la planta seleccionada y un selector de configuración (config.yaml).
  - Un encabezado pequeño con el nombre del proyecto, el logo de SOLCLEF y una barra de pestañas para futuras ampliaciones.
  - Un pié de página donde aparezca una seri de indicadores, como por ejemplo:
      - El acumulado de energía producida por planta (PTE1 y PTE2) en el día actual.
      - El acumulado de energía producida por planta (PTE1 y PTE2) en el mes actual.
      - El índice de tracking de la planta del día en curso de la planta seleccionada.
      - El número de movimientos a TFollow de la planta seleccionada.
      - El número de movimientos a PFollow de la planta seleccionada.
      - El número de minutos de operación con SCAs por encima de 395ºC de la planta seleccionada.
      - El rendimiento actual de la planta seleccionada.
Para todo ello es necesario desarrollar:
  - Una función que importe los datos de PI Data Archive en tiempo real o históricos.
  - Una función que realice cálculos termodinámicos del agua/vapor, del HTF y las sales. Densidad, calor específico, entalpía, rendimiento de plantas, etc.
  - Una función que actualice los datos en la interfaz gráfica. 
El desarrollo debe ser realizado en Python y debe utilizar la librería Dash para la creación de la interfaz gráfica. En paralelo, se están desarrollando otros proyectos, como la calculadora de Índice de Tracking, que incluiremos en el dashboard.

## 2. Principios de Desarrollo
- **Simplicidad primero**: Elige la solución más simple que funcione. 
- **Una responsabilidad por función**: Cada función hace UNA cosa bien.
- **Documentación concisa**: Genera documentación de forma escueta y sólo cuando el usuario te lo pida. Pregunta cuando creas que es necesario documentar. 
- **Pruebas antes de producción**: Verifica que funciona ANTES de subir cambios.
- **Cambios pequeños y frecuentes**: Mejor 10 cambios pequeños que 1 gigante.
- **Código legible > código ingenioso**: Otros deben entender tu código sin ayuda.
- **Gestionar errores siempre**: Anticipa qué puede fallar.
- **No hard-codear valores**: Nunca escribas valores fijos en el código.
- **No ignorar errores**: Nunca hagas `try: ... except: pass`
- **No duplicar código**: Si repites una lógica, extrae una función.
- **No modificar archivos ajenos sin avisar**: Si tocas código de otro, comunica.
- **No commitear código roto**: Solo sube cambios que funcionan.
- **No agregar features sin plan**: Cada cambio debe tener un propósito.
- **No usar variables con nombres genéricos**: Nombres descriptivos siempre.

## 3. Comportamiento del Modelo IA
- **Eres asistente técnico, no jefe de proyecto**: Propones soluciones, no impones decisiones.
- **Explica siempre tu razonamiento**: El usuario debe entender POR QUÉ sugieres algo.
- **Respeta las directrices del proyecto**: Si el usuario define una regla, síguelas siempre.
- **Reconoce cuando no sabes**: Es mejor decir "no sé" que inventar.
- **Primero lee, luego actúa**: Antes de modificar un archivo, entiende su contexto.
- **Pregunta si hay ambigüedad**: No asumas interpretaciones.
- **Proporciona opciones cuando hay caminos diferentes**: Déja al usuario elegir.
- **Mantén el contexto del proyecto**: Recuerda DIRECTRICES.md
- **Sé pragmático, no perfeccionista**: A veces "bueno" es suficiente.
- **No hagas cambios sin confirmación**: Siempre pregunta antes de actuar
- **No ignores errores del usuario**: Señala problemas, no los ocultes.
- **No simplifiques excesivamente**: A veces la complejidad es necesaria.
- **No asumas conocimiento técnico del usuario**: Explica conceptos claramente.
