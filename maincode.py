import streamlit as st
import pandas as pd
import time
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilo CSS (Semiótica de color para HMI)
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #FFB703; font-weight: bold; }
    .falla-gas { color: #DC2626; font-weight: bold; }
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

# 4. Estado de la sesión
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False
if 'historial_fugas' not in st.session_state:
    st.session_state.historial_fugas = []

# --- SIDEBAR (Bitácora con Tipo de Fallo y Fecha) ---
st.sidebar.title("🕹️ Panel de Control")

c_play, c_pause = st.sidebar.columns(2)
if c_play.button("▶️ Iniciar"): st.session_state.corriendo = True
if c_pause.button("⏸️ Pausar"): st.session_state.corriendo = False

if st.sidebar.button("🔄 Reiniciar"):
    st.session_state.corriendo = False
    st.session_state.indice = 1
    st.session_state.historial_fugas = []
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📋 Historial de Fallos")

if st.session_state.historial_fugas:
    for ev in reversed(st.session_state.historial_fugas):
        # Aplicar color según el tipo en la bitácora
        clase = "falla-agua" if "AGUA" in ev['tipo'] else "falla-luz" if "LUZ" in ev['tipo'] or "ELEC" in ev['tipo'] else "falla-gas"
        st.sidebar.markdown(f"""
            <div class='bitacora-item'>
                <small>{ev['fecha']}</small><br>
                <span class='{clase}'>⚠️ FALLO DE {ev['tipo']}</span>
            </div>
        """, unsafe_allow_html=True)
else:
    st.sidebar.write("Sin registros.")

# --- CUERPO PRINCIPAL ---
st.title("🏠 Centro de Control Residencial")

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
    c2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f}", delta_color="inverse")
    
    gas_val = actual['gas_nivel'] if 'gas_nivel' in actual and pd.notnull(actual['gas_nivel']) else 94.8
    c3.metric("NIVEL GAS % 🔥", f"{gas_val}%")
    c4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Lógica de Detección y Clasificación para la Bitácora
    es_anomalia = str(actual.get('anomalia', '')).lower() == 'true'
    
    if es_anomalia:
        texto_anomalia = str(actual.get('tipo_anomalia', '')).upper()
        fecha_completa = str(actual.get('timestamp', 'S/F')).replace('T', ' ')[:16] # Formato: YYYY-MM-DD HH:MM
        
        # Clasificar el tipo de fallo para el usuario
        if "AGUA" in texto_anomalia or "FUGA" in texto_anomalia:
            tipo_usuario = "AGUA"
        elif "ELEC" in texto_anomalia or "VOLT" in texto_anomalia or "LUMIN" in texto_anomalia:
            tipo_usuario = "LUZ"
        elif "GAS" in texto_anomalia:
            tipo_usuario = "GAS"
        else:
            tipo_usuario = "SISTEMA"

        # Guardar si no existe ya
        registro = {"fecha": fecha_completa, "tipo": tipo_usuario, "idx": i}
        if not any(entry['idx'] == i for entry in st.session_state.historial_fugas):
            st.session_state.historial_fugas.append(registro)
        
        st.error(f"🚨 **ALERTA:** Fallo de {tipo_usuario} detectado el {fecha_completa}")

    # Gráficas
    col_a, col_b = st.columns(2)
    col_a.area_chart(ventana['consumo_agua'], color="#0077B6")
    col_b.line_chart(ventana['consumo_electrico'], color="#FFB703")

    # Motor de la simulación
    if st.session_state.corriendo:
        if st.session_state.indice < len(df) - 1:
            st.session_state.indice += 1
            time.sleep(0.5)
            st.rerun()
else:
    st.error("Sube el archivo 'datos_domotia.csv' a GitHub.")
