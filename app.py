from datetime import datetime
import csv
import io

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)


app = Flask(__name__)
app.secret_key = "cambia-esta-clave"  # Necesaria para mostrar mensajes flash

# Historial en memoria para permitir deshacer la última lectura de código
lecturas_historial = []

# Datos simulados para la demostración de funcionalidades
storage_locations = [
    {
        "nombre": "Gaveta A1",
        "tipo": "Gaveta",
        "created_at": datetime(2024, 1, 10, 10, 30),
    },
    {
        "nombre": "Baldas Zona B",
        "tipo": "Baldas",
        "created_at": datetime(2024, 2, 5, 8, 15),
    },
]

# Registro de asignaciones dinámicas entre líneas de pedidos y gavetas.
# La clave es una tupla (pedido_id, codigo) en minúsculas para evitar duplicados.
gaveta_asignaciones = {}
gaveta_secuencia = 1

inventory_items = [
    {
        "codigo": "ABC123",
        "nombre": "Tornillo M4",
        "cantidad": 150,
        "ubicacion": "Gaveta A1",
    },
    {
        "codigo": "XYZ789",
        "nombre": "Arandela 12mm",
        "cantidad": 60,
        "ubicacion": "Baldas Zona B",
    },
    {
        "codigo": "LMN456",
        "nombre": "Destornillador plano",
        "cantidad": 15,
        "ubicacion": "Gaveta A1",
    },
]

purchase_orders = [
    {
        "id": 5001,
        "cliente": "Electrodomésticos Atlas",
        "fecha": datetime(2024, 3, 8, 9, 45),
        "estado": "Parcial",
        "notas": "Reposición urgente para la línea de montaje principal.",
        "lineas": [
            {
                "codigo": "ABC123",
                "descripcion": "Tornillo M4",
                "cantidad_pedida": 150,
                "cantidad_recibida": 80,
                "cantidad_pendiente": 70,
            },
            {
                "codigo": "LMN456",
                "descripcion": "Destornillador plano",
                "cantidad_pedida": 25,
                "cantidad_recibida": 25,
                "cantidad_pendiente": 0,
            },
        ],
    },
    {
        "id": 5002,
        "cliente": "Solaris Components",
        "fecha": datetime(2024, 3, 15, 14, 10),
        "estado": "Pendiente",
        "notas": "Pedido programado para el nuevo centro logístico.",
        "lineas": [
            {
                "codigo": "XYZ789",
                "descripcion": "Arandela 12mm",
                "cantidad_pedida": 200,
                "cantidad_recibida": 0,
                "cantidad_pendiente": 200,
            },
            {
                "codigo": "OPQ222",
                "descripcion": "Llave Allen 5mm",
                "cantidad_pedida": 60,
                "cantidad_recibida": 20,
                "cantidad_pendiente": 40,
            },
        ],
    },
    {
        "id": 5003,
        "cliente": "Ingeniería Boreal",
        "fecha": datetime(2024, 3, 20, 11, 5),
        "estado": "Completado",
        "notas": "Cierre de proyecto piloto con materiales sobrantes.",
        "lineas": [
            {
                "codigo": "RST987",
                "descripcion": "Taladro inalámbrico",
                "cantidad_pedida": 10,
                "cantidad_recibida": 10,
                "cantidad_pendiente": 0,
            },
            {
                "codigo": "UVW654",
                "descripcion": "Guantes anti corte",
                "cantidad_pedida": 80,
                "cantidad_recibida": 80,
                "cantidad_pendiente": 0,
            },
        ],
    },
]

delivery_notes = [
    {
        "id": 7001,
        "numero": "ALB-2024-001",
        "fecha": datetime(2024, 4, 2, 16, 45),
        "proveedor": "Componentes Boreal",
        "fabrica": "Planta Norte",
        "precio_transporte": 125.0,
        "lineas": [
            {
                "codigo": "ABC123",
                "nombre": "Tornillo M4",
                "tipo": "Fijación",
                "precio_pvo": 0.08,
                "precio_pvp": 0.24,
                "cantidad": 80,
            },
            {
                "codigo": "XYZ789",
                "nombre": "Arandela 12mm",
                "tipo": "Fijación",
                "precio_pvo": 0.04,
                "precio_pvp": 0.15,
                "cantidad": 200,
            },
            {
                "codigo": "OPQ222",
                "nombre": "Llave Allen 5mm",
                "tipo": "Herramienta",
                "precio_pvo": 0.95,
                "precio_pvp": 2.1,
                "cantidad": 35,
            },
        ],
    },
    {
        "id": 7002,
        "numero": "ALB-2024-002",
        "fecha": datetime(2024, 4, 8, 10, 20),
        "proveedor": "Tecno Sur",
        "fabrica": "Centro de Distribución Este",
        "precio_transporte": 210.0,
        "lineas": [
            {
                "codigo": "RST987",
                "nombre": "Taladro inalámbrico",
                "tipo": "Herramienta",
                "precio_pvo": 48.0,
                "precio_pvp": 79.0,
                "cantidad": 12,
            },
            {
                "codigo": "UVW654",
                "nombre": "Guantes anti corte",
                "tipo": "Protección",
                "precio_pvo": 3.2,
                "precio_pvp": 6.5,
                "cantidad": 90,
            },
        ],
    },
    {
        "id": 7003,
        "numero": "ALB-2024-003",
        "fecha": datetime(2024, 4, 18, 9, 5),
        "proveedor": "Logística Atlántico",
        "fabrica": "Planta Central",
        "precio_transporte": 95.0,
        "lineas": [
            {
                "codigo": "LMN456",
                "nombre": "Destornillador plano",
                "tipo": "Herramienta",
                "precio_pvo": 4.5,
                "precio_pvp": 8.9,
                "cantidad": 25,
            },
            {
                "codigo": "ABC123",
                "nombre": "Tornillo M4",
                "tipo": "Fijación",
                "precio_pvo": 0.08,
                "precio_pvp": 0.24,
                "cantidad": 120,
            },
        ],
    },
]


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/crear-gavetas", methods=["GET", "POST"])
def crear_gavetas():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()

        if not nombre or not tipo:
            flash("El nombre y el tipo de la ubicación son obligatorios.", "error")
        else:
            storage_locations.append(
                {
                    "nombre": nombre,
                    "tipo": tipo,
                    "created_at": datetime.now(),
                }
            )
            flash("Ubicación registrada correctamente.", "success")
        return redirect(url_for("crear_gavetas"))

    return render_template("crear_gavetas.html", ubicaciones=storage_locations)


@app.route("/crear-gavetas/<path:nombre>")
def gaveta_detalle(nombre: str):
    ubicacion = next(
        (
            ubicacion
            for ubicacion in storage_locations
            if ubicacion["nombre"].lower() == nombre.lower()
        ),
        None,
    )
    if not ubicacion:
        flash("No se encontró la ubicación solicitada.", "error")
        return redirect(url_for("crear_gavetas"))

    articulos = [
        item
        for item in inventory_items
        if item["ubicacion"].lower() == ubicacion["nombre"].lower()
    ]
    total_unidades = sum(item["cantidad"] for item in articulos)

    return render_template(
        "gaveta_detalle.html",
        ubicacion=ubicacion,
        articulos=articulos,
        total_unidades=total_unidades,
    )


def _lineas_pendientes():
    lineas = []
    for pedido in purchase_orders:
        for linea in pedido["lineas"]:
            if linea["cantidad_pendiente"] > 0:
                lineas.append(
                    {
                        "pedido_id": pedido["id"],
                        "cliente": pedido["cliente"],
                        "codigo": linea["codigo"],
                        "descripcion": linea["descripcion"],
                        "cantidad_pedida": linea["cantidad_pedida"],
                        "cantidad_recibida": linea["cantidad_recibida"],
                        "cantidad_pendiente": linea["cantidad_pendiente"],
                        "fecha": pedido["fecha"],
                    }
                )
    return lineas


def _clave_gaveta(pedido_id: int, codigo: str):
    return (pedido_id, codigo.lower())


def _generar_nombre_gaveta() -> str:
    global gaveta_secuencia
    nombre = f"Gaveta #{gaveta_secuencia}"
    gaveta_secuencia += 1
    return nombre


def _obtener_o_crear_gaveta(pedido: dict, linea: dict):
    clave = _clave_gaveta(pedido["id"], linea["codigo"])
    asignacion = gaveta_asignaciones.get(clave)
    if asignacion:
        return clave, asignacion, False

    nombre = _generar_nombre_gaveta()
    nueva_gaveta = {
        "nombre": nombre,
        "tipo": "Gaveta",
        "created_at": datetime.now(),
    }
    storage_locations.append(nueva_gaveta)
    asignacion = {
        "pedido_id": pedido["id"],
        "cliente": pedido["cliente"],
        "codigo": linea["codigo"],
        "descripcion": linea.get("descripcion") or linea.get("nombre", linea["codigo"]),
        "unidades": 0,
        "gaveta": nueva_gaveta,
    }
    gaveta_asignaciones[clave] = asignacion
    return clave, asignacion, True


def _actualizar_unidades_gaveta(clave, delta: int):
    asignacion = gaveta_asignaciones.get(clave)
    if asignacion:
        asignacion["unidades"] = max(asignacion["unidades"] + delta, 0)
    return asignacion


def _listar_gavetas_activas():
    gavetas = [
        {
            "nombre": asignacion["gaveta"]["nombre"],
            "pedido_id": asignacion["pedido_id"],
            "cliente": asignacion["cliente"],
            "codigo": asignacion["codigo"],
            "descripcion": asignacion["descripcion"],
            "unidades": asignacion["unidades"],
        }
        for asignacion in gaveta_asignaciones.values()
    ]
    return sorted(gavetas, key=lambda gaveta: (gaveta["pedido_id"], gaveta["codigo"].lower()))


def _totales_albaran(albaran):
    total_unidades = sum(linea["cantidad"] for linea in albaran["lineas"])
    total_pvo = sum(linea["precio_pvo"] * linea["cantidad"] for linea in albaran["lineas"])
    total_pvp = sum(linea["precio_pvp"] * linea["cantidad"] for linea in albaran["lineas"])
    return {
        "total_unidades": total_unidades,
        "total_pvo": total_pvo,
        "total_pvp": total_pvp,
    }


def _buscar_linea_por_codigo(codigo: str):
    codigo_lower = codigo.lower()
    pedidos_ordenados = sorted(purchase_orders, key=lambda pedido: pedido["fecha"])
    for pedido in pedidos_ordenados:
        for linea in pedido["lineas"]:
            if linea["codigo"].lower() == codigo_lower and linea["cantidad_pendiente"] > 0:
                return pedido, linea
    return None, None


def _deshacer_ultima_lectura():
    if not lecturas_historial:
        return None

    registro = lecturas_historial.pop()
    linea = registro["linea"]
    if linea["cantidad_recibida"] <= 0:
        return None

    linea["cantidad_recibida"] = max(linea["cantidad_recibida"] - 1, 0)
    linea["cantidad_pendiente"] = min(
        linea["cantidad_pendiente"] + 1, linea["cantidad_pedida"]
    )
    gaveta_key = registro.get("gaveta_key")
    asignacion = _actualizar_unidades_gaveta(gaveta_key, -1) if gaveta_key else None
    if asignacion:
        registro["gaveta"] = asignacion["gaveta"]["nombre"]
        registro["unidades_gaveta"] = asignacion["unidades"]
    return registro


@app.route("/lectura-codigos", methods=["GET", "POST"])
def lectura_codigos():
    resultado = None
    codigo = ""
    if request.method == "POST":
        accion = request.form.get("accion")
        if accion == "deshacer":
            registro = _deshacer_ultima_lectura()
            if registro is None:
                flash("No hay lecturas previas para deshacer.", "warning")
            else:
                flash(
                    f"Se revirtió la última lectura del pedido #{registro['pedido_id']}.",
                    "info",
                )
                resultado = {
                    "pedido_id": registro["pedido_id"],
                    "cliente": registro["cliente"],
                    "linea": registro["linea"],
                    "completado": False,
                    "deshacer": True,
                    "gaveta_creada": False,
                }
                if registro.get("gaveta"):
                    resultado["gaveta"] = registro["gaveta"]
                    resultado["unidades_gaveta"] = registro.get("unidades_gaveta", 0)
        else:
            codigo = request.form.get("codigo", "").strip()
            if not codigo:
                flash("Introduce un código de barras.", "error")
            else:
                pedido, linea = _buscar_linea_por_codigo(codigo)
                if not linea:
                    flash("No hay unidades pendientes para ese código.", "warning")
                else:
                    nueva_cantidad_recibida = min(
                        linea["cantidad_recibida"] + 1, linea["cantidad_pedida"]
                    )
                    linea["cantidad_pendiente"] = max(
                        linea["cantidad_pedida"] - nueva_cantidad_recibida, 0
                    )
                    linea["cantidad_recibida"] = nueva_cantidad_recibida
                    completado = linea["cantidad_pendiente"] == 0
                    gaveta_key, asignacion, gaveta_creada = _obtener_o_crear_gaveta(
                        pedido, linea
                    )
                    _actualizar_unidades_gaveta(gaveta_key, 1)
                    resultado = {
                        "pedido_id": pedido["id"],
                        "cliente": pedido["cliente"],
                        "linea": linea,
                        "completado": completado,
                        "gaveta": asignacion["gaveta"]["nombre"],
                        "unidades_gaveta": asignacion["unidades"],
                        "gaveta_creada": gaveta_creada,
                    }
                    lecturas_historial.append(
                        {
                            "pedido_id": pedido["id"],
                            "cliente": pedido["cliente"],
                            "linea": linea,
                            "gaveta_key": gaveta_key,
                        }
                    )
                    if completado:
                        flash(
                            f"Se completó la línea del código {linea['codigo']} en el pedido #{pedido['id']}.",
                            "success",
                        )
                    else:
                        flash(
                            f"Registrada 1 unidad para el pedido #{pedido['id']}. Pendientes: {linea['cantidad_pendiente']}.",
                            "success",
                        )

    lineas_pendientes = _lineas_pendientes()
    gavetas_activas = _listar_gavetas_activas()
    return render_template(
        "lectura_codigos.html",
        codigo=codigo,
        resultado=resultado,
        lineas_pendientes=lineas_pendientes,
        gavetas_activas=gavetas_activas,
    )


@app.route("/subir-excel", methods=["GET", "POST"])
def subir_excel():
    resumen = None
    if request.method == "POST":
        archivo = request.files.get("archivo")
        if not archivo or archivo.filename == "":
            flash("Selecciona un archivo para subir.", "error")
        elif not archivo.filename.lower().endswith((".xlsx", ".xls", ".csv")):
            flash("Formato no soportado. Usa Excel o CSV.", "error")
        else:
            contenido = archivo.read()
            archivo.seek(0)
            resumen = {
                "nombre": archivo.filename,
                "tamano_kb": round(len(contenido) / 1024, 2),
                "procesado": True,
            }
            flash("Archivo recibido. Procesamiento simulado completado.", "success")

    return render_template("subir_excel.html", resumen=resumen)


@app.route("/subir-excel/plantilla")
def descargar_plantilla_excel():
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["codigo", "nombre", "cantidad", "ubicacion"])
    writer.writerow(["ABC123", "Tornillo M4", 25, "Gaveta A1"])
    writer.writerow(["XYZ789", "Arandela 12mm", 40, "Baldas Zona B"])
    writer.writerow(["LMN456", "Destornillador plano", 5, "Gaveta A1"])

    output = io.BytesIO()
    output.write(csv_buffer.getvalue().encode("utf-8"))
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="plantilla_carga_inventario.csv",
        mimetype="text/csv",
    )


@app.route("/exportar-informes")
def exportar_informes():
    total_items = len(inventory_items)
    total_unidades = sum(item["cantidad"] for item in inventory_items)
    return render_template(
        "exportar_informes.html",
        total_items=total_items,
        total_unidades=total_unidades,
    )


@app.route("/exportar-informes/descargar")
def descargar_informe():
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Código", "Nombre", "Cantidad", "Ubicación"])
    for item in inventory_items:
        writer.writerow([item["codigo"], item["nombre"], item["cantidad"], item["ubicacion"]])

    output = io.BytesIO()
    output.write(csv_buffer.getvalue().encode("utf-8"))
    output.seek(0)
    filename = f"informe_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/buscar-articulos")
def buscar_articulos():
    termino = request.args.get("q", "").strip()
    resultados = []
    if termino:
        termino_lower = termino.lower()
        resultados = [
            item
            for item in inventory_items
            if termino_lower in item["nombre"].lower()
            or termino_lower in item["codigo"].lower()
        ]
        if resultados:
            flash(f"Se encontraron {len(resultados)} coincidencias.", "success")
        else:
            flash("No se encontraron artículos con ese criterio.", "warning")

    return render_template("buscar_articulos.html", termino=termino, resultados=resultados)


@app.route("/mostrar-stock")
def mostrar_stock():
    return render_template("mostrar_stock.html", inventario=inventory_items)


@app.route("/panel-control")
def panel_control():
    total_articulos = len(inventory_items)
    total_unidades = sum(item["cantidad"] for item in inventory_items)
    ubicaciones_registradas = len(storage_locations)
    bajo_stock = [item for item in inventory_items if item["cantidad"] < 20]

    ubicaciones_recientes = sorted(
        storage_locations, key=lambda ubicacion: ubicacion["created_at"], reverse=True
    )[:5]

    return render_template(
        "panel_control.html",
        total_articulos=total_articulos,
        total_unidades=total_unidades,
        ubicaciones_registradas=ubicaciones_registradas,
        bajo_stock=bajo_stock,
        ubicaciones_recientes=ubicaciones_recientes,
    )


@app.route("/pedidos", methods=["GET", "POST"])
def pedidos():
    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        codigo = request.form.get("codigo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        cantidad = request.form.get("cantidad", type=int)

        if not cliente or not codigo or not descripcion or cantidad is None or cantidad <= 0:
            flash("Completa todos los datos del pedido con cantidades válidas.", "error")
        else:
            nuevo_id = max((pedido["id"] for pedido in purchase_orders), default=5000) + 1
            nueva_linea = {
                "codigo": codigo,
                "descripcion": descripcion,
                "cantidad_pedida": cantidad,
                "cantidad_recibida": 0,
                "cantidad_pendiente": cantidad,
            }
            nuevo_pedido = {
                "id": nuevo_id,
                "cliente": cliente,
                "fecha": datetime.now(),
                "estado": "Pendiente",
                "notas": "Creado manualmente desde la pantalla de pedidos.",
                "lineas": [nueva_linea],
            }
            purchase_orders.append(nuevo_pedido)
            flash(f"Pedido #{nuevo_id} registrado correctamente.", "success")
        return redirect(url_for("pedidos"))

    total_lineas = sum(len(pedido["lineas"]) for pedido in purchase_orders)
    total_unidades_pedidas = sum(
        sum(linea["cantidad_pedida"] for linea in pedido["lineas"])
        for pedido in purchase_orders
    )
    total_unidades_pendientes = sum(
        sum(linea["cantidad_pendiente"] for linea in pedido["lineas"])
        for pedido in purchase_orders
    )
    pedidos_abiertos = sum(
        1
        for pedido in purchase_orders
        if any(linea["cantidad_pendiente"] > 0 for linea in pedido["lineas"])
    )

    return render_template(
        "pedidos.html",
        pedidos=purchase_orders,
        total_lineas=total_lineas,
        total_unidades_pedidas=total_unidades_pedidas,
        total_unidades_pendientes=total_unidades_pendientes,
        pedidos_abiertos=pedidos_abiertos,
    )


@app.route("/pedidos/<int:pedido_id>")
def pedido_detalle(pedido_id: int):
    pedido = next((pedido for pedido in purchase_orders if pedido["id"] == pedido_id), None)
    if not pedido:
        flash("No se encontró el pedido solicitado.", "error")
        return redirect(url_for("pedidos"))

    total_solicitado = sum(linea["cantidad_pedida"] for linea in pedido["lineas"])
    total_recibido = sum(linea["cantidad_recibida"] for linea in pedido["lineas"])
    total_pendiente = sum(linea["cantidad_pendiente"] for linea in pedido["lineas"])

    return render_template(
        "pedido_detalle.html",
        pedido=pedido,
        total_solicitado=total_solicitado,
        total_recibido=total_recibido,
        total_pendiente=total_pendiente,
    )


@app.route("/albaranes")
def albaranes():
    albaranes_ordenados = sorted(delivery_notes, key=lambda albaran: albaran["fecha"], reverse=True)
    albaranes_enriquecidos = []
    for albaran in albaranes_ordenados:
        totales = _totales_albaran(albaran)
        albaranes_enriquecidos.append({**albaran, **totales})

    totales_generales = {
        "total_albaranes": len(delivery_notes),
        "unidades_recibidas": sum(_totales_albaran(albaran)["total_unidades"] for albaran in delivery_notes),
        "valor_pvo": sum(_totales_albaran(albaran)["total_pvo"] for albaran in delivery_notes),
        "valor_pvp": sum(_totales_albaran(albaran)["total_pvp"] for albaran in delivery_notes),
    }

    return render_template(
        "albaranes.html",
        albaranes=albaranes_enriquecidos,
        totales_generales=totales_generales,
    )


@app.route("/albaranes/<int:albaran_id>")
def albaran_detalle(albaran_id: int):
    albaran = next((nota for nota in delivery_notes if nota["id"] == albaran_id), None)
    if not albaran:
        flash("No se encontró el albarán solicitado.", "error")
        return redirect(url_for("albaranes"))

    totales = _totales_albaran(albaran)

    return render_template(
        "albaran_detalle.html",
        albaran=albaran,
        totales=totales,
    )


if __name__ == "__main__":
    app.run(debug=True)