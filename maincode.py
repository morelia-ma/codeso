import streamlit as st
import pandas as pd
import time

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilo CSS "Premium"
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .stAlert { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Gestión del estado de la simulación
if 'indice' not in st.session_state:
    st.session_state.indice = 0
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False

@st.cache_data
def load_data():
    return pd.read_csv('datos_domotia.csv')

df = load_data()

# --- SIDEBAR CONTROL ---
st.sidebar.title("🕹️ Panel de Control")
if st.sidebar.button("▶️ Iniciar Simulación"):
    st.session_state.corriendo = True

if st.sidebar.button("⏹️ Detener"):
    st.session_state.corriendo = False
    st.session_state.indice = 0

st.sidebar.divider()
st.sidebar.write(f"Registro actual: {st.session_state.indice}")

# --- CUERPO PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if st.session_state.corriendo:
    # Obtener datos actuales
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1] if i > 0 else actual
    ventana = df.iloc[max(0, i-20):i+1]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA 💧", f"{actual['consumo_agua']:.1f} L", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f} L", delta_color="inverse")
    c2.metric("ENERGÍA ⚡", f"{actual['consumo_electrico']:.3f} kWh", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f} kWh", delta_color="inverse")
    c3.metric("GAS LP 🔥", f"{actual['gas_nivel'] if pd.notnull(actual['gas_nivel']) else 98}%")
    c4.metric("TEMP 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Alertas inteligentes
    if actual['anomalia']:
        msg = str(actual['tipo_anomalia']).upper()
        if "FUGA" in msg or "AGUA" in msg:
            st.error(f"🚨 **¡CUIDADO!** Se detectó una **FUGA DE AGUA** ({actual['timestamp']})")
        elif "GAS" in msg:
            st.warning(f"☢️ **¡PELIGRO!** Falla en sistema de **GAS** detectada.")
        else:
            st.error(f"⚠️ **ANOMALÍA:** {msg}")
    else:
        st.success("✅ Sistemas estables. Consumo optimizado.")

    # Gráficas
    col_a, col_b = st.columns(2)
    col_a.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    col_b.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

    # Avanzar el índice y REFRESCAR la página automáticamente
    if st.session_state.indice < len(df) - 1:
        st.session_state.indice += 1
        time.sleep(0.5)
        st.rerun() # <--- Este es el comando clave
    else:
        st.session_state.corriendo = False
        st.success("Simulación completada.")
else:
    st.info("HMI en espera. Presiona 'Iniciar Simulación' en el menú lateral.")
