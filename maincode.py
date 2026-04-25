import streamlit as st
import pandas as pd
import time

# Configuración de página - Estilo CODESO
st.set_page_config(page_title="CODESO Smart Home", layout="wide", initial_sidebar_state="expanded")

# CSS para semiótica visual (Azul=Agua, Ámbar=Luz)
st.markdown("""
    <style>
    .stMetric { border-radius: 10px; background-color: #ffffff; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def get_data():
    df = pd.read_csv('datos_domotia.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df_full = get_data()

# Sidebar - Capa de Control
st.sidebar.header("🕹️ Panel de Control")
if 'sim_running' not in st.session_state:
    st.session_state.sim_running = False

start = st.sidebar.button("▶️ Iniciar Simulación")
stop = st.sidebar.button("⏹️ Detener")

if start: st.session_state.sim_running = True
if stop: st.session_state.sim_running = False

st.sidebar.divider()
st.sidebar.caption("Proyecto: Monitoreo de Recursos Sostenibles\nCODESO - Sonora")

# Contenedores dinámicos
st.title("🏠 Sistema Inteligente de Monitoreo Residencial")
kpis = st.empty()
alerts = st.empty()
charts = st.empty()

# Bucle de Simulación (0.5s = 30min reales)
if st.session_state.sim_running:
    # Empezamos desde un punto aleatorio o el inicio
    for i in range(1, len(df_full)):
        if not st.session_state.sim_running:
            break
            
        actual = df_full.iloc[i]
        anterior = df_full.iloc[i-1]
        ventana = df_full.iloc[max(0, i-48):i] # Últimas 24 horas (48 bloques de 30min)

        # 1. Métricas (Diagnóstico Inmediato)
        with kpis.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Agua (L) 💧", f"{actual['consumo_agua']:.1f}", 
                      f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
            c2.metric("Energía (kWh) ⚡", f"{actual['consumo_electrico']:.3f}", 
                      f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f}", delta_color="inverse")
            c3.metric("Temp. Int 🌡️", f"{actual['temperatura_int']:.1f} °C")
            c4.metric("Gas 💨", f"{actual['gas_nivel'] if pd.notnull(actual['gas_nivel']) else 'OK'}")

        # 2. Alertas (Semántica de Alerta - Rojo)
        with alerts.container():
            if actual['anomalia']:
                st.error(f"🚨 ALERTA: {actual['tipo_anomalia']} detectada a las {actual['timestamp'].strftime('%H:%M')}")

        # 3. Visualización (Integridad Gráfica)
        with charts.container():
            col_izq, col_der = st.columns(2)
            with col_izq:
                st.write("**Flujo de Agua (Histórico)**")
                st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
            with col_der:
                st.write("**Carga Eléctrica (Histórico)**")
                st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")
        
        time.sleep(0.5)
else:
    st.info("Presiona 'Iniciar Simulación' en el panel izquierdo para comenzar la visualización en tiempo real.")