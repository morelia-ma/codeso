import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# 2. Estilos CSS (Tarjetas profesionales + Espaciado + Limpieza)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    h2 { margin-top: -10px; margin-bottom: 25px; font-size: 26px !important; }
    
    /* Espaciado entre indicadores y gráficas */
    .spacer { margin-top: 35px; }

    /* Tarjetas estilo profesional con borde azul */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 12px 18px;
        border-left: 5px solid #0077B6;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        height: 100px;
    }
    .metric-title {
        font-size: 0.75rem;
        font-weight: bold;
        color: #666;
        margin-bottom: 5px;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 500;
        color: #1f2d3d;
        margin: 0;
    }

    /* Tanque de Gas */
    .gas-container {
        height: 200px; width: 100%; background-color: #f0f2f6;
        border-radius: 10px; position: relative; border: 1px solid #ddd;
    }
    .gas-fill {
        background-color: #2ECC71; width: 100%; position: absolute;
        bottom: 0; transition: height 0.3s;
    }
    .gas-label {
        position: absolute; width: 100%; text-align: center;
        top: 40%; font-weight: bold; font-size: 1.6rem; color: #1f2d3d; z-index: 2;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df['gas_nivel'] = df['gas_nivel'].ffill().fillna(0)
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except:
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_data()

if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎮 Simulación")
    c1, c2 = st.columns(2)
    if c1.button("▶️ Iniciar", use_container_width=True): st.session_state.corriendo = True
    if c2.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    st.markdown("---")
    st.subheader("🔔 Alertas (24h)")
    if not df.empty:
        t_actual = df.iloc[st.session_state.indice]['timestamp']
        alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & 
                                 (df_alertas['timestamp'] >= t_actual - timedelta(hours=24))]
        for msg in alertas_24h['mensaje'].unique()[-4:]:
            st.caption(f"⚠️ {msg}")

# --- INTERFAZ PRINCIPAL ---
if not df.empty:
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista == "principal":
        st.markdown(f"## 🏠 Monitoreo: Familia Montoya")

        # Fila 1: Indicadores Superiores (Agua, Energía, Humedad, Temperatura)
        m1, m2, m3, m4 = st.columns(4)
        indicadores = [
            ("Agua (L) 💧", actual["consumo_agua"], "{:.1f}"),
            ("Energía (kWh) ⚡", actual["consumo_electrico"], "{:.3f}"),
            ("Humedad (%) ☁️", actual["humedad_interior"], "{:.1f}"),
            ("Temp. Int (°C) 🌡️", actual["temperatura_int"], "{:.1f}")
        ]
        
        for i, (titulo, valor, form) in enumerate(indicadores):
            cols = [m1, m2, m3, m4]
            with cols[i]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">{titulo}</div>
                        <div class="metric-value">{form.format(valor)}</div>
                    </div>
                """, unsafe_allow_html=True)

        # Espacio coherente entre métricas y gráficas
        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

        # Fila 2: Gráficas y Gas
        col_graf, col_gas = st.columns([4, 1.2])
        ventana = df.iloc[max(0, st.session_state.indice-30):st.session_state.indice+1].set_index('timestamp')

        with col_graf:
            g1, g2 = st.columns(2)
            with g1:
                st.caption("📈 Histórico Agua")
                st.area_chart(ventana['consumo_agua'], height=210, use_container_width=True)
            with g2:
                st.caption("📈 Histórico Energía")
                st.line_chart(ventana['consumo_electrico'], height=210, use_container_width=True, color="#FFB703")

        with col_gas:
            st.caption("⛽ Nivel de Tanque de Gas")
            v_gas = actual['gas_nivel']
            st.markdown(f"""
                <div class="gas-container">
                    <div class="gas-label">{v_gas:.1f}%</div>
                    <div class="gas-fill" style="height: {v_gas}%;"></div>
                </div>
            """, unsafe_allow_html=True)

        # Fila 3: Una sola fila de botones (Sin textos extras debajo)
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("📊 Historial Datos", use_container_width=True): st.session_state.vista = "datos"
        if b2.button("🚨 Historial Alarmas", use_container_width=True): st.session_state.vista = "alarmas"
        if b3.button("📞 Directorio", use_container_width=True): st.session_state.vista = "directorio"
        b4.button("⚙️ Info General", use_container_width=True, disabled=True)

    # Vistas Secundarias
    elif st.session_state.vista == "datos":
        if st.button("⬅ Volver"): st.session_state.vista = "principal"; st.rerun()
        st.dataframe(df[df['timestamp'] <= t_actual].tail(50), use_container_width=True)

# Loop de simulación
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
