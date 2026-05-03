import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# 2. Estilos CSS
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
    .gas-container {
        height: 200px; width: 100%; background-color: #f0f2f6;
        border-radius: 10px; position: relative; border: 1px solid #ddd;
    }
    .gas-fill { background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; transition: height 0.3s; }
    .gas-label { position: absolute; width: 100%; text-align: center; top: 40%; font-weight: bold; font-size: 1.6rem; z-index: 2; }
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

# --- LÓGICA DE TIEMPO REAL ---
if not df.empty:
    # Definimos el "presente" de la simulación
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

# --- VISTAS ---
if not df.empty:
    
    # --- VISTA: HISTORIAL DE DATOS (CON FILTRO DE TIEMPO REAL) ---
    if st.session_state.vista == "datos":
        st.markdown("## 📊 Historial de Consumo")
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"
            st.rerun()
        
        # Filtramos el dataframe original para que solo existan datos hasta el "presente"
        df_hasta_ahora = df[df['timestamp'] <= t_presente]
        
        with st.container():
            st.info(f"Consulta datos registrados hasta: **{t_presente.strftime('%d/%m/%Y %H:%M')}**")
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                # Solo meses que ya ocurrieron
                meses_disponibles = df_hasta_ahora['timestamp'].dt.month_name().unique()
                mes_sel = st.selectbox("Seleccionar Mes", options=meses_disponibles)
            
            with col_f2:
                # Solo días de ese mes que ya ocurrieron
                dias_disponibles = df_hasta_ahora[df_hasta_ahora['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique()
                dia_sel = st.selectbox("Seleccionar Día", options=dias_disponibles)
            
            df_filtrado = df_hasta_ahora[(df_hasta_ahora['timestamp'].dt.month_name() == mes_sel) & 
                                        (df_hasta_ahora['timestamp'].dt.day == dia_sel)]
            
            st.write(f"Mostrando registros del **{dia_sel} de {mes_sel}**:")
            st.dataframe(df_filtrado, use_container_width=True)

    # --- VISTA: PANEL PRINCIPAL ---
    elif st.session_state.vista == "principal":
        actual = df.iloc[st.session_state.indice]
        st.markdown(f"## 🏠 Monitoreo: Familia Montoya")

        # Fila 1: Indicadores
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

        # Fila 2: Gráficas y Gas
        col_graf, col_gas = st.columns([4, 1.2])
        ventana = df.iloc[max(0, st.session_state.indice-30):st.session_state.indice+1].set_index('timestamp')

        with col_graf:
            g1, g2 = st.columns(2)
            with g1:
                st.caption("📈 Histórico Agua")
                st.area_chart(ventana['consumo_agua'], height=210)
            with g2:
                st.caption("📈 Histórico Energía")
                st.line_chart(ventana['consumo_electrico'], height=210, color="#FFB703")

        with col_gas:
            st.caption("⛽ Nivel de Gas")
            v_gas = actual['gas_nivel']
            st.markdown(f'<div class="gas-container"><div class="gas-label">{v_gas:.1f}%</div><div class="gas-fill" style="height: {v_gas}%;"></div></div>', unsafe_allow_html=True)

        # Fila 3: Botones
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("📊 Historial Datos", use_container_width=True):
            st.session_state.vista = "datos"
            st.rerun()
        if b2.button("🚨 Historial Alarmas", use_container_width=True):
            st.session_state.vista = "alarmas"
            st.rerun()
        if b3.button("📞 Directorio", use_container_width=True):
            st.session_state.vista = "directorio"
            st.rerun()
        b4.button("⚙️ Info General", use_container_width=True, disabled=True)

# Loop
if st.session_state.corriendo and st.session_state.vista == "principal" and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
