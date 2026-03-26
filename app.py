import streamlit as st
import pandas as pd
import numpy as np
import time

# Configuración de la interfaz (Enfoque de Diseño)
st.set_page_config(page_title="HMI Residencial - CODESO", layout="wide")

# Identidad Visual: Colores basados en tu plano (Agua: Verde, Luz: Amarillo, Contactos: Rojo)
st.markdown("""
    <style>
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏙️ Panel de Monitoreo Inteligente | Plan Sonora")
st.write("Interfaz de Gestión de Recursos para el Consejo para el Desarrollo Sostenible (CODESO)")

# --- LÓGICA DE SIMULACIÓN ADAPTADA ---
# Basado en la estructura de tu código original pero para visualización web
def generar_lecturas():
    t = time.time()
    # Simulación de flujo de agua (Basado en tus 5 puntos de consumo)
    agua = round(4.0 + 2.5 * np.sin(t / 5) + np.random.normal(0, 0.2), 2)
    # Simulación de consumo eléctrico (Basado en tus contactos y luces)
    energia = round(250 + 100 * np.sin(t / 10) + np.random.normal(0, 0.5), 1)
    return agua, energia

# --- DISEÑO DE LA INTERFAZ (HMI) ---
st.sidebar.header("📍 Ubicación del Dispositivo")
area = st.sidebar.selectbox("Seleccionar Área de la Casa", ["Global", "Estar", "Cocina/Comedor", "Baño", "Dormitorios"])

# Layout de métricas principales
col1, col2, col3 = st.columns(3)
agua_v, luz_v = generar_lecturas()

with col1:
    st.subheader("💧 Agua")
    st.metric(label="Flujo Actual (L/min)", value=f"{agua_v} L", delta="Normal")
    if agua_v > 6.0:
        st.error("🚨 Alerta: Posible fuga detectada")

with col2:
    st.subheader("⚡ Energía")
    st.metric(label="Consumo Eléctrico (W)", value=f"{luz_v} W", delta="Estable")
    if luz_v > 320:
        st.warning("⚠️ Aviso: Consumo elevado")

with col3:
    st.subheader("📡 Sistema")
    st.info(f"Nodo: ESP32\nÁrea: {area}\nEstado: Activo")

# Gráfica de Series de Tiempo (Evolución de tus gráficas de matplotlib)
st.divider()
st.write(f"### Análisis de Tendencias - {area}")
chart_data = pd.DataFrame(
    np.random.randn(20, 2) * [1.5, 20] + [agua_v, luz_v],
    columns=['Flujo Agua', 'Consumo Eléctrico']
)
st.line_chart(chart_data)

st.sidebar.write("---")
st.sidebar.button("Reiniciar Sensores")
