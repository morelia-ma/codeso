import streamlit as st
import pandas as pd
import time
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilos CSS (Semiótica y Limpieza de Interfaz)
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    .progreso-text { font-size: 1rem; font-weight: bold; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de datos
@st.cache_data
def load_data():
    file_name = 'datos_domotia_final.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip()
        return df
    return None

df = load_data()

# 4. Estado de la sesión
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False
if 'historial_fugas' not in st.session_state:
    st.session_state.historial_fugas = []

# --- SIDEBAR (Controles y Bitácora) ---
st.sidebar.title("🕹️ Panel de Control")

col_play, col_pause = st.sidebar.columns(2)
if col_play.button("▶️ Iniciar"): st.session_state.corriendo = True
if col_pause.button("⏸️ Pausar"): st.session_state.corriendo = False

if st.sidebar.button("🔄 Reiniciar"):
    st.session_state.corriendo = False
    st.session_state.indice = 1
    st.session_state.historial_fugas = []
    st.rerun()

# --- CONTADOR DE PROGRESO (Lo que pediste para saber cuánto falta) ---
if df is not None:
    total_datos = len(df)
    progreso = st.session_state.indice
    porcentaje = (progreso / total_datos)
    
    st.sidebar.divider()
    st.sidebar.markdown(f"<div class='progreso-text'>Progreso: {progreso} / {total_datos}</div>", unsafe_allow_html=True)
    st.sidebar.progress(porcentaje)
    st.sidebar.caption(f"Faltan {total_datos - progreso} registros para terminar.")

st.sidebar.divider()
st.sidebar.subheader("📋 Historial de Fallos")
if st.session_state.historial_fugas:
    for ev in reversed(st.session_state.historial_fugas):
        clase = "falla-agua" if ev['tipo'] == "AGUA" else "falla-luz" if ev['tipo'] == "LUZ" else "falla-gas"
        st.sidebar.markdown(f"<div class='bitacora-item'><small>{ev['fecha']}</small><br><span class='{clase}'>⚠️ FALLO DE {ev['tipo']}</span></div>", unsafe_allow_html=True)

# --- CUERPO PRINCIPAL ---
st.title("🏠 Centro de Control Residencial")

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
    c2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f}", delta_color="inverse")
    
    # Gas (Mostrando columna real)
    gas_val = actual['gas_nivel'] if 'gas_nivel' in actual and pd.notnull(actual['gas_nivel']) else 94.5
    c3.metric("NIVEL GAS % 🔥", f"{gas_val}%")
    c4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Lógica de Clasificación de Fallos (Mejorada para no decir "Sistema")
    es_anomalia = str(actual.get('anomalia', '')).lower() == 'true'
    
    if es_anomalia:
        txt = str(actual.get('tipo_anomalia', '')).upper()
        fecha = str(actual.get('timestamp', 'S/F')).replace('T', ' ')[:16]
        
        # Clasificación por palabras clave
        if any(p in txt for p in ["AGUA", "FUGA", "HIDRO", "LIQUIDO"]):
            tipo_real = "AGUA"
        elif any(p in txt for p in ["GAS", "FLUJO", "LP", "METANO"]):
            tipo_real = "GAS"
        else:
            tipo_real = "LUZ" # Default para cualquier otra anomalía eléctrica/térmica

        if not any(entry['idx'] == i for entry in st.session_state.historial_fugas):
            st.session_state.historial_fugas.append({"fecha": fecha, "tipo": tipo_real, "idx": i})
        
        st.error(f"🚨 **ALERTA DE {tipo_real}:** Detectada el {fecha}")

    # GRÁFICAS (UNA SOLA FILA, SIN DUPLICADOS)
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Monitoreo de Agua")
        st.area_chart(ventana['consumo_agua'], color="#0077B6")
    with col_b:
        st.subheader("Monitoreo Eléctrico")
        st.line_chart(ventana['consumo_electrico'], color="#FFB703")

    # Motor de Simulación
    if st.session_state.corriendo:
        if st.session_state.indice < len(df) - 1:
            st.session_state.indice += 1
            time.sleep(0.4)
            st.rerun()
        else:
            st.session_state.corriendo = False
            st.balloons()
            st.success("Simulación completada satisfactoriamente.")
