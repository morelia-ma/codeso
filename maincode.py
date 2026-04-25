import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.graph_objects as go
import os

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="HMI Residencial - CODESO", layout="wide")

# --- INICIALIZACIÓN DE ESTADOS ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['Timestamp', 'Agua', 'Energia', 'Gas', 'Temp'])
if 'fugas' not in st.session_state:
    st.session_state.fugas = [] # Lista para el historial de alertas
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False
if 'indice' not in st.session_state:
    st.session_state.indice = 0

# --- LÓGICA DE DETECCIÓN DE FUGAS ---
def checar_fuga(valor_agua):
    # Supongamos que más de 12L en esta simulación es una anomalía
    if valor_agua > 12.5:
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        evento = {"Fecha/Hora": ahora, "Valor": f"{valor_agua:.2f} L", "Tipo": "Posible Fuga / Consumo Excesivo"}
        # Solo agregar si no es el mismo evento exacto anterior
        if not st.session_state.fugas or st.session_state.fugas[-1]["Fecha/Hora"] != ahora:
            st.session_state.fugas.append(evento)

# --- ENCABEZADO CON FECHA (ARRIBA A LA DERECHA) ---
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.title("🏠 Centro de Control Residencial")
with head_col2:
    st.write(f"📅 **Fecha:** {datetime.now().strftime('%d/%m/%Y')}")
    st.write(f"⏰ **Hora:** {datetime.now().strftime('%H:%M:%S')}")

# --- BARRA LATERAL (CONTROL) ---
st.sidebar.title("🕹️ Panel de Control")

# Botones de control
btn_col1, btn_col2 = st.sidebar.columns(2)
if btn_col1.button("▶️ Iniciar"):
    st.session_state.corriendo = True

if btn_col2.button("⏸️ Pausa"):
    st.session_state.corriendo = False

if st.sidebar.button("🔄 Reiniciar Todo"):
    st.session_state.db = pd.DataFrame(columns=['Timestamp', 'Agua', 'Energia', 'Gas', 'Temp'])
    st.session_state.fugas = []
    st.session_state.indice = 0
    st.session_state.corriendo = False
    st.rerun()

st.sidebar.divider()
st.sidebar.write(f"**Estado:** {'🟢 Corriendo' if st.session_state.corriendo else '🟡 Pausado'}")
st.sidebar.write(f"**Registro:** {st.session_state.indice} / 17474")

# --- SIMULACIÓN DE DATOS ---
if st.session_state.corriendo:
    # Simulamos la lectura de 1 registro nuevo
    nuevo_v_agua = np.random.uniform(5, 14)
    nuevo_dato = {
        'Timestamp': datetime.now().strftime("%H:%M:%S"),
        'Agua': nuevo_v_agua,
        'Energia': np.random.uniform(0.1, 0.8),
        'Gas': np.random.uniform(95, 98),
        'Temp': np.random.uniform(18, 22)
    }
    
    # Añadir al DataFrame
    st.session_state.db = pd.concat([st.session_state.db, pd.DataFrame([nuevo_dato])], ignore_index=True)
    st.session_state.indice += 1
    
    # Detectar Fuga
    checar_fuga(nuevo_v_agua)
    
    # Mantener solo los últimos 50 datos para que la gráfica no sea pesada
    if len(st.session_state.db) > 50:
        st.session_state.db = st.session_state.db.tail(50)

# --- VISUALIZACIÓN PRINCIPAL ---
if not st.session_state.db.empty:
    # KPIs
    ult = st.session_state.db.iloc[-1]
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("AGUA 💧", f"{ult['Agua']:.1f} L")
    kpi2.metric("ENERGÍA ⚡", f"{ult['Energia']:.3f} kWh")
    kpi3.metric("TEMP 🌡️", f"{ult['Temp']:.1f} °C")

    # Gráfica de tiempo real
    st.area_chart(st.session_state.db.set_index('Timestamp')[['Agua', 'Energia']])

else:
    st.info("Sistema HMI en espera. Haz clic en 'Iniciar' para ver datos.")

# --- SECCIÓN DE HISTORIAL DE FUGAS (ABAJO) ---
st.divider()
st.subheader("🚨 Historial de Eventos y Anomalías")

if st.session_state.fugas:
    df_fugas = pd.DataFrame(st.session_state.fugas)
    # Mostramos la tabla con colores según el tipo (opcional)
    st.dataframe(df_fugas, use_container_width=True, hide_index=True)
    
    st.info("💡 Consejo: Revisa las conexiones si detectas múltiples eventos de fuga en la misma hora.")
else:
    st.success("✅ No se han detectado anomalías en el flujo de agua hasta el momento.")

# Auto-refresh
if st.session_state.corriendo:
    time.sleep(1)
    st.rerun()
