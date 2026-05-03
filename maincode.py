import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="Smart Home HMI", layout="wide")

# 2. Estilos CSS para calcar el dibujo
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Contenedor del Tanque de Gas */
    .gas-container {
        height: 300px; width: 100%; background-color: #f0f2f6;
        border-radius: 5px; position: relative; border: 1px solid #ccc;
    }
    .gas-fill {
        background-color: #2ECC71; width: 100%; position: absolute;
        bottom: 0; transition: height 0.5s;
    }
    .gas-label {
        position: absolute; width: 100%; text-align: center;
        top: 45%; font-weight: bold; font-size: 1.2rem; z-index: 2;
    }
    /* Estilo para los cuadros de métricas superiores */
    .metric-box {
        background-color: #d3d3d3; padding: 15px; border-radius: 5px;
        text-align: center; color: #000; font-size: 0.9rem; height: 80px;
        display: flex; align-items: center; justify-content: center;
    }
    /* Sidebar y bordes */
    section[data-testid="stSidebar"] { border-right: 2px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except:
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_data()

# Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# --- SIDEBAR (Panel de Control de Simulación) ---
with st.sidebar:
    st.header("Panel de control de simulación")
    if st.button("Inicio / Pausa", use_container_width=True):
        st.session_state.corriendo = not st.session_state.corriendo
    
    if st.button("Reiniciar", use_container_width=True):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    st.markdown("---")
    st.subheader("🔔 Alertas (Últimas 24h)")
    if not df.empty:
        t_actual = df.iloc[st.session_state.indice]['timestamp']
        alertas_v = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= t_actual - timedelta(hours=24))]
        if not alertas_v.empty:
            for m in alertas_v['mensaje'].tail(5):
                st.caption(f"⚠️ {m}")
        else:
            st.info("Aquí se muestra en tiempo real las alarmas activas en 24 horas.")

# --- CUERPO PRINCIPAL ---
if not df.empty:
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista == "principal":
        st.title("📊 Monitoreo del hogar \"Fam Montoya\"")

        # Fila de métricas (Cuadros grises superiores)
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-box">Consumo de agua:<br><b>{actual["consumo_agua"]:.1f} L</b></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-box">Consumo de energía:<br><b>{actual["consumo_electrico"]:.3f} kWh</b></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-box">Humedad:<br><b>{actual["humedad_interior"]:.1f} %</b></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-box">Temperatura:<br><b>{actual["temperatura_int"]:.1f} °C</b></div>', unsafe_allow_html=True)

        st.write(" ") # Espaciado

        # Fila de Gráficas y Gas
        col_agua, col_luz, col_gas = st.columns([2, 2, 1])
        ventana = df.iloc[max(0, st.session_state.indice-30):st.session_state.indice+1].set_index('timestamp')

        with col_agua:
            st.markdown("**Consumo de Agua (L)**")
            st.area_chart(ventana['consumo_agua'], height=300, use_container_width=True)

        with col_luz:
            st.markdown("**Consumo Eléctrico (kWh)**")
            st.line_chart(ventana['consumo_electrico'], height=300, use_container_width=True, color="#FFB703")

        with col_gas:
            st.markdown("⛽ **Gas**")
            p_gas = float(actual['gas_nivel'])
            st.markdown(f"""
                <div class="gas-container">
                    <div class="gas-label">{p_gas:.1f}%</div>
                    <div class="gas-fill" style="height: {p_gas}%;"></div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        # Fila de botones inferiores
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("Historial de datos según fecha", use_container_width=True): st.session_state.vista = "datos"
        if b2.button("Historial de alarmas según fecha", use_container_width=True): st.session_state.vista = "alarmas"
        if b3.button("Acceder a directorio", use_container_width=True): st.session_state.vista = "directorio"
        b4.button("Editar información general", use_container_width=True, disabled=False) # Solo visualización

    # --- VISTAS SECUNDARIAS ---
    elif st.session_state.vista == "directorio":
        st.subheader("📞 Directorio")
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.info("Espacio para gestión de contactos (Emergencia, Agua, Luz, Gas, Bomberos)")

    elif st.session_state.vista == "datos":
        st.subheader("📑 Historial de Datos")
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.dataframe(df[df['timestamp'] <= t_actual].tail(50), use_container_width=True)

    elif st.session_state.vista == "alarmas":
        st.subheader("📜 Historial de Alarmas")
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.table(df_alertas[df_alertas['timestamp'] <= t_actual].tail(15))

# Loop de simulación
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
