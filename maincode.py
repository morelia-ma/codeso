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
    .bitacora-item { padding: 8px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
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

# 4. Gestión del estado (ESTO ES LO QUE EVITA QUE SE TRABE)
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
# Mostrar bitácora de forma elegante
if st.session_state.historial_fugas:
    for ev in reversed(st.session_state.historial_fugas):
        st.sidebar.markdown(f"<div class='bitacora-item'><b>{ev['fecha']}</b><br>⚠️ {ev['tipo']}</div>", unsafe_allow_html=True)
else:
    st.sidebar.write("No hay eventos.")

# --- CUERPO PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
    c2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f}", delta_color="inverse")
    
    # Gas: Buscamos la columna gas_nivel o gas_fuga
    gas_val = actual['gas_nivel'] if 'gas_nivel' in actual and pd.notnull(actual['gas_nivel']) else 94.8
    c3.metric("NIVEL GAS % 🔥", f"{gas_val}%", "-0.1%")
    
    c4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # ALERTAS Y BITÁCORA
    # Detectamos si hay anomalía (buscando 'True' o el valor booleano)
    es_anomalia = str(actual.get('anomalia', '')).lower() == 'true'
    
    if es_anomalia:
        tipo_falla = str(actual.get('tipo_anomalia', 'FALLA')).upper()
        fecha_falla = str(actual.get('timestamp', 'S/F')).split('T')[-1][:5] # Solo hora para que quepa
        
        # Guardar en bitácora si es nueva
        registro = {"fecha": fecha_falla, "tipo": tipo_falla}
        if registro not in st.session_state.historial_fugas:
            st.session_state.historial_fugas.append(registro)
        
        st.error(f"🚨 **ANOMALÍA DETECTADA:** {tipo_falla} a las {fecha_falla}")
    else:
        st.success("✅ Sistemas operando con normalidad.")

    # Gráficas
    col_a, col_b = st.columns(2)
    with col_a:
        st.area_chart(ventana['consumo_agua'], color="#0077B6")
    with col_b:
        st.line_chart(ventana['consumo_electrico'], color="#FFB703")

    # LÓGICA DE AVANCE (EL MOTOR)
    if st.session_state.corriendo:
        if st.session_state.indice < len(df) - 1:
            st.session_state.indice += 1
            time.sleep(0.5)
            st.rerun() # Esto hace que la página se actualice y vuelva a checar si 'corriendo' es True
        else:
            st.session_state.corriendo = False
            st.balloons()
    else:
        st.info("Pausado. Presiona 'Iniciar' para continuar el monitoreo.")
else:
    st.error("No se encontró el archivo de datos.")
