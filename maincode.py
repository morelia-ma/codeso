import streamlit as st
import pandas as pd
import time
import os
from datetime import timedelta

# 1. Configuración de pantalla
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .falla-agua { color: #0077B6; font-weight: bold; }
    .falla-luz { color: #E67E22; font-weight: bold; }
    .falla-gas { color: #E74C3C; font-weight: bold; }
    .info-sensor { font-size: 0.8rem; color: #666; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    
    # Gas: Identificamos dónde hay silencios antes de rellenar
    df_gen['gas_en_silencio'] = df_gen['gas_nivel'].isna()
    df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)
    
    try:
        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except:
        df_al = pd.DataFrame(columns=['timestamp', 'sensor', 'mensaje', 'tipo_anomalia_real'])
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 1
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'gas_rellenado' not in st.session_state: st.session_state.gas_rellenado = 0
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

t_actual = df.iloc[st.session_state.indice]['timestamp']

# --- SIDEBAR (Panel de Control) ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False
if st.sidebar.button("🔄 Reiniciar"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- BITÁCORA LATERAL (Lógica Estricta de 1 por día) ---
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Activas (24h)")
un_dia_atras = t_actual - timedelta(days=1)
alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)].copy()

if not alertas_24h.empty:
    ya_mostrados_hoy = set()
    for _, row in alertas_24h.iloc[::-1].iterrows():
        tipo_r = str(row.get('tipo_anomalia_real', '')).upper()
        msj = str(row.get('mensaje', '')).upper()
        
        if "AGUA" in tipo_r or "AGUA" in msj: f_tipo, clase = "AGUA", "falla-agua"
        elif "GAS" in tipo_r or "GAS" in msj: f_tipo, clase = "GAS", "falla-gas"
        else: f_tipo, clase = "LUZ", "falla-luz"

        id_unico = f"{f_tipo}_{row['timestamp'].date()}"
        if id_unico not in ya_mostrados_hoy:
            st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp'].strftime('%H:%M')}</small> - <span class='{clase}'>⚠️ {f_tipo}</span></div>", unsafe_allow_html=True)
            ya_mostrados_hoy.add(id_unico)

# --- CUERPO PRINCIPAL ---
st.title("🏠 Dashboard CODESO Smart Home")
i = st.session_state.indice
actual = df.iloc[i]
anterior = df.iloc[i-1]

# Lógica Gas e Inferencia de Silencio
nivel_real = actual['gas_nivel'] - st.session_state.gas_rellenado
if nivel_real <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0
    nivel_real = 100.0

if st.session_state.vista_actual == "principal":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}")
    
    # ⚡ DETECTOR DE PICOS ELÉCTRICOS (Día 10 y similares)
    consumo_e = actual['consumo_electrico']
    delta_e = consumo_e - anterior['consumo_electrico']
    k2.metric("ENERGÍA (kWh) ⚡", f"{consumo_e:.3f}", f"{delta_e:.3f}")
    
    k3.metric("GAS % 🔥", f"{nivel_real:.1f}%")
    k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # --- MENSAJES DE ESTADO INTELIGENTES ---
    # 1. Alerta de Pico Eléctrico Automática
    if consumo_e > 4.0: # Umbral para detectar el pico del día 10
        st.error(f"🚨 **ALERTA DE PICO ELÉCTRICO:** Consumo crítico detectado ({consumo_e} kWh) a las {actual['timestamp'].strftime('%H:%M')}.")

    # 2. Explicación del Sensor de Gas (Punto 2 de tus errores)
    if actual['gas_en_silencio']:
        st.info("📡 **Estado del Sensor de Gas:** Modo de Ahorro Energético. El sensor permanece en silencio por diseño de bajo consumo o probabilidad de canal (75% silencio esperado). No representa una falla.")
    
    if nivel_real <= 10.0: st.warning(f"⚠️ **BAJO NIVEL DE GAS:** Tanque al {nivel_real:.1f}%.")

    # Gráficas
    st.divider()
    ventana = df.iloc[max(0, i-50):i+1]
    g1, g2 = st.columns(2)
    with g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    with g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

    st.divider()
    b1, b2 = st.columns(2)
    if b1.button("📊 Ver Datos de Consumo Almacenados", use_container_width=True):
        st.session_state.vista_actual = "datos"; st.rerun()
    if b2.button("📜 Ver Historial de Alarmas", use_container_width=True):
        st.session_state.vista_actual = "alarmas"; st.rerun()

# VISTAS DE HISTORIAL (Sincronizadas)
elif st.session_state.vista_actual == "datos":
    st.subheader("🔍 Explorador de Datos Históricos")
    df_v = df[df['timestamp'] <= t_actual]
    c_m, c_d, c_b = st.columns([2, 2, 1])
    mes_sel = c_m.selectbox("Mes", df_v['timestamp'].dt.month_name().unique())
    df_m = df_v[df_v['timestamp'].dt.month_name() == mes_sel]
    dia_sel = c_d.selectbox("Día", sorted(df_m['timestamp'].dt.day.unique()))
    if c_b.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
    st.dataframe(df_m[df_m['timestamp'].dt.day == dia_sel][['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel']])

elif st.session_state.vista_actual == "alarmas":
    st.subheader("📜 Historial de Alarmas del Sistema")
    if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
    st.table(df_alertas[df_alertas['timestamp'] <= t_actual][['timestamp', 'mensaje', 'tipo_anomalia_real']])

# Motor
if st.session_state.corriendo and i < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
