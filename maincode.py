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
    </style>
    """, unsafe_allow_html=True)

# 3. Función de carga ultra-segura
@st.cache_data
def load_data():
    file_name = 'datos_domotia.csv' # <--- Asegúrate que en GitHub se llame EXACTO así
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip()
        return df
    else:
        # Si no lo encuentra, nos avisa qué archivos SI hay en el server
        archivos_presentes = os.listdir('.')
        st.error(f"❌ No encontré '{file_name}'. En tu GitHub veo estos archivos: {archivos_presentes}")
        return None

df = load_data()

# 4. Gestión del estado
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False

# --- INTERFAZ ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if df is not None:
    # Sidebar
    st.sidebar.title("🕹️ Panel de Control")
    if st.sidebar.button("▶️ Iniciar Simulación"):
        st.session_state.corriendo = True
    if st.sidebar.button("⏹️ Detener"):
        st.session_state.corriendo = False
        st.session_state.indice = 1

    if st.session_state.corriendo:
        i = st.session_state.indice
        actual = df.iloc[i]
        anterior = df.iloc[i-1]
        ventana = df.iloc[max(0, i-30):i+1]

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AGUA 💧", f"{actual['consumo_agua']:.1f} L", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f} L", delta_color="inverse")
        c2.metric("ENERGÍA ⚡", f"{actual['consumo_electrico']:.3f} kWh", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f} kWh", delta_color="inverse")
        c3.metric("GAS LP 🔥", f"{actual.get('gas_nivel', 95)}%")
        c4.metric("TEMP 🌡️", f"{actual['temperatura_int']:.1f} °C")

        # ALERTAS "Ah qp" (Diagnóstico real)
        if str(actual.get('anomalia', '')).lower() == 'true':
            tipo = str(actual.get('tipo_anomalia', 'DESCONOCIDA')).upper()
            if "FUGA" in tipo or "AGUA" in tipo:
                st.error(f"🚨 **¡ALERTA DE AGUA!** Se detectó una posible FUGA. El sensor marca {actual['consumo_agua']}L de golpe.")
            elif "GAS" in tipo:
                st.warning(f"☢️ **¡PELIGRO!** Anomalía de GAS detectada. Sensor de flujo activo.")
            else:
                st.error(f"⚠️ **SISTEMA:** Anomalía detectada tipo {tipo}")
        else:
            st.success("✅ Todo normal. La casa está ahorrando recursos.")

        # Gráficas
        col_a, col_b = st.columns(2)
        col_a.area_chart(ventana['consumo_agua'], color="#0077B6")
        col_b.line_chart(ventana['consumo_electrico'], color="#FFB703")

        # Auto-refresh
        if st.session_state.indice < len(df) - 1:
            st.session_state.indice += 1
            time.sleep(0.4)
            st.rerun()
    else:
        st.info("Presiona 'Iniciar' en el panel lateral.")
else:
    st.warning("⚠️ Sube el archivo 'datos_domotia.csv' a la carpeta principal de tu GitHub para que la página funcione.")
