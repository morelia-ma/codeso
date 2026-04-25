import streamlit as st
import pandas as pd
import time
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilo CSS "Premium"
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .fuga-log { padding: 10px; border-radius: 5px; background-color: #FEE2E2; border-left: 5px solid #DC2626; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de datos
@st.cache_data
def load_data():
    file_name = 'datos_domotia.csv'
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip()
        return df
    return None

df = load_data()

# 4. Gestión del estado (Pausa, Índice, Historial de Fugas)
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False
if 'historial_fugas' not in st.session_state:
    st.session_state.historial_fugas = []

# --- SIDEBAR (Panel de Control HMI) ---
st.sidebar.title("🕹️ Panel de Control")

col_play, col_pause = st.sidebar.columns(2)
if col_play.button("▶️ Iniciar"):
    st.session_state.corriendo = True
if col_pause.button("⏸️ Pausar"):
    st.session_state.corriendo = False

if st.sidebar.button("🔄 Reiniciar"):
    st.session_state.corriendo = False
    st.session_state.indice = 1
    st.session_state.historial_fugas = []
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📋 Bitácora de Fugas")
if st.session_state.historial_fugas:
    for evento in reversed(st.session_state.historial_fugas):
        st.sidebar.markdown(f"**{evento['fecha']}** \n⚠️ {evento['tipo']}", unsafe_allow_html=True)
else:
    st.sidebar.write("No hay eventos registrados.")

# --- CUERPO PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f} L", delta_color="inverse")
    c2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f} kWh", delta_color="inverse")
    
    # Gas (Mostrando columna gas_nivel si existe)
    nivel_gas = actual['gas_nivel'] if 'gas_nivel' in actual and pd.notnull(actual['gas_nivel']) else 95.0
    c3.metric("NIVEL GAS % 🔥", f"{nivel_gas}%", "-0.1%")
    
    c4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # ALERTAS Y REGISTRO EN BITÁCORA
    if str(actual.get('anomalia', '')).lower() == 'true':
        tipo_
