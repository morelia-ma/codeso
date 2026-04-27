import streamlit as st
import pandas as pd
import time
import os
from datetime import timedelta

# 1. Configuración
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS Personalizados
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos y Preprocesamiento
@st.cache_data
def load_all_data():
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    
    # Lógica de gas persistente
    df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)
    
    try:
        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except:
        df_al = pd.DataFrame(columns=['timestamp', 'tipo_anomalia_real'])
        
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la Sesión (Memoria del HMI)
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False
if 'gas_rellenado' not in st.session_state:
    st.session_state.gas_rellenado = 0 # Para simular el cambio de tanque

# --- SIDEBAR (Controles y Alertas Recientes) ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False
if st.sidebar.button("🔄 Reiniciar"):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()

st.sidebar.divider()
st.sidebar.write(f"📊 **Progreso:** {st.session_state.indice} / {len(df)}")
st.sidebar.progress(st.session_state.indice / len(df))

# --- LÓGICA DE ALERTAS EN SIDEBAR (Desaparecen tras 1 día) ---
st.sidebar.subheader("🔔 Alertas Activas (Últimas 24h)")
t_actual = df.iloc[st.session_state.indice]['timestamp']
un_dia_atras = t_actual - timedelta(days=1)

# Filtrar alertas del CSV y alertas de nivel de gas
alertas_activas = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)]

if not alertas_activas.empty:
    for _, row in alertas_activas.iloc[::-1].iterrows():
        tipo = str(row.get('tipo_anomalia_real', 'SISTEMA')).upper()
        clase = "falla-agua" if "AGUA" in tipo else "falla-luz" if "ELEC" in tipo else "falla-gas"
        st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp']}</small><br><span class='{clase}'>⚠️ {tipo}</span></div>", unsafe_allow_html=True)
else:
    st.sidebar.info("No hay alertas pendientes de revisión.")

# --- CUERPO PRINCIPAL ---
st.title("🏠 Dashboard CODESO Smart Home")

i = st.session_state.indice
actual = df.iloc[i].copy()
anterior = df.iloc[i-1]

# --- LÓGICA DE GAS (10% Alerta, 8% Relleno) ---
nivel_real = actual['gas_nivel'] - st.session_state.gas_rellenado # Simulación de consumo acumulado
if nivel_real <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0 # Resetea a 100%
    nivel_real = 100.0
    st.toast("🔥 Tanque de gas reemplazado automáticamente", icon="🚛")

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}")
k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
k3.metric("GAS % 🔥", f"{nivel_real:.1f}%")
k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

# Alertas Críticas en Pantalla
if nivel_real <= 10.0 and nivel_real > 8.0:
    st.warning(f"⚠️ **BAJO NIVEL DE GAS:** {nivel_real:.1f}% - Favor de solicitar recarga.")

if str(actual['anomalia']).lower() == 'true':
    st.error(f"🚨 **ANOMALÍA DETECTADA:** {str(actual['tipo_anomalia']).upper()}")

# --- GRÁFICAS ---
st.divider()
ventana = df.iloc[max(0, i-50):i+1]
g1, g2 = st.columns(2)
with g1:
    st.subheader("Consumo de Agua (Histórico)")
    st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
with g2:
    st.subheader("Demanda Eléctrica (Histórico)")
    st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

# --- NUEVOS BOTONES DE HISTORIAL ---
st.divider()
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("📊 Ver Datos de Consumo Almacenados"):
        st.subheader("Registros Históricos de Recursos")
        st.dataframe(df[['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel']].head(i))

with col_btn2:
    if st.button("📜 Ver Historial Completo de Alarmas"):
        st.subheader("Historial de Incidencias")
        historico_total = df_alertas[df_alertas['timestamp'] <= t_actual]
        st.table(historico_total[['timestamp', 'tipo_anomalia_real', 'mensaje']])

# Motor de simulación
if st.session_state.corriendo and i < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
