import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# 2. Estilos CSS (Actualizado para alineación y diseño)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .spacer { margin-top: 30px; }
    
    .metric-card {
        background-color: white; border-radius: 10px; padding: 12px 18px;
        border-left: 5px solid #0077B6; box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        height: 100px;
    }
    .metric-title { font-size: 0.75rem; font-weight: bold; color: #666; text-transform: uppercase; }
    .metric-value { font-size: 1.9rem; font-weight: 500; color: #1f2d3d; }
    
    .gas-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .gas-container {
        height: 200px; width: 60px; background-color: #f0f2f6;
        border-radius: 30px; position: relative; border: 2px solid #ddd;
        overflow: hidden;
    }
    .gas-fill { background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; transition: height 0.5s ease-in-out; }
    .gas-percentage { font-weight: bold; font-size: 1.2rem; color: #1f2d3d; margin-top: 10px; }
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

# Estado de la sesión
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

if not df.empty:
    t_presente = df.iloc[st.session_state.indice]['timestamp']

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
        alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_presente) & 
                                 (df_alertas['timestamp'] >= t_presente - timedelta(hours=24))]
        for msg in alertas_24h['mensaje'].unique()[-4:]:
            st.caption(f"⚠️ {msg}")

# --- NAVEGACIÓN Y VISTAS ---
if not df.empty:
    
    # VISTA: HISTORIAL DE DATOS
    if st.session_state.vista == "datos":
        st.markdown("## 📊 Historial de Consumo")
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"
            st.rerun()
        
        df_hasta_ahora = df[df['timestamp'] <= t_presente]
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            mes_sel = st.selectbox("Seleccionar Mes", options=df_hasta_ahora['timestamp'].dt.month_name().unique())
        with col_f2:
            dias = df_hasta_ahora[df_hasta_ahora['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique()
            dia_sel = st.selectbox("Seleccionar Día", options=dias)
        
        st.dataframe(df_hasta_ahora[(df_hasta_ahora['timestamp'].dt.month_name() == mes_sel) & 
                                   (df_hasta_ahora['timestamp'].dt.day == dia_sel)], use_container_width=True)

    # VISTA: HISTORIAL DE ALARMAS (CORREGIDO)
    elif st.session_state.vista == "alarmas":
        st.markdown("## 🚨 Histórico de Alertas")
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"
            st.rerun()
        
        filtro_alertas = df_alertas[df_alertas['timestamp'] <= t_presente].sort_values(by='timestamp', ascending=False)
        if not filtro_alertas.empty:
            st.table(filtro_alertas)
        else:
            st.info("No hay alertas registradas hasta el momento.")

    # VISTA: DIRECTORIO (CORREGIDO)
    elif st.session_state.vista == "directorio":
        st.markdown("## 📞 Directorio de Emergencia")
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"
            st.rerun()
        st.table(pd.DataFrame([
            {"Contacto": "Protección Civil", "Número": "911"},
            {"Contacto": "Mantenimiento Gas", "Número": "01-800-GAS-SERV"},
            {"Contacto": "Suministro Agua", "Número": "555-0192"}
        ]))

    # VISTA: PANEL PRINCIPAL
    elif st.session_state.vista == "principal":
        actual = df.iloc[st.session_state.indice]
        st.markdown(f"## 🏠 Monitoreo: Familia Montoya")

        # Indicadores Superiores
        m1, m2, m3, m4 = st.columns(4)
        indicadores = [
            ("Agua (L) 💧", actual["consumo_agua"], "{:.1f}"),
            ("Energía (kWh) ⚡", actual["consumo_electrico"], "{:.3f}"),
            ("Humedad (%) ☁️", actual["humedad_interior"], "{:.1f}"),
            ("Temp. Int (°C) 🌡️", actual["temperatura_int"], "{:.1f}")
        ]
        for i, (titulo, valor, form) in enumerate(indicadores):
            with [m1, m2, m3, m4][i]:
                st.markdown(f'<div class="metric-card"><div class="metric-title">{titulo}</div><div class="metric-value">{form.format(valor)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

        # Gráficas y Gas con altura igualada
        col_graf, col_gas = st.columns([4, 0.8])
        ventana = df.iloc[max(0, st.session_state.indice-30):st.session_state.indice+1].set_index('timestamp')

        with col_graf:
            g1, g2 = st.columns(2)
            with g1:
                st.caption("📈 Histórico Agua")
                st.area_chart(ventana['consumo_agua'], height=250) # Altura igualada
            with g2:
                st.caption("📈 Histórico Energía")
                st.line_chart(ventana['consumo_electrico'], height=250, color="#FFB703") # Altura igualada

        with col_gas:
            st.caption("⛽ Nivel de Gas")
            v_gas = actual['gas_nivel']
            st.markdown(f"""
                <div class="gas-wrapper">
                    <div class="gas-container"><div class="gas-fill" style="height: {v_gas}%;"></div></div>
                    <div class="gas-percentage">{v_gas:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        # Botones de navegación
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("📊 Historial Datos", use_container_width=True):
            st.session_state.vista = "datos"; st.rerun()
        if b2.button("🚨 Historial Alarmas", use_container_width=True):
            st.session_state.vista = "alarmas"; st.rerun()
        if b3.button("📞 Directorio", use_container_width=True):
            st.session_state.vista = "directorio"; st.rerun()
        b4.button("⚙️ Info General", use_container_width=True, disabled=True)

# Loop de simulación
if st.session_state.corriendo and st.session_state.vista == "principal" and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
