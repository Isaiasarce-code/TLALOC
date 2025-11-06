import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO, TextIOWrapper
from openpyxl import Workbook

st.set_page_config(page_title="📦 Catálogo de Filtros desde ZIP", layout="wide")
st.title("📦 Extraer todas las opciones únicas desde varios CSV")

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
    st.success(f"✅ Se encontraron {len(csv_files)} archivos CSV.")
except Exception as e:
    st.error(f"Error al leer el ZIP: {e}")
    st.stop()

# --- Variables acumuladoras de valores únicos ---
entidades = set()
modalidades = set()
ciclos = set()
cultivos = set()

st.write("📊 Analizando archivos para obtener todas las opciones únicas...")

# --- Recorrer cada CSV ---
procesados = 0
for file_name in csv_files:
    try:
        with z.open(file_name) as f:
            df = pd.read_csv(TextIOWrapper(f, encoding=encoding_opcion), usecols=lambda x: x in ["Entidad", "Modalidad", "Ciclo", "Cultivo"], low_memory=False)
            df.columns = df.columns.str.strip()

            # Verificar columnas
            columnas_presentes = [c for c in ["Entidad", "Modalidad", "Ciclo", "Cultivo"] if c in df.columns]
            if not columnas_presentes:
                continue

            # Guardar valores únicos
            if "Entidad" in df.columns:
                entidades.update(df["Entidad"].dropna().unique().tolist())
            if "Modalidad" in df.columns:
                modalidades.update(df["Modalidad"].dropna().unique().tolist())
            if "Ciclo" in df.columns:
                ciclos.update(df["Ciclo"].dropna().unique().tolist())
            if "Cultivo" in df.columns:
                cultivos.update(df["Cultivo"].dropna().unique().tolist())

            procesados += 1

    except Exception as e:
        st.warning(f"⚠️ Error procesando {file_name}: {e}")

if procesados == 0:
    st.error("Ningún archivo contenía las columnas requeridas (Entidad, Modalidad, Ciclo, Cultivo).")
    st.stop()

# --- Crear DataFrame resumen ---
data = {
    "Entidad": sorted(entidades),
    "Modalidad": sorted(modalidades),
    "Ciclo": sorted(ciclos),
    "Cultivo": sorted(cultivos)
}

# Crear hojas separadas para cada catálogo
wb = Workbook()
wb.remove(wb.active)

for key, values in data.items():
    ws = wb.create_sheet(title=key)
    ws.append([key])
    for v in values:
        ws.append([v])

# --- Descargar resultado ---
output = BytesIO()
wb.save(output)

st.download_button(
    label="📥 Descargar Excel con todas las opciones únicas",
    data=output.getvalue(),
    file_name="catalogos_unicos.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success(f"✅ Catálogo generado correctamente con datos de {procesados} archivos.")
