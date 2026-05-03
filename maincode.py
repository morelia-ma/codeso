import streamlit as st
import pandas as pd
import time
import os

# 1. CONFIGURACIÓN Y ESTILOS (Restaurados y Completos)
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    .spacer { margin-top: 30px; }
    .metric-card {
        background-color: white; border-radius: 10px; padding: 12px 18px;
        border-left: 5px solid #0077B6; box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        height: 100px;
    }
    .metric-title { font-size: 0.75rem; font-weight: bold; color: #666; text-transform: uppercase; }
    .metric-value { font-size: 1.9rem; font-weight: 500; color: #1f2d3d; }
    .gas-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .gas-container {
        height: 200px; width: 60px; background-color: #f0f2f6;
        border-radius: 30px; position: relative; border: 2px solid #ddd;
        overflow: hidden;
    }
    .gas-fill { background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; }
    .gas-percentage { font-weight: bold; font-size: 1.1rem; color: #1f2d3d; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIONES DE DATOS Y PERSISTENCIA
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        # Aseguramos que el gas nunca sea NaN para evitar errores visuales
        df['gas_nivel'] = df['gas_nivel'].ffill().bfill().fillna(0)
        
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except Exception as e:
        st.error(f"Error al cargar archivos: {e}")
        return pd.DataFrame(), pd.DataFrame()

def cargar_directorio():
    if os.path.exists('directorio.csv'):
        return pd.read_csv('directorio.csv')
    # Valores por defecto si no existe el archivo
    return pd.DataFrame({"Servicio": ["Emergencias", "Fugas Gas", "Agua"], "Número": ["911", "800-GAS-LINE", "555-0102"]})

# 3. INICIALIZACIÓN DE ESTADO
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

df_raw, df_alertas_raw = load_data()

# 4. SIDEBAR (Control y Alertas Recientes)
with st.sidebar:
    st.header("🎮 Control")
    col_bt1, col_bt2 = st.columns(2)
    if col_bt1.button("▶️ Iniciar"): st.session_state.corriendo = True
    if col_bt2.button("🔄 Reiniciar"):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()
    
    st.markdown("---")
    st.subheader("🔔 Últimas Alertas")
    if not df_raw.empty:
        t_actual = df_raw.iloc[st.session_state.indice]['timestamp']
        recientes = df_alertas_raw[df_alertas_raw['timestamp'] <= t_actual].tail(3)
        if recientes.empty:
            st.write("Sin alertas registradas.")
        for _, fila in recientes.iterrows():
            st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")

# 5. NAVEGACIÓN Y VISTAS
if not df_raw.empty:
    actual_row = df_raw.iloc[st.session_state.indice]
    t_presente = actual_row['timestamp']
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]

    # --- VISTA: HISTORIAL DE DATOS ---
    if st.session_state.vista == "datos":
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"; st.rerun()
        st.header("📊 Historial Completo de Telemetría")
        
        meses = df_presente['timestamp'].dt.month_name().unique()
        sel_mes = st.selectbox("Filtrar por Mes", meses)
        dias = df_presente[df_presente['timestamp'].dt.month_name() == sel_mes]['timestamp'].dt.day.unique()
        sel_dia = st.selectbox("Filtrar por Día", dias)
        
        df_filtrado = df_presente[(df_presente['timestamp'].dt.month_name() == sel_mes) & 
                                  (df_presente['timestamp'].dt.day == sel_dia)]
        st.dataframe(df_filtrado.sort_values('timestamp', ascending=False), use_container_width=True)

    # --- VISTA: HISTORIAL DE ALARMAS ---
    elif st.session_state.vista == "alarmas":
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"; st.rerun()
        st.header("🚨 Registro Histórico de Alarmas")
        
        df_al_pres = df_alertas_raw[df_alertas_raw['timestamp'] <= t_presente]
        if not df_al_pres.empty:
            m_al = st.selectbox("Mes de Alerta", df_al_pres['timestamp'].dt.month_name().unique())
            d_al = st.selectbox("Día de Alerta", df_al_pres[df_al_pres['timestamp'].dt.month_name() == m_al]['timestamp'].dt.day.unique())
            st.table(df_al_pres[(df_al_pres['timestamp'].dt.month_name() == m_al) & 
                                (df_al_pres['timestamp'].dt.day == d_al)].sort_values('timestamp', ascending=False))
        else:
            st.info("No hay alarmas en el historial hasta este momento.")

    # --- VISTA: DIRECTORIO (Arreglada) ---
    elif st.session_state.vista == "directorio":
        if st.button("⬅ Volver al Panel"):
            st.session_state.vista = "principal"; st.rerun()
        st.header("📞 Directorio de Contactos de Emergencia")
        
        col_form, col_list = st.columns([1, 2])
        with col_form:
            st.subheader("Añadir Contacto")
            with st.form("form_contacto", clear_on_submit=True):
                nuevo_ser = st.text_input("Nombre del Servicio (ej. Gas)")
                nuevo_num = st.text_input("Número de Teléfono")
                if st.form_submit_button("Guardar Contacto"):
                    if nuevo_ser and nuevo_num:
                        df_d = cargar_directorio()
                        nuevo_df = pd.DataFrame({"Servicio": [nuevo_ser], "Número": [nuevo_num]})
                        pd.concat([df_d, nuevo_df], ignore_index=True).to_csv('directorio.csv', index=False)
                        st.success("Guardado")
                        st.rerun()
        
        with col_list:
            st.subheader("Lista de Contactos")
            df_d = cargar_directorio()
            for idx, row in df_d.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.info(f"**{row['Servicio']}**: {row['Número']}")
                if c2.button("Eliminar", key=f"btn_del_{idx}"):
                    df_d.drop(idx).to_csv('directorio.csv', index=False)
                    st.rerun()

    # --- VISTA: DASHBOARD PRINCIPAL ---
    else:
        st.title("🏠 Monitoreo Familia Montoya")
        st.caption(f"Simulación en tiempo real: {t_presente.strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Fila de Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><div class="metric-title">AGUA (L) 💧</div><div class="metric-value">{actual_row["consumo_agua"]:.1f}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-title">ENERGÍA (KWH) ⚡</div><div class="metric-value">{actual_row["consumo_electrico"]:.3f}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-title">HUMEDAD (%) ☁️</div><div class="metric-value">{actual_row["humedad_interior"]:.1f}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="metric-title">TEMP (°C) 🌡️</div><div class="metric-value">{actual_row["temperatura_int"]:.1f}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        # Fila de Gráficos y Gas
        col_charts, col_gas = st.columns([4, 1])
        with col_charts:
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.write("📊 **Histórico Reciente: Agua**")
                st.area_chart(df_presente.tail(30).set_index('timestamp')['consumo_agua'], height=250)
            with g_col2:
                st.write("📊 **Histórico Reciente: Energía**")
                st.line_chart(df_presente.tail(30).set_index('timestamp')['consumo_electrico'], height=250)
        
        with col_gas:
            st.write("⛽ **Nivel de Gas**")
            val_gas = float(actual_row['gas_nivel'])
            st.markdown(f"""
                <div class="gas-wrapper">
                    <div class="gas-container">
                        <div class="gas-fill" style="height:{val_gas}%;"></div>
                    </div>
                    <div class="gas-percentage">{val_gas:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        # Botones de Navegación Inferiores
        nav1, nav2, nav3 = st.columns(3)
        if nav1.button("📊 Ver Historial de Datos", use_container_width=True):
            st.session_state.vista = "datos"; st.rerun()
        if nav2.button("🚨 Ver Historial de Alarmas", use_container_width=True):
            st.session_state.vista = "alarmas"; st.rerun()
        if nav3.button("📞 Abrir Directorio", use_container_width=True):
            st.session_state.vista = "directorio"; st.rerun()

# 6. LÓGICA DE ACTUALIZACIÓN (Solo corre en la vista principal)
if st.session_state.corriendo and st.session_state.vista == "principal":
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.1)
        st.rerun()
