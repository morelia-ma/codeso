import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página y carga de datos
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

@st.cache_data
def load_all_data():
    # Asegúrate de que los nombres de archivos coincidan con tus archivos locales
    df_gen = pd.read_csv('datos_domotia_final_2.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    
    try:
        df_al = pd.read_csv('alertas_historico_2.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except:
        df_al = pd.DataFrame(columns=['timestamp', 'mensaje', 'tipo_anomalia_real', 'valor'])
    
    return df_gen, df_al

df, df_alertas = load_all_data()

# 2. Inicialización de Estado
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

t_actual = df.iloc[st.session_state.indice]['timestamp']

# --- SIDEBAR: PANEL DE CONTROL ---
st.sidebar.title("🕹️ Panel de Control")
if st.sidebar.button("▶️ Iniciar / ⏸️ Pausar"):
    st.session_state.corriendo = not st.session_state.corriendo

if st.sidebar.button("🔄 Reiniciar Simulación"):
    st.session_state.indice = 0
    st.session_state.corriendo = False
    st.rerun()

# --- SIDEBAR: LÓGICA DE ALARMAS NO REPETITIVAS ---
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Recientes (24h)")
un_dia_atras = t_actual - timedelta(days=1)

# Filtramos alertas de las últimas 24h
alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)].copy()

if not alertas_24h.empty:
    # Agrupamos por día y tipo para evitar repeticiones visuales de gas
    # Solo tomamos la alarma con el valor más alto por cada hora para evitar saturación de 30 min
    alertas_24h['fecha_hora'] = alertas_24h['timestamp'].dt.floor('H')
    alertas_filtradas = alertas_24h.sort_values('valor', ascending=False).drop_duplicates(subset=['fecha_hora', 'tipo_anomalia_real'])
    
    for _, row in alertas_filtradas.sort_values('timestamp', ascending=False).iterrows():
        tipo = str(row.get('tipo_anomalia_real', '')).lower()
        msj = str(row.get('mensaje', '')).upper()
        
        # Estilo según tipo
        clase = "falla-gas" if "gas" in tipo else "falla-agua" if "agua" in tipo else "falla-luz"
        icono = "🔥" if "gas" in tipo else "💧" if "agua" in tipo else "⚡"
        
        st.sidebar.markdown(f"""
            <div class='bitacora-item'>
                <small>{row['timestamp'].strftime('%H:%M')}</small> - <span class='{clase}'>⚠️ {msj}</span>
            </div>
        """, unsafe_allow_html=True)

# --- ÁREA DE TRABAJO PRINCIPAL (Usando st.empty para evitar duplicados) ---
placeholder = st.empty()

with placeholder.container():
    if st.session_state.vista_actual == "principal":
        st.title("🏠 Dashboard CODESO Smart Home")
        
        # KPIs y Gráficas (Tu lógica actual de visualización)
        idx = st.session_state.indice
        actual = df.iloc[idx]
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}")
        k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
        k3.metric("GAS % 🔥", f"{actual['gas_nivel']:.1f}%")
        k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

        st.divider()
        
        # Gráficas
        ventana = df.iloc[max(0, idx-50):idx+1]
        g1, g2 = st.columns(2)
        with g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
        with g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

        st.divider()
        
        # BOTONES DE NAVEGACIÓN (Solo una vez)
        c_nav1, c_nav2 = st.columns(2)
        if c_nav1.button("📊 Ver Datos de Consumo Almacenados", use_container_width=True):
            st.session_state.vista_actual = "datos"
            st.rerun()
        if c_nav2.button("📜 Ver Historial de Alarmas", use_container_width=True):
            st.session_state.vista_actual = "alarmas"
            st.rerun()

    elif st.session_state.vista_actual == "datos":
        st.subheader("🔍 Explorador de Consumo Histórico")
        if st.button("⬅️ Volver al Panel"):
            st.session_state.vista_actual = "principal"
            st.rerun()
        # (Aquí va tu tabla de datos con estilo rojo)
        st.dataframe(df[df['timestamp'] <= t_actual].tail(100), use_container_width=True)

    elif st.session_state.vista_actual == "alarmas":
        st.subheader("📜 Historial de Alarmas Registradas")
        if st.button("⬅️ Volver al Panel"):
            st.session_state.vista_actual = "principal"
            st.rerun()
        st.table(df_alertas[df_alertas['timestamp'] <= t_actual])

# --- MOTOR DE SIMULACIÓN ---
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1) # Ajusta la velocidad aquí
    st.rerun()
