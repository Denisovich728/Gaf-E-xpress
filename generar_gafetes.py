import csv
import os
import re
from xml.sax.saxutils import escape as xml_escape


def extract_and_process_svg(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remover declaracion XML y DOCTYPE para poder inyectarlo limpiamente
    content = re.sub(r'<\?xml.*?\?>', '', content, flags=re.DOTALL)
    content = re.sub(r'<!DOCTYPE.*?>', '', content, flags=re.DOTALL)

    # Buscar el bloque principal <svg> ... </svg>
    match_svg = re.search(r'<svg[^>]*>(.*?)</svg>', content, flags=re.IGNORECASE | re.DOTALL)
    if not match_svg:
        raise ValueError("No se encontro contenido SVG valido en el archivo.")

    inner_content = match_svg.group(1)

    # Filtro Chroma Blanco y Negro:
    # Reemplazar todos los colores HEX (#FFFFFF) o RGB por Negro (#000000)
    # Esto preserva inteligentemente "fill: none" y transparencias nativas del vector
    inner_content = re.sub(r'#[0-9a-fA-F]{3,6}', '#000000', inner_content)
    inner_content = re.sub(r'rgba?\([^)]+\)', '#000000', inner_content)

    # Intentar obtener el ViewBox original para escalar correctamente
    viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', content, flags=re.IGNORECASE)
    width_match = re.search(r'\bwidth=["\']([^"\']+)["\']', content, flags=re.IGNORECASE)
    height_match = re.search(r'\bheight=["\']([^"\']+)["\']', content, flags=re.IGNORECASE)

    vb_x, vb_y, vb_w, vb_h = 0, 0, 100, 100
    if viewbox_match:
        parts = viewbox_match.group(1).replace(',', ' ').split()
        if len(parts) >= 4:
            vb_x, vb_y, vb_w, vb_h = map(float, parts[:4])
    elif width_match and height_match:
        try:
            vb_w = float(re.sub(r'[^\d.]', '', width_match.group(1)))
            vb_h = float(re.sub(r'[^\d.]', '', height_match.group(1)))
        except ValueError:
            pass

    return inner_content, vb_x, vb_y, vb_w, vb_h


def sanitizar_nombre_archivo(texto):
    limpio = re.sub(r'[<>:"/\\|?*]', '', texto.strip().lower())
    return re.sub(r'\s+', ' ', limpio)


def obtener_carpeta_salida(ruta_vector):
    sufijo_svg = os.path.splitext(os.path.basename(ruta_vector))[0]
    sufijo_limpio = sanitizar_nombre_archivo(sufijo_svg) or "svg"
    carpeta = os.path.join(os.getcwd(), f"Gafetes_{sufijo_limpio}")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta


def crear_gafete_svg(nombre, puesto, ruta_vector, salida=None):
    # Validaciones
    if not ruta_vector.lower().endswith('.svg'):
        raise ValueError("El archivo de logo debe tener extension '.svg'.")

    if not os.path.exists(ruta_vector):
        raise FileNotFoundError(f"No se encontro el archivo de logo: {ruta_vector}")

    carpeta_salida = obtener_carpeta_salida(ruta_vector)
    if not salida:
        nombre_limpio = sanitizar_nombre_archivo(nombre)
        puesto_limpio = sanitizar_nombre_archivo(puesto)
        nombre_archivo = f"gafete {nombre_limpio} {puesto_limpio}.svg".strip()
        ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
    else:
        ruta_salida = os.path.join(carpeta_salida, os.path.basename(salida))

    # Medidas Fisicas: 4.5 cm x 1.5 cm
    ancho_cm = 4.5
    alto_cm = 1.5

    # ViewBox interno del Gafete (450x150 para coordenadas de fuente)
    canvas_w = 450
    canvas_h = 150

    logo_content, vb_x, vb_y, vb_w, vb_h = extract_and_process_svg(ruta_vector)

    # Calculo de Maquetacion del Logo
    logo_target_size = 120
    margen_x = 15
    margen_y = 15

    if vb_h == 0 or vb_w == 0:
        vb_w, vb_h = 100, 100
    scale_factor = logo_target_size / max(vb_w, vb_h)

    pos_x = margen_x - (vb_x * scale_factor)
    pos_y = margen_y - (vb_y * scale_factor) + (logo_target_size - (vb_h * scale_factor)) / 2

    transform_logo = f"translate({pos_x}, {pos_y}) scale({scale_factor})"

    # Calculo de Maquetacion del Texto
    fin_logo_x = margen_x + (vb_w * scale_factor)
    if fin_logo_x < 100:
        fin_logo_x = 135

    espacio_texto = canvas_w - fin_logo_x - margen_x
    centro_texto_x = fin_logo_x + (espacio_texto / 2)

    size_nombre = 28
    size_puesto = 14

    nombre_seguro = xml_escape(nombre.strip())
    puesto_seguro = xml_escape(puesto.strip())

    svg_template = f"""<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" width="{ancho_cm}cm" height="{alto_cm}cm">
    <defs>
        <style>
            /* Estilos de Textos */
            .nombre {{
                font-family: Arial, sans-serif;
                font-size: {size_nombre}px;
                font-weight: bold;
                fill: black;
                text-anchor: middle;
            }}
            .puesto {{
                font-family: Arial, sans-serif;
                font-size: {size_puesto}px;
                fill: black;
                text-anchor: middle;
            }}
        </style>
    </defs>
    
    <!-- Contenedor del Logo Procesado (Izquierda) -->
    <g class="logo-group" transform="{transform_logo}">
        {logo_content}
    </g>
    
    <!-- Contenedor del Texto (Derecha) -->
    <g>
        <text x="{centro_texto_x}" y="80" class="nombre">{nombre_seguro}</text>
        <text x="{centro_texto_x}" y="105" class="puesto">{puesto_seguro}</text>
    </g>
</svg>
"""

    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(svg_template)

    return ruta_salida, ancho_cm, alto_cm


def seleccionar_archivo_actual(extension, descripcion):
    carpeta_actual = os.getcwd()
    archivos = sorted(
        f for f in os.listdir(carpeta_actual)
        if os.path.isfile(os.path.join(carpeta_actual, f)) and f.lower().endswith(extension.lower())
    )

    while True:
        print(f"\nCarpeta actual: {carpeta_actual}")
        if archivos:
            print(f"Archivos {extension} encontrados ({descripcion}):")
            for idx, nombre_archivo in enumerate(archivos, start=1):
                print(f"  {idx}. {nombre_archivo}")
            print("  0. Ingresar ruta manual")
            print("  V. Volver")

            seleccion = input("Seleccione una opcion: ").strip()
            if seleccion.lower() == 'v':
                return None
            if seleccion == '0':
                ruta_manual = input(f"Ingrese la ruta del {descripcion}: ").strip().strip('"')
                if not ruta_manual:
                    continue
                if os.path.exists(ruta_manual):
                    return ruta_manual
                print(f"[!] ERROR: No se encontro el archivo: {ruta_manual}")
                continue
            if seleccion.isdigit():
                indice = int(seleccion)
                if 1 <= indice <= len(archivos):
                    return os.path.join(carpeta_actual, archivos[indice - 1])
            print("[!] Opcion no valida.")
        else:
            print(f"No se encontraron archivos {extension} en la carpeta actual.")
            ruta_manual = input(f"Ingrese la ruta del {descripcion} (o Enter para volver): ").strip().strip('"')
            if not ruta_manual:
                return None
            if os.path.exists(ruta_manual):
                return ruta_manual
            print(f"[!] ERROR: No se encontro el archivo: {ruta_manual}")


def modo_general():
    print("\n--- Modo General (Gafete Individual) ---")
    ruta_vector = seleccionar_archivo_actual(".svg", "logo SVG")
    if not ruta_vector:
        return

    nombre = input("Ingrese el Nombre: ").strip()
    puesto = input("Ingrese el Puesto: ").strip()

    if not nombre or not puesto:
        print("[!] ERROR: Nombre y Puesto son obligatorios.")
        return

    try:
        ruta_salida, ancho_cm, alto_cm = crear_gafete_svg(nombre, puesto, ruta_vector)
        print(f"\nGafete Vectorial creado con exito: {ruta_salida}")
        print(f"Medidas fisicas: {ancho_cm}cm x {alto_cm}cm (Calidad Maxima Imprenta)")
    except Exception as e:
        print(f"[!] ERROR al generar gafete: {e}")


def imprimir_plantilla_csv():
    ruta_plantilla = os.path.join(os.getcwd(), "plantilla_gafetes.csv")
    filas = [
        ["nombre", "puesto"],
        ["Juan Perez", "Gerente"],
        ["Maria Lopez", "Cajera"],
    ]

    with open(ruta_plantilla, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(filas)

    print(f"\nPlantilla CSV generada en: {ruta_plantilla}")
    print("Contenido de la plantilla:")
    for fila in filas:
        print(",".join(fila))


def leer_registros_csv(ruta_csv):
    encodings = ['utf-8-sig', 'latin-1']
    contenido = None
    encoding_usado = None

    for enc in encodings:
        try:
            with open(ruta_csv, 'r', encoding=enc) as f:
                contenido = f.read()
            encoding_usado = enc
            break
        except UnicodeDecodeError:
            continue

    if contenido is None:
        raise ValueError("No se pudo decodificar el archivo CSV.")

    try:
        dialecto = csv.Sniffer().sniff(contenido[:2048], delimiters=',;')
        delimitador = dialecto.delimiter
    except csv.Error:
        delimitador = ','

    with open(ruta_csv, 'r', encoding=encoding_usado, newline='') as f:
        reader = csv.DictReader(f, delimiter=delimitador)
        if not reader.fieldnames:
            raise ValueError("El archivo CSV esta vacio o no tiene encabezados.")

        mapa_columnas = {col.strip().lower(): col for col in reader.fieldnames if col}
        if 'nombre' not in mapa_columnas or 'puesto' not in mapa_columnas:
            raise ValueError("El CSV debe contener las columnas 'nombre' y 'puesto'.")

        col_nombre = mapa_columnas['nombre']
        col_puesto = mapa_columnas['puesto']

        registros = []
        for idx, fila in enumerate(reader, start=2):
            nombre = (fila.get(col_nombre) or '').strip()
            puesto = (fila.get(col_puesto) or '').strip()
            if nombre or puesto:
                registros.append((idx, nombre, puesto))

    return registros


def cargar_csv():
    print("\n--- Cargar CSV (Generacion por Lotes) ---")
    ruta_csv = seleccionar_archivo_actual(".csv", "archivo CSV")
    if not ruta_csv:
        return

    ruta_vector = seleccionar_archivo_actual(".svg", "logo SVG")
    if not ruta_vector:
        return

    try:
        registros = leer_registros_csv(ruta_csv)
    except Exception as e:
        print(f"[!] ERROR al leer CSV: {e}")
        return

    if not registros:
        print("[!] El archivo CSV no contiene registros validos.")
        return

    generados = 0
    errores = 0
    carpeta_destino = obtener_carpeta_salida(ruta_vector)

    print(f"\nProcesando {len(registros)} registros en: {carpeta_destino}")
    for linea, nombre, puesto in registros:
        if not nombre or not puesto:
            print(f"[!] Fila {linea} omitida: falta nombre o puesto.")
            errores += 1
            continue
        try:
            ruta_salida, _, _ = crear_gafete_svg(nombre, puesto, ruta_vector)
            print(f"  [OK] {os.path.basename(ruta_salida)}")
            generados += 1
        except Exception as e:
            print(f"  [ERROR] Fila {linea} ({nombre}): {e}")
            errores += 1

    print(f"\nLote finalizado. Generados: {generados} | Errores/Omitidos: {errores}")
    print(f"Carpeta de salida: {carpeta_destino}")


def submenu_lotes():
    while True:
        print("\n--- Generador por Lotes ---")
        print("1. Imprimir plantilla CSV")
        print("2. Cargar CSV")
        print("0. Volver al menu principal")

        opcion = input("Seleccione una opcion: ").strip()
        if opcion == '1':
            imprimir_plantilla_csv()
        elif opcion == '2':
            cargar_csv()
        elif opcion == '0':
            break
        else:
            print("[!] Opcion no valida.")


def menu_principal():
    while True:
        print("\n=== Creador de Gafetes Vectorial (Para Imprenta) ===")
        print(f"Carpeta actual: {os.getcwd()}")
        print("1. Modo General (Gafete individual)")
        print("2. Generador por Lotes")
        print("0. Salir")

        opcion = input("Seleccione una opcion: ").strip()
        if opcion == '1':
            modo_general()
        elif opcion == '2':
            submenu_lotes()
        elif opcion == '0':
            print("Saliendo...")
            break
        else:
            print("[!] Opcion no valida.")


if __name__ == "__main__":
    menu_principal()
