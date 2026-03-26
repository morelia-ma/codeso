import streamlit as st
import pandas as pd
import numpy as np
import time

# Configuración de la interfaz
st.set_page_config(page_title="HMI CODESO - Detalle por Sensor", layout="wide")

st.title("📊 Visualización Individual de Recursos | Plan Sonora")
st.sidebar.header("Filtros de Visualización")
habitacion = st.sidebar.selectbox("Área de la Vivienda", ["Global", "Estar", "Cocina", "Baño", "Dormitorio"])

# --- GENERACIÓN DE DATOS SEPARADOS ---
def get_sensor_data():
    # Generamos 20 puntos de datos para las gráficas
    t = np.linspace(0, 10, 20)
    data_agua = 5 + 2 * np.sin(t) + np.random.normal(0, 0.2, 20)
    data_luz = 200 + 50 * np.cos(t) + np.random.normal(0, 5, 20)
    data_temp = 25 + 3 * np.sin(t/2) + np.random.normal(0, 0.1, 20)
    return data_agua, data_luz, data_temp

d_agua, d_luz, d_temp = get_sensor_data()

# --- FILA 1: AGUA ---
st.divider()
col_a1, col_a2 = st.columns([1, 3])
with col_a1:
    st.metric("💧 Flujo de Agua", f"{round(d_agua[-1], 2)} L/min", delta="-0.5")
    st.write("**Ubicación:** Nodos de red hidráulica.")
with col_a2:
    df_agua = pd.DataFrame(d_agua, columns=["Litros/Min"])
    st.area_chart(df_agua, color="#29b5e8")

# --- FILA 2: ENERGÍA ---
st.divider()
col_e1, col_e2 = st.columns([1, 3])
with col_e1:
    st.metric("⚡ Consumo Eléctrico", f"{round(d_luz[-1], 1)} W", delta="12W", delta_color="inverse")
    st.write("**Ubicación:** Contactos y luminarias.")
with col_e2:
    df_luz = pd.DataFrame(d_luz, columns=["Watts"])
    st.line_chart(df_luz, color="#f4d03f")

# --- FILA 3: AMBIENTE (Simulando Temperatura/Humedad) ---
st.divider()
col_t1, col_t2 = st.columns([1, 3])
with col_t1:
    st.metric("🌡️ Temperatura", f"{round(d_temp[-1], 1)} °C")
    st.write("**Estado:** Confort térmico.")
with col_t2:
    df_temp = pd.DataFrame(d_temp, columns=["Grados C"])
    st.bar_chart(df_temp, color="#e67e22")
