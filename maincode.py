import streamlit as st
import pandas as pd
import time
import os
from datetime import timedelta

# 1. Configuración
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS (Semiótica de colores)
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga y Limpieza de Datos
@st.cache_data
def load_all_data():
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)
    
    try:
        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except:
        df_al = pd.DataFrame(columns=['timestamp', 'tipo_anomalia_real', 'sensor', 'mensaje'])
        
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 1
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'gas_rellenado' not in st.session_state: st.session_state.gas_rellenado = 0

# --- SIDEBAR (Panel de Control y Alertas Inteligentes) ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False
if st.sidebar.button("🔄 Reiniciar"):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()

st.sidebar.divider()
st.sidebar.write(f"📊 **Dato:** {st.session_state.indice} / {len(df)}")
st.sidebar.progress(st.session_state.indice / len(df))

# --- BITÁCORA DE IZQUIERDA (SIN NaNs) ---
st.sidebar.subheader("🔔 Alertas Activas (24h)")
t_actual = df.iloc[st.session_state.indice]['timestamp']
un_dia_atras = t_actual - timedelta(days=1)

alertas_activas = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)]

if not alertas_activas.empty:
    for _, row in alertas_activas.iloc[::-1].iterrows():
        # LÓGICA PARA EVITAR EL "NaN":
        tipo_raw = str(row.get('tipo_anomalia_real', '')).upper()
        sensor = str(row.get('sensor', '')).upper()
        msj = str(row.get('mensaje', '')).upper()
        
        # Traductor de Fallos
        if "AGUA" in tipo_raw or "AGUA" in sensor or "AGUA" in msj:
            final_type, clase = "AGUA", "falla-agua"
        elif "GAS" in tipo_raw or "GAS" in sensor or "GAS" in msj:
            final_type, clase = "GAS", "falla-gas"
        else:
            final_type, clase = "LUZ", "falla-luz" # Por defecto electricidad si es anomalia

        st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp']}</small><br><span class='{clase}'>⚠️ FALLO DE {final_type}</span></div>", unsafe_allow_html=True)
else:
    st.sidebar.info("Sistemas estables.")

# --- CUERPO PRINCIPAL ---
st.title("🏠 Dashboard CODESO Smart Home")

i = st.session_state.indice
actual = df.iloc[i]
anterior = df.iloc[i-1]

# Lógica de Gas (10% Alerta, 8% Relleno)
nivel_real = actual['gas_nivel'] - st.session_state.gas_rellenado
if nivel_real <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0
    nivel_real = 100.0
    st.toast("🔥 Gas rellenado")

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}")
k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
k3.metric("GAS % 🔥", f"{nivel_real:.1f}%")
k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

if nivel_real <= 10.0 and nivel_real > 8.0:
    st.warning(f"⚠️ BAJO NIVEL DE GAS: {nivel_real:.1f}%")

# Gráficas (UNA SOLA VEZ)
st.divider()
ventana = df.iloc[max(0, i-50):i+1]
g1, g2 = st.columns(2)
with g1:
    st.subheader("Consumo de Agua")
    st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
with g2:
    st.subheader("Demanda Eléctrica")
    st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

# BOTONES DE HISTORIAL
st.divider()
b1, b2 = st.columns(2)
if b1.button("📊 Ver Datos de Consumo"):
    st.dataframe(df[['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel']].head(i))
if b2.button("📜 Ver Historial de Alarmas"):
    # Limpiamos el NaN también en la tabla de historial
    hist = df_alertas[df_alertas['timestamp'] <= t_actual].copy()
    st.table(hist[['timestamp', 'sensor', 'mensaje']])

# Motor
if st.session_state.corriendo and i < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
