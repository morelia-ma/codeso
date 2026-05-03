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
    /* Estilo para la barra de gas tipo batería */
    .stProgress > div > div > div > div { background-color: #E74C3C; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    try:
        df_gen = pd.read_csv('datos_domotia_final.csv')
        df_gen.columns = df_gen.columns.str.strip()
        df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'], errors='coerce')
        df_gen = df_gen.dropna(subset=['timestamp'])
        df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)

        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'], errors='coerce')
        df_al = df_al.dropna(subset=['timestamp'])
        return df_gen, df_al
    except Exception as e:
        st.error(f"Error al cargar archivos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_all_data()

# 4. Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"

if not df.empty:
    t_actual = df.iloc[st.session_state.indice]['timestamp']

    # --- SIDEBAR ---
    st.sidebar.title("🕹️ Panel de Control")
    if st.sidebar.button("▶️ Iniciar / ⏸️ Pausar", key="play_btn"):
        st.session_state.corriendo = not st.session_state.corriendo
    if st.sidebar.button("🔄 Reiniciar", key="reset_btn"):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    # --- SIDEBAR: ALERTAS (MÁXIMO 24H ATRÁS) ---
    st.sidebar.divider()
    st.sidebar.subheader("🔔 Alertas (Últimas 24h)")
    
    # Lógica de 24 horas: alertas entre (t_actual - 24h) y (t_actual)
    limite_24h = t_actual - timedelta(hours=24)
    alertas_recientes = df_alertas[
        (df_alertas['timestamp'] <= t_actual) & 
        (df_alertas['timestamp'] >= limite_24h)
    ].copy()

    if not alertas_recientes.empty:
        # Mantener solo una alerta por tipo en este rango para no saturar
        alertas_recientes['fecha_dia'] = alertas_recientes['timestamp'].dt.date
        alertas_unicas = alertas_recientes.drop_duplicates(subset=['fecha_dia', 'tipo_anomalia_real'])
        
        for _, row in alertas_unicas.sort_values('timestamp', ascending=False).iterrows():
            tipo = str(row.get('tipo_anomalia_real', '')).lower()
            clase = "falla-gas" if "gas" in tipo else "falla-agua" if "agua" in tipo else "falla-luz"
            st.sidebar.markdown(f"<div class='bitacora-item'><small>{row['timestamp'].strftime('%H:%M')}</small><br><span class='{clase}'>⚠️ {row['mensaje'].upper()}</span></div>", unsafe_allow_html=True)
    else:
        st.sidebar.write("✅ Sin alertas en las últimas 24h")

    # --- CUERPO PRINCIPAL ---
    main_placeholder = st.empty()

    with main_placeholder.container():
        idx = st.session_state.indice
        actual = df.iloc[idx]

        if st.session_state.vista_actual == "principal":
            st.title("🏠 Dashboard CODESO Smart Home")
            
            # Indicadores
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("AGUA (L) 💧", f"{actual['consumo_agua']:.1f}")
            k2.metric("ENERGÍA (kWh) ⚡", f"{actual['consumo_electrico']:.3f}")
            k3.metric("GAS 🔥", f"{actual['gas_nivel']:.1f}%")
            k4.metric("TEMP. INT 🌡️", f"{actual['temperatura_int']:.1f} °C")

            st.divider()
            
            # FILA DE GRÁFICAS Y "BATERÍA" DE GAS
            ventana = df.iloc[max(0, idx-50):idx+1]
            g1, g2, g3 = st.columns([2, 2, 1]) # La tercera columna es más estrecha para la "batería"
            
            with g1:
                st.subheader("Consumo Agua")
                st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
            
            with g2:
                st.subheader("Consumo Energía")
                st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")
                
            with g3:
                st.subheader("Nivel de Gas")
                # Lógica visual de batería
                nivel_gas = float(actual['gas_nivel'])
                st.write(f"Capacidad: {nivel_gas}%")
                st.progress(nivel_gas / 100)
                if nivel_gas < 20:
                    st.warning("Nivel de gas bajo")

            st.divider()
            
            # Botones de navegación (ÚNICOS)
            c1, c2 = st.columns(2)
            if c1.button("📊 Ver Datos Almacenados", use_container_width=True, key="btn_view_data"):
                st.session_state.vista_actual = "datos"
                st.rerun()
            if c2.button("📜 Ver Historial de Alarmas", use_container_width=True, key="btn_view_hist"):
                st.session_state.vista_actual = "alarmas"
                st.rerun()

        elif st.session_state.vista_actual == "datos":
            if st.button("⬅️ Volver", key="back_to_main_1"): 
                st.session_state.vista_actual = "principal"; st.rerun()
            df_v = df[df['timestamp'] <= t_actual].copy()
            st.dataframe(df_v.tail(100), use_container_width=True)

        elif st.session_state.vista_actual == "alarmas":
            if st.button("⬅️ Volver", key="back_to_main_2"): 
                st.session_state.vista_actual = "principal"; st.rerun()
            st.table(df_alertas[df_alertas['timestamp'] <= t_actual].tail(30))

    # Motor de Simulación
    if st.session_state.corriendo and idx < len(df) - 1 and st.session_state.vista_actual == "principal":
        st.session_state.indice += 1
        time.sleep(0.05)
        st.rerun()
