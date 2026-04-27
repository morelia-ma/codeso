import streamlit as st
import pandas as pd
import time
import os
from datetime import timedelta

# 1. Configuración
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
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
        df_al = pd.DataFrame(columns=['timestamp', 'sensor', 'mensaje', 'tipo_anomalia_real'])
        
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la Sesión (Navegación de Botones)
if 'indice' not in st.session_state: st.session_state.indice = 1
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'gas_rellenado' not in st.session_state: st.session_state.gas_rellenado = 0
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

# --- SIDEBAR ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False
if st.sidebar.button("🔄 Reiniciar"):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()

# Bitácora Izquierda (Alertas 24h)
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Activas (24h)")
t_simulacion = df.iloc[st.session_state.indice]['timestamp']
un_dia_atras = t_simulacion - timedelta(days=1)

alertas_activas = df_alertas[(df_alertas['timestamp'] <= t_simulacion) & (df_alertas['timestamp'] >= un_dia_atras)]

if not alertas_activas.empty:
    for _, row in alertas_activas.iloc[::-1].iterrows():
        # Traductor de Fallos para evitar NaNs
        tipo_r = str(row.get('tipo_anomalia_real', '')).upper()
        msj = str(row.get('mensaje', '')).upper()
        if "AGUA" in tipo_r or "AGUA" in msj: final_t, clase = "AGUA", "falla-agua"
        elif "GAS" in tipo_r or "GAS" in msj: final_t, clase = "GAS", "falla-gas"
        else: final_t, clase = "LUZ", "falla-luz"
        st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp']}</small><br><span class='{clase}'>⚠️ FALLO DE {final_t}</span></div>", unsafe_allow_html=True)

# --- CUERPO PRINCIPAL ---
st.title("🏠 Dashboard CODESO Smart Home")

i = st.session_state.indice
actual = df.iloc[i]
anterior = df.iloc[i-1]

# Lógica Gas
nivel_real = actual['gas_nivel'] - st.session_state.gas_rellenado
if nivel_real <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0
    nivel_real = 100.0

# KPIs y Gráficas (Solo se ven en vista principal)
if st.session_state.vista_actual == "principal":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}")
    k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
    k3.metric("GAS % 🔥", f"{nivel_real:.1f}%")
    k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    if nivel_real <= 10.0: st.warning(f"⚠️ BAJO NIVEL DE GAS: {nivel_real:.1f}%")
    
    st.divider()
    ventana = df.iloc[max(0, i-50):i+1]
    g1, g2 = st.columns(2)
    with g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    with g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

# --- SECCIÓN DE BOTONES E HISTORIALES ---
st.divider()

if st.session_state.vista_actual == "principal":
    b1, b2 = st.columns(2)
    if b1.button("📊 Ver Datos de Consumo Almacenados", use_container_width=True):
        st.session_state.vista_actual = "datos"
        st.rerun()
    if b2.button("📜 Ver Historial de Alarmas", use_container_width=True):
        st.session_state.vista_actual = "alarmas"
        st.rerun()

# VISTA DE DATOS CON FILTRO DE FECHA
elif st.session_state.vista_actual == "datos":
    st.subheader("🔍 Explorador de Consumo Histórico")
    
    # Selectores de Fecha
    col_mes, col_dia, col_back = st.columns([2, 2, 1])
    
    meses_disp = df['timestamp'].dt.month_name().unique()
    mes_sel = col_mes.selectbox("Selecciona el Mes", meses_disp)
    
    df_mes = df[df['timestamp'].dt.month_name() == mes_sel]
    dias_disp = df_mes['timestamp'].dt.day.unique()
    dia_sel = col_dia.selectbox("Selecciona el Día", sorted(dias_disp))
    
    if col_back.button("⬅️ Volver", use_container_width=True):
        st.session_state.vista_actual = "principal"
        st.rerun()
    
    # Filtrado final
    resultado = df_mes[df_mes['timestamp'].dt.day == dia_sel]
    st.dataframe(resultado[['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel', 'temperatura_int']], use_container_width=True)

# VISTA DE HISTORIAL DE ALARMAS
elif st.session_state.vista_actual == "alarmas":
    st.subheader("📜 Historial Completo de Incidencias")
    
    if st.button("⬅️ Volver a Panel Principal"):
        st.session_state.vista_actual = "principal"
        st.rerun()
    
    hist_total = df_alertas[df_alertas['timestamp'] <= t_simulacion].copy()
    st.table(hist_total[['timestamp', 'sensor', 'mensaje', 'tipo_anomalia_real']])

# Motor de Simulación
if st.session_state.corriendo and i < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
