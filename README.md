# Gaf-E-xpress

Generador de gafetes vectoriales en formato SVG listos para imprenta (4.5 cm x 1.5 cm), con modo individual y generador por lotes mediante archivos CSV.

## Caracteristicas

- **Deteccion automatica en la carpeta actual**: Escanea y lista archivos `.svg` y `.csv` presentes en el directorio de trabajo para seleccionarlos por numero, con opcion de ingresar una ruta manual.
- **Modo General (Individual)**: Genera un gafete SVG a partir de un logo `.svg`, nombre y puesto.
- **Generador por Lotes (CSV)**:
  - **Imprimir plantilla CSV**: Crea `plantilla_gafetes.csv` con las columnas requeridas (`nombre,puesto`) y registros de ejemplo.
  - **Cargar CSV**: Lee archivos CSV (soporta delimitadores `,` y `;` y codificaciones UTF-8/Latin-1) y genera todos los gafetes en lote.
- **Procesamiento Vectorial (Imprenta)**:
  - Convierte colores HEX y RGB del logo a negro puro (`#000000`) preservando transparencias (`fill: none`).
  - Escala automaticamente el logo usando su `viewBox` o dimensiones originales.
  - Dimensiones fisicas exactas: `4.5cm x 1.5cm` (`viewBox="0 0 450 150"`).
- **Carpeta de salida organizada**: Todos los archivos generados se guardan en `Gafetes_<nombre_del_svg>/`.

## Uso

### Ejecutable (Windows)

1. Descarga `Gaf-E-xpress.exe` desde la seccion de **Releases** del repositorio.
2. Coloca `Gaf-E-xpress.exe` en la carpeta donde tienes tus logos `.svg` (y opcionalmente tus archivos `.csv`).
3. Ejecuta `Gaf-E-xpress.exe` y selecciona una opcion del menu:
   - `1. Modo General (Gafete individual)`
   - `2. Generador por Lotes`
     - `1. Imprimir plantilla CSV`
     - `2. Cargar CSV`

### Desde codigo fuente (Python 3)

No requiere dependencias externas (usa unicamente la biblioteca estandar de Python).

```bash
python generar_gafetes.py
```

### Compilar el ejecutable (.exe)

```bash
pip install pyinstaller
python -m PyInstaller --onefile --console --name Gaf-E-xpress generar_gafetes.py
```

El ejecutable se generara en `dist/Gaf-E-xpress.exe`.

## Formato del CSV para lotes

El archivo CSV debe incluir encabezados `nombre` y `puesto`:

```csv
nombre,puesto
Juan Perez,Gerente
Maria Lopez,Cajera
```
