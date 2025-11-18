# Gestión de Inventario EVO

Aplicación de demostración construida con [Flask](https://flask.palletsprojects.com/) para gestionar tareas básicas de inventario desde un panel web único.

## Características
- Registro de nuevas ubicaciones físicas (gavetas, baldas y cajones).
- Lectura de códigos de barras que descuenta unidades pendientes del primer pedido abierto.
- Subida de ficheros Excel o CSV para procesamientos masivos simulados.
- Exportación de informes CSV con el estado del stock.
- Buscador de artículos por nombre o código.
- Listado general del inventario con cantidades y ubicaciones.
- Panel de control con indicadores clave (unidades totales, ubicaciones recientes, alertas por bajo stock).

## Requisitos previos
- Python 3.10 o superior instalado en el sistema.
- (Opcional) Entorno virtual creado con `python -m venv venv` y activado.

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

## Ejecución
Inicia el servidor de desarrollo ejecutando:

```bash
flask --app app run --debug
```

o bien:

```bash
python app.py
```

La aplicación estará disponible en `http://127.0.0.1:5000/`.

## Datos de demostración
El archivo `app.py` incluye datos simulados de ubicaciones y artículos para probar la interfaz sin necesidad de una base de datos. Puedes modificar las listas `storage_locations` e `inventory_items` para adaptar la demo a tus necesidades.

## Estructura del proyecto
```
Gestion-de-inventario-EVO/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── buscar_articulos.html
│   ├── crear_gavetas.html
│   ├── exportar_informes.html
│   ├── index.html
│   ├── lectura_codigos.html
│   ├── mostrar_stock.html
│   ├── panel_control.html
│   ├── pedido_detalle.html
│   ├── pedidos.html
│   └── subir_excel.html
└── README.md
```

## Próximos pasos sugeridos
- Conectar una base de datos real (por ejemplo, SQLite o PostgreSQL) mediante SQLAlchemy.
- Añadir autenticación de usuarios y control de permisos por rol.
- Implementar subida real de ficheros Excel usando bibliotecas como `pandas` u `openpyxl`.
- Integrar un sistema de notificaciones por correo o mensajería cuando se detecte bajo stock.

## Pruebas
Para comprobar rápidamente que la aplicación no tiene errores de sintaxis se puede ejecutar:

```bash
python -m compileall app.py
```

Esto genera los bytecode temporales en `__pycache__` y verifica que todo el código de Flask compila correctamente.
