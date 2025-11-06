import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO, TextIOWrapper
from openpyxl import Workbook

st.set_page_config(page_title="Filtro ZIP eficiente", layout="wide")
st.title("📦 Filtro de múltiples CSV desde ZIP (Optimizado para archivos grandes)")

# --- Configuración ---
st.sidebar.header("⚙️ Configuración")
encoding_opcion = st.sidebar.selectbox(
    "Codificación de archivos CSV:",
    ["utf-8", "latin1", "cp1252", "ISO-8859-1"],
    index=1
)

uploaded_zip = st.file_uploader("Sube un archivo ZIP con varios CSV", type=["zip"])

if not uploaded_zip:
    st.info("Sube un archivo ZIP para comenzar.")
    st.stop()

# --- Leer estructura ZIP ---
try:
    z = zipfile.ZipFile(uploaded_zip)
    csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
    if not csv_files:
        st.error("No se encontraron archivos CSV dentro del ZIP.")
        st.stop()
    st.success(f"Se encontraron {len(csv_files)} archivos CSV.")
except Exception as e:
    st.error(f"Error al leer el ZIP: {e}")
    st.stop()

# --- Tomar un archivo pequeño para generar listas de filtros ---
muestra = None
for file_name in csv_files:
    try:
        with z.open(file_name) as f:
            df = pd.read_csv(TextIOWrapper(f, encoding=encoding_opcion), nrows=5000)
            if all(c in df.columns for c in ["Entidad", "Modalidad", "Ciclo", "Cultivo"]):
                muestra = df
                break
    except Exception:
        continue

if muestra is None:
    st.error("Ningún archivo contiene las columnas requeridas (Entidad, Modalidad, Ciclo, Cultivo).")
    st.stop()

# --- Crear filtros dinámicos ---
st.sidebar.header("🎯 Filtros")

entidad_sel = st.sidebar.multiselect(
    "Entidad", sorted(muestra["Entidad"].dropna().unique().tolist())
)
modalidad_sel = st.sidebar.multiselect(
    "Modalidad", sorted(muestra["Modalidad"].dropna().unique().tolist())
)
ciclo_sel = st.sidebar.multiselect(
    "Ciclo", sorted(muestra["Ciclo"].dropna().unique().tolist())
)
cultivo_sel = st.sidebar.multiselect(
    "Cultivo", sorted(muestra["Cultivo"].dropna().unique().tolist())
)

# --- Generar archivo Excel final ---
st.write("📊 Procesando archivos... (esto puede tardar unos minutos con archivos grandes)")

wb = Workbook()
wb.remove(wb.active)

procesados = 0
for file_name in csv_files:
    try:
        with z.open(file_name) as f:
            df = pd.read_csv(TextIOWrapper(f, encoding=encoding_opcion))
            if not all(c in df.columns for c in ["Entidad", "Modalidad", "Ciclo", "Cultivo"]):
                continue

            # --- Aplicar filtros ---
            if entidad_sel:
                df = df[df["Entidad"].isin(entidad_sel)]
            if modalidad_sel:
                df = df[df["Modalidad"].isin(modalidad_sel)]
            if ciclo_sel:
                df = df[df["Ciclo"].isin(ciclo_sel)]
            if cultivo_sel:
                df = df[df["Cultivo"].isin(cultivo_sel)]

            if len(df) == 0:
                continue

            # --- Agregar hoja al Excel ---
            ws = wb.create_sheet(title=file_name.replace(".csv", "")[:31])
            ws.append(list(df.columns))
            for row in df.itertuples(index=False):
                ws.append(row)

            procesados += 1

    except Exception as e:
        st.warning(f"⚠️ Error procesando {file_name}: {e}")

if procesados == 0:
    st.warning("Ningún archivo cumplió con los filtros seleccionados.")
    st.stop()

# --- Descargar resultado ---
output = BytesIO()
wb.save(output)
st.download_button(
    label="📥 Descargar Excel filtrado",
    data=output.getvalue(),
    file_name="filtrado_resultados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success(f"✅ {procesados} archivos procesados correctamente.")
