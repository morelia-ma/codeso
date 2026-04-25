import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import plotly.graph_objects as go
from threading import Thread
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Centro de Control CODESO", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #2e5a88;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO (Session State) ---
if 'db_simulacion' not in st.session_state:
    st.session_state.db_simulacion = pd.DataFrame(columns=['Timestamp', 'Agua', 'Energia', 'Gas', 'Temp'])
if 'ejecutando' not in st.session_state:
    st.session_state.ejecutando = False
if 'indice_actual' not in st.session_state:
    st.session_state.indice_actual = 0

# --- FUNCIONES DE LÓGICA ---

def guardar_datos_mensuales(df):
    """Guarda los datos en un CSV basado en el mes actual"""
    if not os.path.exists('data'):
        os.makedirs('data')
    nombre_archivo = f"data/registro_{datetime.now().strftime('%Y_%m')}.csv"
    # Si ya existe, añade sin cabecera. Si no, crea nuevo.
    df.to_csv(nombre_archivo, mode='a', header=not os.path.exists(nombre_archivo), index=False)

def simular_paso():
    """Simula la llegada de un nuevo dato cada segundo"""
    while st.session_state.ejecutando:
        # Aquí es donde integrarías los datos de tu compañera
        nuevo_dato = {
            'Timestamp': datetime.now().strftime("%H:%M:%S"),
            'Agua': np.random.uniform(5, 15), # Simulación
            'Energia': np.random.uniform(0.1, 0.9),
            'Gas': np.random.uniform(90, 99),
            'Temp': np.random.uniform(14, 25)
        }
        
        # Actualizar dataframe en memoria
        df_nuevo = pd.DataFrame([nuevo_dato])
        st.session_state.db_simulacion = pd.concat([st.session_state.db_simulacion, df_nuevo], ignore_index=True)
        st.session_state.indice_actual += 1
        
        # Guardar cada 10 registros para no perder info
        if st.session_state.indice_actual % 10 == 0:
            guardar_datos_mensuales(df_nuevo)
            
        time.sleep(1) 

# --- INTERFAZ - BARRA LATERAL ---
st.sidebar.title("🕹️ Panel de Control")

if st.sidebar.button("▶️ Iniciar Simulación"):
    st.session_state.ejecutando = True
    # Iniciar hilo para que no bloquee la UI
    Thread(target=simular_paso).start()

if st.sidebar.button("⏹️ Detener"):
    st.session_state.ejecutando = False

st.sidebar.divider()
st.sidebar.write(f"**Registro actual:** {st.session_state.indice_actual}")
st.sidebar.caption("El registro representa el número de muestras capturadas en la sesión actual (Segundos/Lecturas).")

# --- SECCIÓN DE CARPETAS (HISTORIAL) ---
st.sidebar.header("📂 Historial por Mes")
archivos = [f for f in os.listdir('data') if f.endswith('.csv')] if os.path.exists('data') else []

if archivos:
    archivo_sel = st.sidebar.selectbox("Ver registros pasados:", archivos)
    if st.sidebar.button("Ver Gráficas Históricas"):
        df_hist = pd.read_csv(f"data/{archivo_sel}")
        st.session_state.vista_historial = df_hist
else:
    st.sidebar.info("No hay archivos de meses previos.")

# --- CUERPO PRINCIPAL ---
st.title("🏠 Centro de Control Residencial - CODESO")

# Métrica de KPIs (Fila superior)
col1, col2, col3, col4 = st.columns(4)

if not st.session_state.db_simulacion.empty:
    ult = st.session_state.db_simulacion.iloc[-1]
    col1.metric("AGUA 💧", f"{ult['Agua']:.1f} L", "-4.1 L")
    col2.metric("ENERGÍA ⚡", f"{ult['Energia']:.3f} kWh", "0.078 kWh")
    col3.metric("GAS LP 🔥", f"{ult['Gas']:.0f}%")
    col4.metric("TEMP 🌡️", f"{ult['Temp']:.1f} °C")
else:
    st.info("Presiona 'Iniciar' para recibir datos en tiempo real.")

# --- GRÁFICAS EN TIEMPO REAL ---
st.divider()
if not st.session_state.db_simulacion.empty:
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("### Consumo de Agua (Tiempo Real)")
        st.area_chart(st.session_state.db_simulacion.set_index('Timestamp')['Agua'])
        
    with c2:
        st.write("### Demanda Energética (Tiempo Real)")
        st.line_chart(st.session_state.db_simulacion.set_index('Timestamp')['Energia'])

# --- SECCIÓN HISTÓRICA (LO QUE PEDISTE DEL MES) ---
if 'vista_historial' in st.session_state:
    st.divider()
    st.header(f"📊 Análisis Mensual: {archivo_sel}")
    
    df_h = st.session_state.vista_historial
    
    # Gráfica de barras para consumo diario (Simulada con los datos del CSV)
    fig_barras = go.Figure(data=[
        go.Bar(name='Agua', x=df_h['Timestamp'], y=df_h['Agua'], marker_color='#1f77b4'),
        go.Bar(name='Energía', x=df_h['Timestamp'], y=df_h['Energia'], marker_color='#ff7f0e')
    ])
    fig_barras.update_layout(barmode='group', title="Comparativa de Consumo por Registro")
    st.plotly_chart(fig_barras, use_container_width=True)

# Auto-refresh de la página para ver los datos moverse
if st.session_state.ejecutando:
    time.sleep(1)
    st.rerun()
