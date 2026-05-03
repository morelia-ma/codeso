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
    .stProgress > div > div > div > div { background-color: #E74C3C; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    try:
        df_gen = pd.read_csv('datos_domotia_final.csv')
        df_gen.columns = df_gen.columns.str.strip()
        # Forzamos que no tengan zona horaria para evitar conflictos en la comparación
        df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp'], errors='coerce').dt.tz_localize(None)
        df_gen = df_gen.dropna(subset=['timestamp'])
        df_gen['gas_nivel'] = df_gen['gas_nivel'].ffill().fillna(99.9)

        df_al = pd.read_csv('alertas_historico.csv')
        df_al.columns = df_al.columns.str.strip()
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp'], errors='coerce').dt.tz_localize(None)
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
    # Tiempo actual relativo a la simulación
    t_actual = df.iloc[st.session_state.indice]['timestamp']

    # --- SIDEBAR ---
    st.sidebar.title("🕹️ Panel de Control")
    if st.sidebar.button("▶️ Iniciar / ⏸️ Pausar", key="play_btn"):
        st.session_state.corriendo = not st.session_state.corriendo
    if st.sidebar.button("🔄 Reiniciar", key="reset_btn"):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    # --- SIDEBAR: ALERTAS (Lógica de 24h relativa a la simulación) ---
    st.sidebar.divider()
    st.sidebar.subheader("🔔 Alertas (Últimas 24h)")
    
    # Filtramos alertas que ocurrieron ANTES del tiempo actual, pero no hace más de 24h
    limite_24h_atras = t_actual - timedelta(hours=24)
    
    alertas_ventana = df_alertas[
        (df_alertas['timestamp'] <= t_actual) & 
        (df_alertas['timestamp'] >= limite_24h_atras)
    ].copy()

    if not alertas_ventana.empty:
        # Agrupamos para mostrar solo la más reciente de cada tipo en esas 24h
        alertas_ventana['solo_fecha'] = alertas_ventana['timestamp'].dt.date
        alertas_display = alertas_ventana.sort_values('timestamp', ascending=False).drop_duplicates(subset=['solo_fecha', 'tipo_anomalia_real'])
        
        for _, row in alertas_display.iterrows():
            tipo = str(row.get('tipo_anomalia_real', '')).lower()
            clase = "falla-gas" if "gas" in tipo else "falla-agua" if "agua" in tipo else "falla-luz"
            st.sidebar.markdown(f"""
                <div class='bitacora-item'>
                    <small>{row['timestamp'].strftime('%d/%m %H:%M')}</small><br>
                    <span class='{clase}'>⚠️ {row['mensaje'].upper()}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.success("✅ Sin alertas recientes")

    # --- CUERPO PRINCIPAL ---
    container = st.empty()

    with container.container():
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
            
            # Gráficas y Batería
            ventana = df.iloc[max(0, idx-50):idx+1]
            g1, g2, g3 = st.columns([2, 2, 1])
            
            with g1:
                st.subheader("Consumo Agua")
                st.area_chart(ventana.set_index('timestamp')['consumo_agua'], color="#0077B6")
            
            with g2:
                st.subheader("Consumo Energía")
                st.line_chart(ventana.set_index('timestamp')['consumo_electrico'], color="#FFB703")
                
            with g3:
                st.subheader("Nivel de Gas")
                nivel_gas = float(actual['gas_nivel'])
                st.write(f"Capacidad: {nivel_gas}%")
                st.progress(nivel_gas / 100)
                if nivel_gas < 20:
                    st.warning("Nivel Crítico")

            st.divider()
            
            # Botones de navegación
            c1, c2 = st.columns(2)
            if c1.button("📊 Ver Datos Almacenados", use_container_width=True):
                st.session_state.vista_actual = "datos"; st.rerun()
            if c2.button("📜 Ver Historial de Alarmas", use_container_width=True):
                st.session_state.vista_actual = "alarmas"; st.rerun()

        elif st.session_state.vista_actual == "datos":
            if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
            st.dataframe(df[df['timestamp'] <= t_actual].tail(100), use_container_width=True)

        elif st.session_state.vista_actual == "alarmas":
            if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
            st.table(df_alertas[df_alertas['timestamp'] <= t_actual].tail(30))

    # Motor de Simulación
    if st.session_state.corriendo and idx < len(df) - 1 and st.session_state.vista_actual == "principal":
        st.session_state.indice += 1
        time.sleep(0.05)
        st.rerun()
