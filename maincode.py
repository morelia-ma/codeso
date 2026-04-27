import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
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

# 3. Carga de Datos (Sincronizada con tus nuevos archivos)
@st.cache_data
def load_all_data():
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    
    # Identificar silencios de gas (NaN) antes de rellenar para el diagnóstico
    df_gen['gas_en_silencio'] = df_gen['gas_nivel'].isna()
    df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)
    
    try:
        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'])
    except:
        df_al = pd.DataFrame(columns=['timestamp', 'mensaje', 'tipo_anomalia_real'])
    return df_gen, df_al

df, df_alertas = load_all_data()

# 4. Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 1
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'gas_rellenado' not in st.session_state: st.session_state.gas_rellenado = 0
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

t_actual = df.iloc[st.session_state.indice]['timestamp']

# --- SIDEBAR (Panel de Control Unificado) ---
st.sidebar.title("🕹️ Panel de Control")
if st.sidebar.button("▶️ Iniciar / ⏸️ Pausar", key="play_pause"):
    st.session_state.corriendo = not st.session_state.corriendo

if st.sidebar.button("🔄 Reiniciar Simulación", key="reset"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- BITÁCORA LATERAL (Basada en tus nuevos datos limpios) ---
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Recientes (24h)")
un_dia_atras = t_actual - timedelta(days=1)
alertas_24h = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)].copy()

if not alertas_24h.empty:
    for _, row in alertas_24h.iloc[::-1].iterrows():
        tipo = str(row.get('tipo_anomalia_real', '')).lower()
        msj = str(row.get('mensaje', '')).upper()
        
        # Lógica de especificación solicitada
        if "gas" in tipo or "GAS" in msj:
            label = "FUGA DE GAS" if "FUGA" in msj else "GAS (AHORRO ENERGÍA)"
            clase = "falla-gas"
        elif "agua" in tipo or "AGUA" in msj:
            label, clase = "FALLA DE AGUA", "falla-agua"
        else:
            label, clase = "PICO ELÉCTRICO", "falla-luz"
            
        st.sidebar.markdown(f"""
            <div class='bitacora-item'>
                <small>{row['timestamp'].strftime('%H:%M')}</small> - <span class='{clase}'>⚠️ {label}</span>
            </div>
        """, unsafe_allow_html=True)

# --- CONTENEDOR DE VISTAS (Evita duplicidad de elementos) ---
view_space = st.empty()

with view_space.container():
    idx = st.session_state.indice
    actual = df.iloc[idx]
    
    if st.session_state.vista_actual == "principal":
        st.title("🏠 Dashboard CODESO Smart Home")
        
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}")
        k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
        k3.metric("GAS % 🔥", f"{actual['gas_nivel']:.1f}%")
        k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

        # Alertas de tiempo real
        if actual['consumo_electrico'] > 4.0:
            st.error(f"🚨 PICO ELÉCTRICO DETECTADO: {actual['consumo_electrico']} kWh")
        
        st.divider()
        # Gráficas
        ventana = df.iloc[max(0, idx-50):idx+1]
        g1, g2 = st.columns(2)
        with g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
        with g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

        st.divider()
        # Navegación con Keys Únicas
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("📊 Ver Datos de Consumo Almacenados", key="nav_datos", use_container_width=True):
            st.session_state.vista_actual = "datos"
            st.rerun()
        if col_b2.button("📜 Ver Historial de Alarmas", key="nav_alarmas", use_container_width=True):
            st.session_state.vista_actual = "alarmas"
            st.rerun()

    elif st.session_state.vista_actual == "datos":
        st.subheader("🔍 Explorador de Datos (Fallas en Rojo)")
        if st.button("⬅️ Volver al Panel", key="back_to_main"):
            st.session_state.vista_actual = "principal"
            st.rerun()
        
        # Filtro de tiempo real
        df_visto = df[df['timestamp'] <= t_actual].copy()
        meses = df_visto['timestamp'].dt.month_name().unique()
        sel_mes = st.selectbox("Mes", meses)
        
        df_mes = df_visto[df_visto['timestamp'].dt.month_name() == sel_mes]
        sel_dia = st.selectbox("Día", sorted(df_mes['timestamp'].dt.day.unique()))
        
        df_final = df_mes[df_mes['timestamp'].dt.day == sel_dia].copy()

        # Estilo para pintar de rojo si anomalia == True
        def style_anomalia(row):
            return ['background-color: #ffcccc' if row.anomalia == True else '' for _ in row]

        st.dataframe(df_final.style.apply(style_anomalia, axis=1), use_container_width=True)

    elif st.session_state.vista_actual == "alarmas":
        st.subheader("📜 Historial de Alarmas Registradas")
        if st.button("⬅️ Volver al Panel", key="back_from_alarmas"):
            st.session_state.vista_actual = "principal"
            st.rerun()
        st.table(df_alertas[df_alertas['timestamp'] <= t_actual])

# Motor de simulación
if st.session_state.corriendo and idx < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
