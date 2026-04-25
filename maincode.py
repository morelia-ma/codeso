import streamlit as st
import pandas as pd
import time
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilo CSS "Premium" (Jerarquía Visual de tu doc)
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
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

# 4. Gestión del estado (Pausa, Índice, Corriendo)
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False

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
    st.rerun()

st.sidebar.divider()
st.sidebar.write(f"Progreso: {st.session_state.indice} / {len(df) if df is not None else 0}")

# --- CUERPO PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    
    # 💧 Agua
    c1.metric("AGUA (L)", f"{actual['consumo_agua']:.1f}", 
              f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
    
    # ⚡ Energía
    c2.metric("ENERGÍA (kWh)", f"{actual['consumo_electrico']:.3f}", 
              f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f}", delta_color="inverse")
    
    # 🔥 GAS (Corregido: Mostrando porcentaje)
    # Si el valor es nulo en el CSV, mostramos 95% como base de simulación
    valor_gas = actual['gas_level'] if 'gas_level' in actual and pd.notnull(actual['gas_level']) else 95.2
    c3.metric("NIVEL GAS %", f"{valor_gas}%", "-0.1%")
    
    # 🌡️ Temperatura
    c4.metric("TEMP. INT", f"{actual['temperatura_int']:.1f} °C")

    # ALERTAS INTELIGENTES (Semántica de Alerta)
    if str(actual.get('anomalia', '')).lower() == 'true':
        tipo = str(actual.get('tipo_anomalia', 'DESCONOCIDA')).upper()
        st.error(f"🚨 **ANOMALÍA DETECTADA:** {tipo}")
    else:
        st.success("✅ Sistemas bajo control. Consumo eficiente.")

    # Gráficas
    col_a, col_b = st.columns(2)
    with col_a:
        st.area_chart(ventana['consumo_agua'], color="#0077B6")
    with col_b:
        st.line_chart(ventana['consumo_electrico'], color="#FFB703")

    # Lógica de Pausa y Avance
    if st.session_state.corriendo:
        if st.session_state.indice < len(df) - 1:
            st.session_state.indice += 1
            time.sleep(0.5)
            st.rerun()
        else:
            st.session_state.corriendo = False
            st.success("Simulación terminada.")
else:
    st.error("Archivo 'datos_domotia.csv' no detectado en el repositorio.")
