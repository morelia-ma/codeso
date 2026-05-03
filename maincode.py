import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="Smart Home HMI - CODESO", layout="wide")

# 2. Estilos CSS mejorados
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #f8f9fa; padding: 20px; border-left: 5px solid #0077B6; }
    .bitacora-item { padding: 10px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    .prediction-box { background-color: #fff3cd; padding: 10px; border-radius: 10px; border: 1px solid #ffeeba; margin-bottom: 10px; }
    .emergency-card { background-color: #fdf2f2; border: 1px solid #f8d7da; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    try:
        df_gen = pd.read_csv('datos_domotia_final.csv')
        df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'], errors='coerce').dt.tz_localize(None)
        df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)
        
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'], errors='coerce').dt.tz_localize(None)
        return df_gen.dropna(subset=['timestamp']), df_al.dropna(subset=['timestamp'])
    except:
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_all_data()

# 4. Estado de la Sesión para Directorio y Navegación
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"
if 'directorio' not in st.session_state:
    st.session_state.directorio = {"Bomberos": "911", "Ambulancia": "911", "Técnico": "", "Gas": ""}

# --- SIDEBAR ---
with st.sidebar:
    st.title("🕹️ Panel de Control")
    if st.button("▶️ Iniciar / ⏸️ Pausar", use_container_width=True):
        st.session_state.corriendo = not st.session_state.corriendo
    
    # Botón Directorio
    if st.button("📞 Directorio de Emergencia", use_container_width=True):
        st.session_state.vista_actual = "directorio"

    st.divider()
    st.subheader("🔔 Alertas Recientes")
    
    t_actual = df.iloc[st.session_state.indice]['timestamp']
    
    # Lógica de Predicción de Gas
    # Calculamos consumo promedio simple (ejemplo: 0.5% por día de simulación)
    gas_actual = df.iloc[st.session_state.indice]['gas_nivel']
    dias_restantes = int(gas_actual / 2) # Simulación: gasta 2% diario
    
    if dias_restantes in [15, 10, 5]:
        st.markdown(f"""<div class='prediction-box'>📅 <b>Predicción:</b> Quedan aprox. {dias_restantes} días de gas.</div>""", unsafe_allow_html=True)

    # Mostrar alertas de las últimas 24h
    limite_24h = t_actual - timedelta(hours=24)
    alertas_recientes = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= limite_24h)]
    if not alertas_recientes.empty:
        for _, row in alertas_recientes.tail(3).iterrows():
            st.markdown(f"<div class='bitacora-item'>⚠️ {row['mensaje']}</div>", unsafe_allow_html=True)
    else:
        st.success("Sin anomalías en las últimas 24h")

# --- CONTENIDO PRINCIPAL ---
main_area = st.empty()

with main_area.container():
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista_actual == "principal":
        st.title("🏠 Monitor Inteligente CODESO")
        
        # Métricas principales
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AGUA (L)", f"{actual['consumo_agua']:.1f} 💧")
        m2.metric("ENERGÍA (kWh)", f"{actual['consumo_electrico']:.3f} ⚡")
        m3.metric("GAS", f"{actual['gas_nivel']:.1f}% 🔥")
        m4.metric("TEMP. INT", f"{actual['temperatura_int']:.1f} °C 🌡️")

        st.divider()

        # Layout de gráficas reorganizado
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📈 Consumo de Recursos")
            ventana = df.iloc[max(0, st.session_state.indice-40):st.session_state.indice+1]
            tab1, tab2 = st.tabs(["Agua", "Energía"])
            with tab1: st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
            with tab2: st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")

        with col_right:
            st.subheader("⛽ Estado del Tanque")
            st.write(f"Capacidad actual: {actual['gas_nivel']:.2f}%")
            st.progress(actual['gas_nivel']/100)
            # Gráfica pequeña circular o de área para el gas
            st.area_chart(ventana.set_index('timestamp')['gas_nivel'], color="#E74C3C", height=200)

        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("📊 Historial de Datos", use_container_width=True): st.session_state.vista_actual = "datos"
        if c2.button("📜 Historial de Alarmas", use_container_width=True): st.session_state.vista_actual = "alarmas"

    elif st.session_state.vista_actual == "directorio":
        st.subheader("📞 Directorio de Contactos de Emergencia")
        if st.button("⬅️ Volver al Panel"): st.session_state.vista_actual = "principal"; st.rerun()
        
        with st.form("emergency_form"):
            col_e1, col_e2 = st.columns(2)
            st.session_state.directorio["Bomberos"] = col_e1.text_input("🚒 Bomberos", st.session_state.directorio["Bomberos"])
            st.session_state.directorio["Ambulancia"] = col_e2.text_input("🚑 Ambulancia", st.session_state.directorio["Ambulancia"])
            st.session_state.directorio["Técnico"] = col_e1.text_input("🛠️ Técnico (Luz/Agua)", st.session_state.directorio["Técnico"])
            st.session_state.directorio["Gas"] = col_e2.text_input("🔥 Proveedor de Gas", st.session_state.directorio["Gas"])
            if st.form_submit_button("Guardar Contactos"):
                st.success("Directorio actualizado correctamente")

    elif st.session_state.vista_actual == "alarmas":
        st.subheader("📜 Historial de Alarmas Filtrado")
        if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
        
        df_al_disp = df_alertas[df_alertas['timestamp'] <= t_actual].copy()
        df_al_disp['Mes'] = df_al_disp['timestamp'].dt.month_name()
        df_al_disp['Día'] = df_al_disp['timestamp'].dt.day
        
        f1, f2 = st.columns(2)
        m_sel = f1.selectbox("Filtrar Mes", df_al_disp['Mes'].unique())
        d_sel = f2.selectbox("Filtrar Día", sorted(df_al_disp[df_al_disp['Mes'] == m_sel]['Día'].unique()))
        
        res = df_al_disp[(df_al_disp['Mes'] == m_sel) & (df_al_disp['Día'] == d_sel)]
        st.table(res[['timestamp', 'mensaje', 'tipo']].sort_values('timestamp', ascending=False))

    elif st.session_state.vista_actual == "datos":
        if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
        # Filtro de datos (como ya lo tenías)
        df_disp = df[df['timestamp'] <= t_actual].copy()
        df_disp['Mes'] = df_disp['timestamp'].dt.month_name()
        df_disp['Día'] = df_disp['timestamp'].dt.day
        f1, f2 = st.columns(2)
        ms = f1.selectbox("Mes", df_disp['Mes'].unique())
        ds = f2.selectbox("Día", sorted(df_disp[df_disp['Mes'] == ms]['Día'].unique()))
        st.dataframe(df_disp[(df_disp['Mes'] == ms) & (df_disp['Día'] == ds)], use_container_width=True)

# Motor de simulación
if st.session_state.corriendo and st.session_state.indice < len(df) - 1 and st.session_state.vista_actual == "principal":
    st.session_state.indice += 1
    time.sleep(0.05)
    st.rerun()
