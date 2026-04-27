import streamlit as st
import pandas as pd
import time
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

# 3. Carga y Limpieza
@st.cache_data
def load_all_data():
    df_gen = pd.read_csv('datos_domotia_final.csv')
    df_gen.columns = df_gen.columns.str.strip()
    df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'])
    # Detectar silencios de gas (NaNs originales)
    df_gen['gas_es_silencio'] = df_gen['gas_nivel'].isna()
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

# --- SIDEBAR ---
st.sidebar.title("🕹️ Panel de Control")
c1, c2 = st.sidebar.columns(2)
if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
if c2.button("⏸️ Pausar"): st.session_state.corriendo = False
if st.sidebar.button("🔄 Reiniciar"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- BITÁCORA IZQUIERDA (Anti-repetición Estricta) ---
st.sidebar.divider()
st.sidebar.subheader("🔔 Alertas Activas (24h)")
un_dia_atras = t_actual - timedelta(days=1)

# Filtramos alertas del pasado cercano
alertas_recientes = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= un_dia_atras)].copy()

if not alertas_recientes.empty:
    # Agregamos fecha para agrupar
    alertas_recientes['fecha_dia'] = alertas_recientes['timestamp'].dt.date
    
    # Clasificación y limpieza
    items_a_mostrar = []
    vistos = set() # Para evitar duplicados de (Tipo + Día)

    for _, row in alertas_recientes.iloc[::-1].iterrows():
        tipo_r = str(row.get('tipo_anomalia_real', '')).upper()
        msj = str(row.get('mensaje', '')).upper()
        
        # Determinar Categoría Real
        if "GAS" in tipo_r or "GAS" in msj:
            # Si el mensaje dice fuga es fuga, si no, es el comportamiento esperado del sensor
            f_label = "FUGA DE GAS" if "FUGA" in msj else "GAS (AHORRO ENERGÍA/PROB.)"
            clase = "falla-gas"
        elif "AGUA" in tipo_r or "AGUA" in msj:
            f_label, clase = "FUGA DE AGUA", "falla-agua"
        else:
            f_label, clase = "PICO ELÉCTRICO", "falla-luz"

        # Solo guardamos si no hemos visto este tipo HOY
        key = f"{f_label}_{row['fecha_dia']}"
        if key not in vistos:
            items_a_mostrar.append({'ts': row['timestamp'], 'label': f_label, 'clase': clase})
            vistos.add(key)

    for item in items_a_mostrar:
        st.sidebar.markdown(f"""
            <div class='bitacora-item'>
                <small>{item['ts'].strftime('%H:%M')}</small> - <span class='{item['clase']}'>⚠️ {item['label']}</span>
            </div>
        """, unsafe_allow_html=True)

# --- CUERPO PRINCIPAL ---
st.title("🏠 Dashboard CODESO Smart Home")
idx = st.session_state.indice
actual = df.iloc[idx]
anterior = df.iloc[idx-1]

# Lógica Gas
nivel_gas_vis = actual['gas_nivel'] - st.session_state.gas_rellenado
if nivel_gas_vis <= 8.0:
    st.session_state.gas_rellenado = actual['gas_nivel'] - 100.0
    nivel_gas_vis = 100.0

if st.session_state.vista_actual == "principal":
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}")
    
    # Detector de Pico Eléctrico para el KPI
    val_e = actual['consumo_electrico']
    k2.metric("ENERGÍA (kWh) ⚡", f"{val_e:.3f}")
    if val_e > 4.0: st.error(f"🚨 PICO ELÉCTRICO DETECTADO: {val_e} kWh")
    
    k3.metric("GAS % 🔥", f"{nivel_gas_vis:.1f}%")
    k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

    st.divider()
    
    # Gráficas (Protegidas en columnas)
    ventana = df.iloc[max(0, idx-50):idx+1]
    col_g1, col_g2 = st.columns(2)
    with col_g1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
    with col_g2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

    st.divider()
    
    # Botones de Navegación
    bn1, bn2 = st.columns(2)
    if bn1.button("📊 Ver Datos de Consumo Almacenados", use_container_width=True):
        st.session_state.vista_actual = "datos"
        st.rerun()
    if bn2.button("📜 Ver Historial de Alarmas", use_container_width=True):
        st.session_state.vista_actual = "alarmas"
        st.rerun()

elif st.session_state.vista_actual == "datos":
    st.subheader("🔍 Explorador de Consumo")
    if st.button("⬅️ Volver"):
        st.session_state.vista_actual = "principal"
        st.rerun()
    
    df_v = df[df['timestamp'] <= t_actual]
    mes_sel = st.selectbox("Seleccionar Mes", df_v['timestamp'].dt.month_name().unique())
    df_m = df_v[df_v['timestamp'].dt.month_name() == mes_sel]
    dia_sel = st.selectbox("Seleccionar Día", sorted(df_m['timestamp'].dt.day.unique()))
    st.dataframe(df_m[df_m['timestamp'].dt.day == dia_sel][['timestamp', 'consumo_agua', 'consumo_electrico', 'gas_nivel']], use_container_width=True)

elif st.session_state.vista_actual == "alarmas":
    st.subheader("📜 Historial Completo")
    if st.button("⬅️ Volver"):
        st.session_state.vista_actual = "principal"
        st.rerun()
    st.table(df_alertas[df_alertas['timestamp'] <= t_actual][['timestamp', 'mensaje', 'tipo_anomalia_real']])

# Motor
if st.session_state.corriendo and idx < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.3)
    st.rerun()
