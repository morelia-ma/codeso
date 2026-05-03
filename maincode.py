import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# 2. ESTILOS CSS PERSONALIZADOS
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .spacer { margin-top: 30px; }
    
    /* Tarjetas de indicadores superiores */
    .metric-card {
        background-color: white; border-radius: 10px; padding: 12px 18px;
        border-left: 5px solid #0077B6; box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        height: 100px;
    }
    .metric-title { font-size: 0.75rem; font-weight: bold; color: #666; text-transform: uppercase; }
    .metric-value { font-size: 1.9rem; font-weight: 500; color: #1f2d3d; }
    
    /* Contenedor del Tanque de Gas */
    .gas-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .gas-container {
        height: 200px; width: 60px; background-color: #f0f2f6;
        border-radius: 30px; position: relative; border: 2px solid #ddd;
        overflow: hidden;
    }
    .gas-fill { 
        background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; 
        transition: height 0.5s ease-in-out; 
    }
    .gas-percentage { font-weight: bold; font-size: 1.1rem; color: #1f2d3d; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE CARGA DE DATOS
@st.cache_data
def load_data():
    try:
        # Carga de telemetría
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df['gas_nivel'] = df['gas_nivel'].ffill().fillna(0)
        
        # Carga de alertas
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except Exception as e:
        st.error(f"Error al cargar archivos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_raw, df_alertas_raw = load_data()

# 4. MANEJO DE ESTADO DE SESIÓN
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# 5. LÓGICA DE TIEMPO "REAL" (SIMULADO)
if not df_raw.empty:
    # Punto actual en el tiempo según la simulación
    t_presente = df_raw.iloc[st.session_state.indice]['timestamp']
    
    # Dataframes filtrados hasta el momento actual
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]
    df_alertas_presente = df_alertas_raw[df_alertas_raw['timestamp'] <= t_presente]

# 6. BARRA LATERAL (CONTROL)
with st.sidebar:
    st.header("🎮 Control de Simulación")
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("▶️ Iniciar", use_container_width=True): st.session_state.corriendo = True
    if col_btn2.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()
    
    st.markdown("---")
    st.subheader("🔔 Últimas Alertas")
    if not df_alertas_presente.empty:
        # Mostrar alertas de las últimas 24 horas simuladas
        ultimas_24h = df_alertas_presente[df_alertas_presente['timestamp'] >= t_presente - timedelta(hours=24)]
        if not ultimas_24h.empty:
            for _, fila in ultimas_24h.tail(3).iterrows():
                st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")
        else:
            st.write("Sin alertas recientes.")

# 7. NAVEGACIÓN Y VISTAS
if not df_raw.empty:

    # --- VISTA: HISTORIAL DE DATOS ---
    if st.session_state.vista == "datos":
        st.header("📊 Historial de Telemetría")
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
        
        st.info(f"Visualizando datos hasta: **{t_presente.strftime('%d %B, %Y - %H:%M')}**")
        
        col_m, col_d = st.columns(2)
        with col_m:
            meses = df_presente['timestamp'].dt.month_name().unique()
            mes_sel = st.selectbox("Filtrar por Mes", options=meses)
        with col_d:
            dias = df_presente[df_presente['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique()
            dia_sel = st.selectbox("Filtrar por Día", options=dias)
            
        data_final = df_presente[(df_presente['timestamp'].dt.month_name() == mes_sel) & 
                                (df_presente['timestamp'].dt.day == dia_sel)]
        
        st.dataframe(data_final.sort_values(by='timestamp', ascending=False), use_container_width=True)

    # --- VISTA: HISTORIAL DE ALARMAS (CON FILTROS) ---
    elif st.session_state.vista == "alarmas":
        st.header("🚨 Histórico de Alarmas del Sistema")
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
            
        st.info(f"Alarmas registradas hasta: **{t_presente.strftime('%d %B, %Y')}**")
        
        if not df_alertas_presente.empty:
            col_am, col_ad = st.columns(2)
            with col_am:
                meses_al = df_alertas_presente['timestamp'].dt.month_name().unique()
                mes_al_sel = st.selectbox("Mes de la Alerta", options=meses_al)
            with col_ad:
                dias_al = df_alertas_presente[df_alertas_presente['timestamp'].dt.month_name() == mes_al_sel]['timestamp'].dt.day.unique()
                dia_al_sel = st.selectbox("Día de la Alerta", options=dias_al)
            
            alertas_filtradas = df_alertas_presente[(df_alertas_presente['timestamp'].dt.month_name() == mes_al_sel) & 
                                                   (df_alertas_presente['timestamp'].dt.day == dia_al_sel)]
            
            if not alertas_filtradas.empty:
                st.table(alertas_filtradas.sort_values(by='timestamp', ascending=False))
            else:
                st.warning("No se encontraron alertas para la fecha seleccionada.")
        else:
            st.success("No se han generado alertas en lo que va de la simulación.")

    # --- VISTA: DIRECTORIO ---
    elif st.session_state.vista == "directorio":
        st.header("📞 Directorio de Contactos de Emergencia")
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
            
        st.table(pd.DataFrame({
            "Servicio": ["Soporte Domótico", "Emergencias", "Seguridad Privada", "Mantenimiento Gas"],
            "Contacto": ["Ing. Montoya", "911", "Central Vigilancia", "Técnico Especialista"],
            "Teléfono": ["555-0102", "911", "555-9000", "555-4433"]
        }))

    # --- VISTA: PANEL PRINCIPAL ---
    elif st.session_state.vista == "principal":
        actual = df_raw.iloc[st.session_state.indice]
        st.title(f"🏠 Monitoreo Familia Montoya")
        st.caption(f"Fecha de simulación: {t_presente.strftime('%d/%m/%Y %H:%M:%S')}")

        # Indicadores en la parte superior
        cols_ind = st.columns(4)
        metricas = [
            ("Consumo Agua (L) 💧", actual["consumo_agua"], "{:.1f}"),
            ("Energía (kWh) ⚡", actual["consumo_electrico"], "{:.3f}"),
            ("Humedad Int (%) ☁️", actual["humedad_interior"], "{:.1f}"),
            ("Temperatura Int (°C) 🌡️", actual["temperatura_int"], "{:.1f}")
        ]
        for i, (label, val, fmt) in enumerate(metricas):
            with cols_ind[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">{label}</div>
                    <div class="metric-value">{fmt.format(val)}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

        # Gráficas y Tanque de Gas (ALTURAS IGUALADAS)
        col_graf, col_gas = st.columns([4, 0.8])
        
        # Ventana de los últimos 30 registros para las gráficas
        ventana_grafica = df_presente.tail(30).set_index('timestamp')

        with col_graf:
            g1, g2 = st.columns(2)
            with g1:
                st.caption("📈 Histórico Reciente: Agua")
                st.area_chart(ventana_grafica['consumo_agua'], height=250)
            with g2:
                st.caption("📈 Histórico Reciente: Energía")
                st.line_chart(ventana_grafica['consumo_electrico'], height=250, color="#FFB703")

        with col_gas:
            st.caption("⛽ Nivel de Gas")
            v_gas = actual['gas_nivel']
            st.markdown(f"""
                <div class="gas-wrapper">
                    <div class="gas-container">
                        <div class="gas-fill" style="height: {v_gas}%;"></div>
                    </div>
                    <div class="gas-percentage">{v_gas:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        # Botones de navegación inferiores
        st.markdown("---")
        nav1, nav2, nav3, nav4 = st.columns(4)
        if nav1.button("📊 Ver Historial Datos", use_container_width=True):
            st.session_state.vista = "datos"; st.rerun()
        if nav2.button("🚨 Ver Historial Alarmas", use_container_width=True):
            st.session_state.vista = "alarmas"; st.rerun()
        if nav3.button("📞 Directorio Emergencia", use_container_width=True):
            st.session_state.vista = "directorio"; st.rerun()
        nav4.button("⚙️ Configuración", use_container_width=True, disabled=True)

# 8. BUCLE DE ACTUALIZACIÓN
if st.session_state.corriendo and st.session_state.vista == "principal":
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.1) # Velocidad de la simulación
        st.rerun()
    else:
        st.session_state.corriendo = False
        st.success("Simulación completada.")
