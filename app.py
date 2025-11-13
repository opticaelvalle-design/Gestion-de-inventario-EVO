 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
new file mode 100644
index 0000000000000000000000000000000000000000..4736000313d2d4431e143f6fec53177699b7b7ef
--- /dev/null
+++ b/app.py
@@ -0,0 +1,206 @@
+from datetime import datetime
+import csv
+import io
+
+from flask import (
+    Flask,
+    flash,
+    redirect,
+    render_template,
+    request,
+    send_file,
+    url_for,
+)
+
+
+app = Flask(__name__)
+app.secret_key = "cambia-esta-clave"  # Necesaria para mostrar mensajes flash
+
+# Datos simulados para la demostración de funcionalidades
+storage_locations = [
+    {
+        "nombre": "Gaveta A1",
+        "tipo": "Gaveta",
+        "capacidad": 200,
+        "created_at": datetime(2024, 1, 10, 10, 30),
+    },
+    {
+        "nombre": "Baldas Zona B",
+        "tipo": "Baldas",
+        "capacidad": 120,
+        "created_at": datetime(2024, 2, 5, 8, 15),
+    },
+]
+
+inventory_items = [
+    {
+        "codigo": "ABC123",
+        "nombre": "Tornillo M4",
+        "cantidad": 150,
+        "ubicacion": "Gaveta A1",
+    },
+    {
+        "codigo": "XYZ789",
+        "nombre": "Arandela 12mm",
+        "cantidad": 60,
+        "ubicacion": "Baldas Zona B",
+    },
+    {
+        "codigo": "LMN456",
+        "nombre": "Destornillador plano",
+        "cantidad": 15,
+        "ubicacion": "Gaveta A1",
+    },
+]
+
+
+@app.route("/")
+def home():
+    return render_template("index.html")
+
+
+@app.route("/crear-gavetas", methods=["GET", "POST"])
+def crear_gavetas():
+    if request.method == "POST":
+        nombre = request.form.get("nombre", "").strip()
+        tipo = request.form.get("tipo", "").strip()
+        capacidad = request.form.get("capacidad", type=int)
+
+        if not nombre or not tipo or capacidad is None:
+            flash("Todos los campos son obligatorios.", "error")
+        else:
+            storage_locations.append(
+                {
+                    "nombre": nombre,
+                    "tipo": tipo,
+                    "capacidad": capacidad,
+                    "created_at": datetime.now(),
+                }
+            )
+            flash("Ubicación registrada correctamente.", "success")
+        return redirect(url_for("crear_gavetas"))
+
+    return render_template("crear_gavetas.html", ubicaciones=storage_locations)
+
+
+@app.route("/leer-codigos-de-barras", methods=["GET", "POST"])
+def leer_codigos_de_barras():
+    resultado = None
+    if request.method == "POST":
+        codigo = request.form.get("codigo", "").strip()
+        if not codigo:
+            flash("Introduce un código de barras.", "error")
+        else:
+            resultado = next(
+                (item for item in inventory_items if item["codigo"].lower() == codigo.lower()),
+                None,
+            )
+            if resultado:
+                flash("Artículo encontrado.", "success")
+            else:
+                flash("No se encontró ningún artículo con ese código.", "warning")
+
+    return render_template("leer_codigos.html", resultado=resultado)
+
+
+@app.route("/subir-excel", methods=["GET", "POST"])
+def subir_excel():
+    resumen = None
+    if request.method == "POST":
+        archivo = request.files.get("archivo")
+        if not archivo or archivo.filename == "":
+            flash("Selecciona un archivo para subir.", "error")
+        elif not archivo.filename.lower().endswith((".xlsx", ".xls", ".csv")):
+            flash("Formato no soportado. Usa Excel o CSV.", "error")
+        else:
+            contenido = archivo.read()
+            archivo.seek(0)
+            resumen = {
+                "nombre": archivo.filename,
+                "tamano_kb": round(len(contenido) / 1024, 2),
+                "procesado": True,
+            }
+            flash("Archivo recibido. Procesamiento simulado completado.", "success")
+
+    return render_template("subir_excel.html", resumen=resumen)
+
+
+@app.route("/exportar-informes")
+def exportar_informes():
+    total_items = len(inventory_items)
+    total_unidades = sum(item["cantidad"] for item in inventory_items)
+    return render_template(
+        "exportar_informes.html",
+        total_items=total_items,
+        total_unidades=total_unidades,
+    )
+
+
+@app.route("/exportar-informes/descargar")
+def descargar_informe():
+    csv_buffer = io.StringIO()
+    writer = csv.writer(csv_buffer)
+    writer.writerow(["Código", "Nombre", "Cantidad", "Ubicación"])
+    for item in inventory_items:
+        writer.writerow([item["codigo"], item["nombre"], item["cantidad"], item["ubicacion"]])
+
+    output = io.BytesIO()
+    output.write(csv_buffer.getvalue().encode("utf-8"))
+    output.seek(0)
+    filename = f"informe_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
+    return send_file(
+        output,
+        mimetype="text/csv",
+        as_attachment=True,
+        download_name=filename,
+    )
+
+
+@app.route("/buscar-articulos")
+def buscar_articulos():
+    termino = request.args.get("q", "").strip()
+    resultados = []
+    if termino:
+        termino_lower = termino.lower()
+        resultados = [
+            item
+            for item in inventory_items
+            if termino_lower in item["nombre"].lower()
+            or termino_lower in item["codigo"].lower()
+        ]
+        if resultados:
+            flash(f"Se encontraron {len(resultados)} coincidencias.", "success")
+        else:
+            flash("No se encontraron artículos con ese criterio.", "warning")
+
+    return render_template("buscar_articulos.html", termino=termino, resultados=resultados)
+
+
+@app.route("/mostrar-stock")
+def mostrar_stock():
+    return render_template("mostrar_stock.html", inventario=inventory_items)
+
+
+@app.route("/panel-control")
+def panel_control():
+    total_articulos = len(inventory_items)
+    total_unidades = sum(item["cantidad"] for item in inventory_items)
+    ubicaciones_registradas = len(storage_locations)
+    bajo_stock = [item for item in inventory_items if item["cantidad"] < 20]
+
+    ubicaciones_recientes = sorted(
+        storage_locations, key=lambda ubicacion: ubicacion["created_at"], reverse=True
+    )[:5]
+
+    return render_template(
+        "panel_control.html",
+        total_articulos=total_articulos,
+        total_unidades=total_unidades,
+        ubicaciones_registradas=ubicaciones_registradas,
+        bajo_stock=bajo_stock,
+        ubicaciones_recientes=ubicaciones_recientes,
+    )
+
+
+if __name__ == "__main__":
+    app.run(debug=True)
 
EOF
)
