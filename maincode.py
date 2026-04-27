import streamlit as st
import pandas as pd
import time
import os

# 1. Configuración de pantalla
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS (Semiótica y Interfaz limpia)
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de datos unificada
@st.cache_data
def load_all_data():
    # Carga de datos generales
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    
    # REGLA DEL GAS: Rellenar huecos para que el porcentaje baje sin saltar
    if 'gas_nivel' in df_gen.columns:
        df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9) # Empieza en 99.9 si el primer dato es nulo
    
    # Carga de alertas históricas
    try:
        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except Exception:
        df_al = None
        
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la sesión
if 'indice' not in st.session_state:
    st.session_state.indice = 1
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False

# --- SIDEBAR (Panel de Control y Monitor para TI) ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False

if st.sidebar.button("🔄 Reiniciar"):
    st.session_state.corriendo = False
    st.session_state.indice = 1
    st.rerun()

# Monitor de progreso (Para que sepas cuánto falta)
st.sidebar.divider()
total_f = len(df)
curr_f = st.session_state.indice
st.sidebar.write(f"📊 **Dato:** {curr_f} / {total_f}")
st.sidebar.progress(curr_f / total_f)

# Bitácora Dinámica (Lee de alertas_historico conforme avanza el tiempo)
st.sidebar.divider()
st.sidebar.subheader("📋 Bitácora de Alarmas")
if df_alertas is not None:
    t_actual = df.iloc[curr_f]['timestamp']
    # Filtrar alertas que ya ocurrieron hasta este momento de la simulación
    pasadas = df_alertas[df_alertas['timestamp'] <= t_actual].tail(5)
    for _, row in pasadas.iloc[::-1].iterrows():
        tipo = str(row.get('tipo_anomalia_real', 'Alerta')).upper()
        clase = "falla-agua" if "AGUA" in tipo else "falla-luz" if "ELEC" in tipo else "falla-gas"
        st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp']}</small><br><span class='{clase}'>⚠️ {tipo}</span></div>", unsafe_allow_html=True)

# --- CUERPO PRINCIPAL ---
st.title("🏠 HMI Domótica Inteligente")

if df is not None:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    ventana = df.iloc[max(0, i-40):i+1] # Ventana de tiempo para gráficas

    # KPIs Principales
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}", delta_color="inverse")
    k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
    
    # 🔥 GAS (Ya no se regresa a 94 por el ffill() de arriba)
    gas_val = actual['gas_nivel']
    k3.metric("NIVEL GAS %", f"{gas_val:.2f}%", "-0.01%")
    
    k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Alertas en tiempo real (Sincronizadas con la columna anomalia de datos_final)
    if str(actual['anomalia']).lower() == 'true':
        tipo_f = str(actual['tipo_anomalia']).upper()
        st.error(f"🚨 **ANOMALÍA EN VIVO:** {tipo_f} detectada en {actual['timestamp']}")

    # Gráficas (UNA SOLA FILA, SIN DUPLICADOS)
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Consumo Hídrico")
        st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    with g2:
        st.subheader("Demanda Eléctrica")
        st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

    # Motor de la simulación
    if st.session_state.corriendo and i < len(df) - 1:
        st.session_state.indice += 1
        time.sleep(0.3)
        st.rerun()
