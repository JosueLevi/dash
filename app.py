import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Gantt Proyecto Web", layout="wide")
st.title("SISE WEB")

FILE_PATH = Path("data.xlsx")

if not FILE_PATH.exists():
    st.error("❌ No se encontró el archivo 'data.xlsx' en la carpeta del proyecto.")
    st.stop()

df = pd.read_excel(FILE_PATH)

# ---------- NORMALIZAR NOMBRES DE COLUMNAS ----------
def norm(col: str) -> str:
    return str(col).strip().lower().replace("\n", " ").replace("\t", " ")

df.columns = [norm(c) for c in df.columns]

# Mapeo flexible: acepta variantes comunes
aliases = {
    "fase": ["fase", "etapa", "phase"],
    "actividad": ["actividad", "tarea", "task", "nombre", "actividad/tarea"],
    "inicio": ["inicio", "fecha inicio", "start", "start date", "fecha_inicio"],
    "fin": ["fin", "fecha fin", "end", "end date", "fecha_fin", "termino", "término", "final"],
    "responsable": ["responsable", "owner", "asignado", "encargado"],
    "estado": ["estado", "status", "situacion", "situación"]
}

def find_col(candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

col_fase = find_col(aliases["fase"])
col_actividad = find_col(aliases["actividad"])
col_inicio = find_col(aliases["inicio"])
col_fin = find_col(aliases["fin"])
col_responsable = find_col(aliases["responsable"])
col_estado = find_col(aliases["estado"])

found = {
    "Fase": col_fase,
    "Actividad": col_actividad,
    "Inicio": col_inicio,
    "Fin": col_fin,
    "Responsable": col_responsable,
    "Estado": col_estado
}

missing = [k for k, v in found.items() if v is None]

with st.expander("🔎 Columnas detectadas (debug)"):
    st.write("Columnas en tu Excel (normalizadas):")
    st.write(list(df.columns))
    st.write("Mapeo detectado:")
    st.json(found)

if missing:
    st.error(f"❌ No pude encontrar estas columnas en tu Excel: {', '.join(missing)}")
    st.stop()

# ---------- Renombrar a estándar ----------
df = df.rename(columns={
    col_fase: "Fase",
    col_actividad: "Actividad",
    col_inicio: "Inicio",
    col_fin: "Fin",
    col_responsable: "Responsable",
    col_estado: "Estado",
})

# ---------- Tipos de fecha ----------
df["Inicio"] = pd.to_datetime(df["Inicio"], errors="coerce")
df["Fin"] = pd.to_datetime(df["Fin"], errors="coerce")

df = df.dropna(subset=["Inicio", "Fin"])
df = df[df["Fin"] >= df["Inicio"]].copy()

# ---------- Filtros ----------
st.sidebar.header("🎛️ Filtros")
fases = st.sidebar.multiselect("Fase", sorted(df["Fase"].dropna().unique()),
                               default=sorted(df["Fase"].dropna().unique()))
responsables = st.sidebar.multiselect("Responsable", sorted(df["Responsable"].dropna().unique()),
                                      default=sorted(df["Responsable"].dropna().unique()))
estados = st.sidebar.multiselect("Estado", sorted(df["Estado"].dropna().unique()),
                                 default=sorted(df["Estado"].dropna().unique()))

df_f = df[df["Fase"].isin(fases) & df["Responsable"].isin(responsables) & df["Estado"].isin(estados)].copy()
df_f = df_f.sort_values("Inicio")

c1, c2, c3 = st.columns(3)
c1.metric("🧩 Actividades", len(df_f))
c2.metric("📌 Fases", df_f["Fase"].nunique() if len(df_f) else 0)
c3.metric("👥 Responsables", df_f["Responsable"].nunique() if len(df_f) else 0)

if df_f.empty:
    st.warning("⚠️ No hay datos con los filtros actuales.")
    st.stop()

color_mode = st.radio("Colorear por", ["Fase", "Estado", "Responsable"], horizontal=True)

fig = px.timeline(df_f, x_start="Inicio", x_end="Fin", y="Actividad", color=color_mode,
                  hover_data=["Fase", "Responsable", "Estado", "Inicio", "Fin"])
fig.update_yaxes(autorange="reversed")
fig.update_layout(height=min(900, 120 + 35 * len(df_f)))

st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Ver tabla"):
    st.dataframe(df_f[["Fase", "Actividad", "Inicio", "Fin", "Responsable", "Estado"]],
                 use_container_width=True)
