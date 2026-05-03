import streamlit as st
import pandas as pd
import time
import os
from datetime import timedelta

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# 2. ESTILOS CSS
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
    .gas-fill { 
        background-color: #2ECC71; width: 100%; position: absolute; bottom: 0; 
        transition: height 0.5s ease-in-out; 
    }
    .gas-percentage { font-weight: bold; font-size: 1.1rem; color: #1f2d3d; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE PERSISTENCIA (DIRECTORIO)
def cargar_directorio():
    if os.path.exists('directorio.csv'):
        return pd.read_csv('directorio.csv')
    return pd.DataFrame({"Servicio": ["Emergencias", "Fugas Gas", "Agua"], "Número": ["911", "800-GAS-LINE", "555-0102"]})

def guardar_contacto(servicio, numero):
    df = cargar_directorio()
    nuevo = pd.DataFrame({"Servicio": [servicio], "Número": [str(numero)]})
    pd.concat([df, nuevo], ignore_index=True).to_csv('directorio.csv', index=False)

def eliminar_contacto(index):
    df = cargar_directorio()
    df.drop(index).to_csv('directorio.csv', index=False)

# 4. CARGA DE DATOS
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except: return pd.DataFrame(), pd.DataFrame()

df_raw, df_alertas_raw = load_data()

# 5. ESTADO DE SESIÓN
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# 6. SIDEBAR (Siempre visible)
with st.sidebar:
    st.header("🎮 Control")
    c1, c2 = st.columns(2)
    if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
    if c2.button("🔄 Reiniciar"):
        st.session_state.indice = 0; st.session_state.corriendo = False; st.rerun()
    
    st.markdown("---")
    st.subheader("🔔 Últimas Alertas")
    if not df_alertas_raw.empty:
        t_actual = df_raw.iloc[st.session_state.indice]['timestamp']
        recientes = df_alertas_raw[df_alertas_raw['timestamp'] <= t_actual].tail(3)
        if recientes.empty: st.write("Sin alertas registradas.")
        for _, fila in recientes.iterrows():
            st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")

# 7. LÓGICA DE NAVEGACIÓN (BLOQUES EXCLUYENTES)
if not df_raw.empty:
    actual_row = df_raw.iloc[st.session_state.indice]
    t_presente = actual_row['timestamp']
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]

    # VISTA: DATOS
    if st.session_state.vista == "datos":
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
        st.header("📊 Historial de Telemetría")
        mes_sel = st.selectbox("Mes", df_presente['timestamp'].dt.month_name().unique())
        dia_sel = st.selectbox("Día", df_presente[df_presente['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique())
        st.dataframe(df_presente[(df_presente['timestamp'].dt.month_name() == mes_sel) & (df_presente['timestamp'].dt.day == dia_sel)].sort_values(by='timestamp', ascending=False))

    # VISTA: ALARMAS (Actualizada con filtros de mes/día)
    elif st.session_state.vista == "alarmas":
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
        st.header("🚨 Histórico de Alarmas")
        df_al_pres = df_alertas_raw[df_alertas_raw['timestamp'] <= t_presente]
        if not df_al_pres.empty:
            m_al = st.selectbox("Selecciona Mes", df_al_pres['timestamp'].dt.month_name().unique())
            d_al = st.selectbox("Selecciona Día", df_al_pres[df_al_pres['timestamp'].dt.month_name() == m_al]['timestamp'].dt.day.unique())
            st.table(df_al_pres[(df_al_pres['timestamp'].dt.month_name() == m_al) & (df_al_pres['timestamp'].dt.day == d_al)].sort_values(by='timestamp', ascending=False))
        else: st.info("No hay alarmas.")

    # VISTA: DIRECTORIO
    elif st.session_state.vista == "directorio":
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
        st.header("📞 Directorio de Servicios")
        col_add, col_list = st.columns([1, 2])
        with col_add:
            with st.form("nuevo"):
                n, num = st.text_input("Servicio"), st.text_input("Número")
                if st.form_submit_button("Guardar"):
                    guardar_contacto(n, num); st.rerun()
        with col_list:
            df_dir = cargar_directorio()
            for idx, row in df_dir.iterrows():
                c_i, c_d = st.columns([3, 1])
                c_i.write(f"**{row['Servicio']}**: {row['Número']}")
                if c_d.button("Eliminar", key=f"del_{idx}"):
                    eliminar_contacto(idx); st.rerun()

    # VISTA: PRINCIPAL (Solo se muestra si vista == "principal")
    elif st.session_state.vista == "principal":
        st.title("🏠 Monitoreo Familia Montoya")
        st.caption(f"Simulación: {t_presente.strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><div class="metric-title">Agua (L)</div><div class="metric-value">{actual_row["consumo_agua"]:.1f}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-title">Energía (kWh)</div><div class="metric-value">{actual_row["consumo_electrico"]:.3f}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-title">Humedad (%)</div><div class="metric-value">{actual_row["humedad_interior"]:.1f}</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="metric-title">Temp (°C)</div><div class="metric-value">{actual_row["temperatura_int"]:.1f}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        # Gráficos y Gas
        cg, cgas = st.columns([4, 1])
        with cg:
            g1, g2 = st.columns(2)
            g1.area_chart(df_presente.tail(30).set_index('timestamp')['consumo_agua'], height=200)
            g2.line_chart(df_presente.tail(30).set_index('timestamp')['consumo_electrico'], height=200)
        with cgas:
            v = float(actual_row['gas_nivel'])
            st.markdown(f'<div class="gas-wrapper"><div class="gas-container"><div class="gas-fill" style="height:{v}%;"></div></div><div>{v:.1f}%</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        # Botones de Navegación
        b1, b2, b3 = st.columns(3)
        if b1.button("📊 Ver Historial Datos", use_container_width=True): 
            st.session_state.vista = "datos"; st.rerun()
        if b2.button("🚨 Ver Historial Alarmas", use_container_width=True): 
            st.session_state.vista = "alarmas"; st.rerun()
        if b3.button("📞 Ver Directorio", use_container_width=True): 
            st.session_state.vista = "directorio"; st.rerun()

# 8. BUCLE DE TIEMPO
if st.session_state.corriendo and st.session_state.vista == "principal":
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.1)
        st.rerun()
