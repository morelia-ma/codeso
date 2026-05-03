import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página (Layout wide y sin scroll excesivo)
st.set_page_config(page_title="Smart Home HMI", layout="wide", initial_sidebar_state="expanded")

# 2. Estilos CSS para compactar y embellecer
st.markdown("""
    <style>
    /* Compactar márgenes y espacios */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    .stMetric { padding: 5px !important; }
    
    /* Tanque de Gas Compacto */
    .gas-container {
        height: 220px; width: 100%; background-color: #f0f2f6;
        border-radius: 10px; position: relative; border: 1px solid #ccc;
        margin-top: 10px;
    }
    .gas-fill {
        background-color: #2ECC71; width: 100%; position: absolute;
        bottom: 0; transition: height 0.5s;
    }
    .gas-label {
        position: absolute; width: 100%; text-align: center;
        top: 40%; font-weight: bold; font-size: 1.5rem; color: #1f2d3d; z-index: 2;
    }
    
    /* Cuadros de métricas superiores limpios */
    .metric-card {
        background-color: #E5E7E9; padding: 10px; border-radius: 10px;
        text-align: center; border: 1px solid #BDC3C7;
    }
    .metric-card h3 { margin: 0; font-size: 1.1rem; color: #2C3E50; }
    .metric-card p { margin: 0; font-size: 1.3rem; font-weight: bold; color: #2980B9; }
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

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎮 Simulación")
    c1, c2 = st.columns(2)
    if c1.button("▶️ Inicio/Pausa", use_container_width=True):
        st.session_state.corriendo = not st.session_state.corriendo
    if c2.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    st.markdown("---")
    st.subheader("🔔 Alertas (24h)")
    if not df.empty:
        t_actual = df.iloc[st.session_state.indice]['timestamp']
        # Filtro: Últimas 24h Y eliminar duplicados del mismo mensaje
        alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & 
                                 (df_alertas['timestamp'] >= t_actual - timedelta(hours=24))]
        alertas_unicas = alertas_24h.drop_duplicates(subset=['mensaje'], keep='last')
        
        if not alertas_unicas.empty:
            for _, row in alertas_unicas.iterrows():
                st.caption(f"📍 {row['mensaje']}")
        else:
            st.write("✅ Todo en orden")

# --- CUERPO PRINCIPAL ---
if not df.empty:
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista == "principal":
        st.subheader("🏠 Monitoreo: Familia Montoya")

        # Fila 1: Métricas Superiores Compactas
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-card"><h3>💧 Agua</h3><p>{actual["consumo_agua"]:.1f} L</p></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card"><h3>⚡ Energía</h3><p>{actual["consumo_electrico"]:.2f} kWh</p></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card"><h3>☁️ Humedad</h3><p>{actual["humedad_interior"]:.1f} %</p></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card"><h3>🌡️ Temp.</h3><p>{actual["temperatura_int"]:.1f} °C</p></div>', unsafe_allow_html=True)

        # Fila 2: Gráficas y Gas (Plano medio)
        col_graficas, col_gas = st.columns([4, 1])
        ventana = df.iloc[max(0, st.session_state.indice-25):st.session_state.indice+1].set_index('timestamp')

        with col_graficas:
            g1, g2 = st.columns(2)
            with g1:
                st.caption("Consumo de Agua (L)")
                st.area_chart(ventana['consumo_agua'], height=220, use_container_width=True)
            with g2:
                st.caption("Consumo Eléctrico (kWh)")
                st.line_chart(ventana['consumo_electrico'], height=220, use_container_width=True, color="#FFB703")

        with col_gas:
            st.caption("⛽ Nivel de Gas")
            # Validación para evitar NaN
            val_gas = actual['gas_nivel'] if pd.notnull(actual['gas_nivel']) else 0
            st.markdown(f"""
                <div class="gas-container">
                    <div class="gas-label">{val_gas:.1f}%</div>
                    <div class="gas-fill" style="height: {val_gas}%;"></div>
                </div>
            """, unsafe_allow_html=True)

        # Fila 3: Navegación Inferior (Plano final)
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("📊 Historial Datos", use_container_width=True): st.session_state.vista = "datos"
        if b2.button("🚨 Historial Alarmas", use_container_width=True): st.session_state.vista = "alarmas"
        if b3.button("📞 Directorio", use_container_width=True): st.session_state.vista = "directorio"
        b4.button("⚙️ Info General", use_container_width=True, disabled=True)

    # Vistas secundarias compactas
    elif st.session_state.vista == "directorio":
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.table(pd.DataFrame([{"Servicio": "Emergencias", "Tel": "911"}, {"Servicio": "Gas Natural", "Tel": "01-800-GAS"}]))

    elif st.session_state.vista == "datos":
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.dataframe(df[df['timestamp'] <= t_actual].tail(30), use_container_width=True)

    elif st.session_state.vista == "alarmas":
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.dataframe(df_alertas[df_alertas['timestamp'] <= t_actual].tail(20), use_container_width=True)

# Loop de simulación
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
