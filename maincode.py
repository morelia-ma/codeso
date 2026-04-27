import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de pantalla
st.set_page_config(page_title="HMI Domótica CODESO", layout="wide")

# 2. Estilos CSS (Sin cambios, para mantener tu estética)
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
    
    # Identificar silencios de gas antes del ffill
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

# --- BITÁCORA LATERAL (Especificidad de Gas y Anti-Repetición) ---
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Activas (24h)")
un_dia_atras = t_actual - timedelta(days=1)
alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)].copy()

if not alertas_24h.empty:
    ya_mostrados_hoy = set()
    for _, row in alertas_24h.iloc[::-1].iterrows():
        tipo_r = str(row.get('tipo_anomalia_real', '')).upper()
        msj = str(row.get('mensaje', '')).upper()
        
        # Lógica de Especificación de Gas
        if "GAS" in tipo_r or "GAS" in msj:
            f_tipo = "FUGA DE GAS" if "FUGA" in msj else "GAS (MODO AHORRO)"
            clase = "falla-gas"
        elif "AGUA" in tipo_r or "AGUA" in msj:
            f_tipo, clase = "AGUA", "falla-agua"
        else:
            f_tipo, clase = "PICO ELÉCTRICO", "falla-luz"

        id_unico = f"{f_tipo}_{row['timestamp'].date()}"
        if id_unico not in ya_mostrados_hoy:
            st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp'].strftime('%H:%M')}</small> - <span class='{clase}'>⚠️ {f_tipo}</span></div>", unsafe_allow_html=True)
            ya_mostrados_hoy.add(id_unico)

# --- CUERPO PRINCIPAL (Control de Vistas para evitar duplicados) ---
st.title("🏠 Dashboard CODESO Smart Home")
i = st.session_state.indice
actual = df.iloc[i]
anterior = df.iloc[i-1]

# Lógica Gas
nivel_real = actual['gas_nivel'] - st.session_state.gas_rellenado
if nivel_real <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0
    nivel_real = 100.0

# --- VISTA: PANEL PRINCIPAL ---
if st.session_state.vista_actual == "principal":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f}")
    
    # Detección de picos para el KPI
    consumo_e = actual['consumo_electrico']
    k2.metric("ENERGÍA (kWh) ⚡", f"{consumo_e:.3f}")
    k3.metric("GAS % 🔥", f"{nivel_real:.1f}%")
    k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Alertas visuales rápidas (solo si son críticas)
    if consumo_e > 4.0:
        st.error(f"🚨 PICO ELÉCTRICO DETECTADO: {consumo_e} kWh")
    if nivel_real <= 10.0:
        st.warning(f"⚠️ NIVEL DE GAS BAJO: {nivel_real:.1f}%")

    st.divider()
    # Gráficas
    ventana = df.iloc[max(0, i-50):i+1]
    g1, g2 = st.columns(2)
    with g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    with g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

    st.divider()
    b1, b2 = st.columns(2)
    if b1.button("📊 Ver Datos de Consumo Almacenados", use_container_width=True):
        st.session_state.vista_actual = "datos"
        st.rerun()
    if b2.button("📜 Ver Historial de Alarmas", use_container_width=True):
        st.session_state.vista_actual = "alarmas"
        st.rerun()

# --- VISTA: DATOS ---
elif st.session_state.vista_actual == "datos":
    st.subheader("🔍 Explorador de Consumo Histórico")
    df_v = df[df['timestamp'] <= t_actual]
    c_m, c_d, c_b = st.columns([2, 2, 1])
    mes_sel = c_m.selectbox("Mes", df_v['timestamp'].dt.month_name().unique())
    df_m = df_v[df_v['timestamp'].dt.month_name() == mes_sel]
    dia_sel = c_d.selectbox("Día", sorted(df_m['timestamp'].dt.day.unique()))
    
    if c_b.button("⬅️ Volver al Panel"):
        st.session_state.vista_actual = "principal"
        st.rerun()
    st.dataframe(df_m[df_m['timestamp'].dt.day == dia_sel][['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel']], use_container_width=True)

# --- VISTA: ALARMAS ---
elif st.session_state.vista_actual == "alarmas":
    st.subheader("📜 Historial de Alarmas")
    if st.button("⬅️ Volver al Panel Principal"):
        st.session_state.vista_actual = "principal"
        st.rerun()
    st.table(df_alertas[df_alertas['timestamp'] <= t_actual][['timestamp', 'mensaje', 'tipo_anomalia_real']])

# Motor de simulación (Solo avanza si estamos en la principal)
if st.session_state.corriendo and i < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
