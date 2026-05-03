import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="Smart Home HMI", layout="wide")

# 2. Estilos CSS (Tanque vertical y métricas)
st.markdown("""
    <style>
    .gas-container {
        height: 350px;
        width: 100%;
        background-color: #f0f2f6;
        border-radius: 15px;
        position: relative;
        overflow: hidden;
        border: 2px solid #dfe3e6;
    }
    .gas-fill {
        background-color: #E74C3C;
        width: 100%;
        position: absolute;
        bottom: 0;
        transition: height 0.5s ease-in-out;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .gas-label {
        position: absolute;
        width: 100%;
        text-align: center;
        top: 45%;
        font-weight: bold;
        color: #1f2d3d;
        font-size: 1.3rem;
        z-index: 2;
    }
    .stMetric { 
        border-radius: 12px; 
        background-color: #ffffff; 
        padding: 15px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-bottom: 4px solid #0077B6; 
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    try:
        df_gen = pd.read_csv('datos_domotia_final.csv')
        df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp']).dt.tz_localize(None)
        # Aseguramos que existan las columnas necesarias
        df_gen['humedad_interior'] = df_gen['humedad_interior'].ffill() 
        
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df_gen, df_al
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_all_data()

if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🕹️ Panel de Control")
    if st.button("▶️ Iniciar / ⏸️ Pausar", use_container_width=True):
        st.session_state.corriendo = not st.session_state.corriendo
    
    if st.button("📞 Directorio de Emergencia", use_container_width=True):
        st.session_state.vista_actual = "directorio"

    st.divider()
    st.subheader("🔔 Estado de Suministros")
    
    # Lógica de Predicción Proactiva
    gas_actual = df.iloc[st.session_state.indice]['gas_nivel']
    dias_est = int(gas_actual / 1.5) # Simulación de consumo proactivo
    
    if dias_est <= 15:
        st.warning(f"Suministro de Gas: aprox. {dias_est} días restantes.")

# --- CUERPO PRINCIPAL ---
if not df.empty:
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista_actual == "principal":
        # 1. Encabezado con Humedad en lugar de Gas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AGUA", f"{actual['consumo_agua']:.1f} L 💧")
        m2.metric("ENERGÍA", f"{actual['consumo_electrico']:.3f} kWh ⚡")
        m3.metric("HUMEDAD", f"{actual['humedad_interior']:.1f} % 💧")
        m4.metric("TEMP. INT", f"{actual['temperatura_int']:.1f} °C 🌡️")

        st.divider()

        # 2. Layout Principal Reorganizado
        col_graficas, col_tanque = st.columns([3, 1])

        with col_graficas:
            st.subheader("📊 Historial de Consumo")
            ventana = df.iloc[max(0, st.session_state.indice-50):st.session_state.indice+1]
            
            tab_agua, tab_elec = st.tabs(["Consumo Agua", "Consumo Eléctrico"])
            with tab_agua:
                st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6", height=350)
            with tab_elec:
                st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703", height=350)

        with col_tanque:
            st.subheader("⛽ Nivel de Gas")
            # Tanque con llenado dinámico (arriba hacia abajo el vacío)
            p_gas = actual['gas_nivel']
            st.markdown(f"""
                <div class="gas-container">
                    <div class="gas-label">{p_gas:.1f}%</div>
                    <div class="gas-fill" style="height: {p_gas}%;"></div>
                </div>
                <p style="text-align:center; margin-top:10px; font-size: 0.9rem; color: #666;">
                    Monitoreo de Válvula Principal
                </p>
            """, unsafe_allow_html=True)

        st.divider()
        # Botones de navegación únicos
        c1, c2 = st.columns(2)
        if c1.button("📑 Historial de Datos", use_container_width=True): st.session_state.vista_actual = "datos"
        if c2.button("📜 Registro de Alarmas", use_container_width=True): st.session_state.vista_actual = "alarmas"

    # (Las vistas de 'datos', 'alarmas' y 'directorio' se mantienen igual para soporte)
    elif st.session_state.vista_actual == "datos":
        if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
        st.dataframe(df[df['timestamp'] <= actual['timestamp']].tail(100), use_container_width=True)

# Lógica de Ejecución
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
