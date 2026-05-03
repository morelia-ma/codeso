import streamlit as st
import pandas as pd
import time
import os

# 1. CONFIGURACIÓN
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# Estilos visuales (Tus estilos originales)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background-color: white; border-radius: 10px; padding: 12px 18px;
        border-left: 5px solid #0077B6; box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
    }
    .metric-title { font-size: 0.75rem; font-weight: bold; color: #666; text-transform: uppercase; }
    .metric-value { font-size: 1.9rem; font-weight: 500; color: #1f2d3d; }
    .gas-wrapper { display: flex; flex-direction: column; align-items: center; }
    .gas-container {
        height: 200px; width: 60px; background-color: #f0f2f6;
        border-radius: 30px; position: relative; border: 2px solid #ddd; overflow: hidden;
    }
    .gas-fill { background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS
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

def cargar_directorio():
    if os.path.exists('directorio.csv'): return pd.read_csv('directorio.csv')
    return pd.DataFrame({"Servicio": ["Emergencias"], "Número": ["911"]})

# 3. ESTADO DE SESIÓN
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

df_raw, df_alertas_raw = load_data()

# 4. SIDEBAR (Tu control de siempre)
with st.sidebar:
    st.header("🎮 Control")
    col_a, col_b = st.columns(2)
    if col_a.button("▶️ Iniciar"): st.session_state.corriendo = True
    if col_b.button("🔄 Reiniciar"):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.session_state.vista = "principal"
        st.rerun()
    
    st.markdown("---")
    st.subheader("🔔 Últimas Alertas")
    t_actual = df_raw.iloc[st.session_state.indice]['timestamp']
    alertas = df_alertas_raw[df_alertas_raw['timestamp'] <= t_actual].tail(3)
    for _, fila in alertas.iterrows():
        st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")

# 5. LÓGICA DE VISTAS (Aquí es donde se arregla el "encimado")

# --- SI LA VISTA ES DIRECTORIO ---
if st.session_state.vista == "directorio":
    if st.button("⬅ VOLVER AL PANEL PRINCIPAL"):
        st.session_state.vista = "principal"
        st.rerun()
    
    st.header("📞 Directorio")
    # ... código de formulario y tabla ...
    df_d = cargar_directorio()
    st.data_editor(df_d, use_container_width=True, key="editor_dir")
    
    # ESTE ES EL TRUCO:
    st.stop() # Esto detiene la ejecución aquí. NADA de lo que sigue se dibujará.

# --- SI LA VISTA ES DATOS ---
if st.session_state.vista == "datos":
    if st.button("⬅ VOLVER"):
        st.session_state.vista = "principal"; st.rerun()
    st.header("📊 Historial de Telemetría")
    st.dataframe(df_raw[df_raw['timestamp'] <= t_actual], use_container_width=True)
    st.stop()

# --- SI LA VISTA ES ALARMAS ---
if st.session_state.vista == "alarmas":
    if st.button("⬅ VOLVER"):
        st.session_state.vista = "principal"; st.rerun()
    st.header("🚨 Registro de Alarmas")
    st.table(df_alertas_raw[df_alertas_raw['timestamp'] <= t_actual])
    st.stop()

# --- SI LLEGAMOS AQUÍ, ES LA VISTA PRINCIPAL (EL DASHBOARD QUE YA FUNCIONABA) ---
actual = df_raw.iloc[st.session_state.indice]
df_p = df_raw[df_raw['timestamp'] <= t_actual]

st.title("🏠 Monitoreo Familia Montoya")

# Métricas
m1, m2, m3, m4 = st.columns(4)
m1.markdown(f'<div class="metric-card"><div class="metric-title">AGUA (L) 💧</div><div class="metric-value">{actual["consumo_agua"]:.1f}</div></div>', unsafe_allow_html=True)
m2.markdown(f'<div class="metric-card"><div class="metric-title">ENERGÍA (KWH) ⚡</div><div class="metric-value">{actual["consumo_electrico"]:.3f}</div></div>', unsafe_allow_html=True)
m3.markdown(f'<div class="metric-card"><div class="metric-title">HUMEDAD (%) ☁️</div><div class="metric-value">{actual["humedad_interior"]:.1f}</div></div>', unsafe_allow_html=True)
m4.markdown(f'<div class="metric-card"><div class="metric-title">TEMP (°C) 🌡️</div><div class="metric-value">{actual["temperatura_int"]:.1f}</div></div>', unsafe_allow_html=True)

st.write("") # Espacio

# Gráficos
c_graf, c_gas = st.columns([4, 1])
with c_graf:
    g1, g2 = st.columns(2)
    g1.area_chart(df_p.tail(20).set_index('timestamp')['consumo_agua'])
    g2.line_chart(df_p.tail(20).set_index('timestamp')['consumo_electrico'])

with c_gas:
    st.write("⛽ **Gas**")
    gv = float(actual['gas_nivel'])
    st.markdown(f'<div class="gas-wrapper"><div class="gas-container"><div class="gas-fill" style="height:{gv}%;"></div></div><b>{gv:.1f}%</b></div>', unsafe_allow_html=True)

# BOTONES DE NAVEGACIÓN (Los que me reclamaste que borré)
st.markdown("---")
b1, b2, b3 = st.columns(3)
if b1.button("📊 Ver Datos", use_container_width=True):
    st.session_state.vista = "datos"; st.rerun()
if b2.button("🚨 Ver Alarmas", use_container_width=True):
    st.session_state.vista = "alarmas"; st.rerun()
if b3.button("📞 Directorio", use_container_width=True):
    st.session_state.vista = "directorio"; st.rerun()

# Bucle de animación
if st.session_state.corriendo:
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.05)
        st.rerun()
