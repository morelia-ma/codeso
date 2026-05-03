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
    .prediction-card {
        background-color: #E8F5E9; border: 1px solid #C8E6C9;
        border-radius: 8px; padding: 10px; margin-bottom: 15px;
    }
    .prediction-title { color: #2E7D32; font-weight: bold; font-size: 0.9rem; margin-bottom: 4px; text-transform: uppercase; }
    .prediction-text { color: #388E3C; font-size: 0.85rem; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES DE PERSISTENCIA (DIRECTORIO)
def cargar_directorio():
    if os.path.exists('directorio.csv'):
        return pd.read_csv('directorio.csv')
    else:
        df_ini = pd.DataFrame({"Servicio": ["Emergencias", "Fugas Gas", "Agua"], "Número": ["911", "800-GAS-LINE", "555-0102"]})
        df_ini.to_csv('directorio.csv', index=False)
        return df_ini

def guardar_contacto(servicio, numero):
    df = cargar_directorio()
    nuevo = pd.DataFrame({"Servicio": [servicio], "Número": [str(numero)]})
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv('directorio.csv', index=False)

def eliminar_contacto(index):
    df = cargar_directorio()
    df = df.drop(index)
    df.to_csv('directorio.csv', index=False)

# 4. CARGA DE DATOS TELEMETRÍA
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df['gas_nivel'] = df['gas_nivel'].ffill().bfill().fillna(0).astype(float)
        
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_raw, df_alertas_raw = load_data()

# 5. ESTADO DE SESIÓN
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# 6. LÓGICA DE TIEMPO
if not df_raw.empty:
    actual_row = df_raw.iloc[st.session_state.indice]
    t_presente = actual_row['timestamp']
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]
    df_alertas_presente = df_alertas_raw[df_alertas_raw['timestamp'] <= t_presente]

# 7. SIDEBAR
with st.sidebar:
    st.header("🎮 Control")
    c1, c2 = st.columns(2)
    if c1.button("▶️ Iniciar", use_container_width=True): st.session_state.corriendo = True
    if c2.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0; st.session_state.corriendo = False; st.rerun()
    
    st.markdown("---")
    
    if not df_raw.empty:
        nivel_gas_val = float(actual_row['gas_nivel'])
        if nivel_gas_val < 25:
            st.markdown(f"""<div class="prediction-card"><div class="prediction-title">🔮 Predicción</div>
            <div class="prediction-text">Nivel bajo ({nivel_gas_val:.1f}%). Agotamiento probable en <b>10 días</b>.</div></div>""", unsafe_allow_html=True)

    st.subheader("🔔 Últimas Alertas")
    if not df_alertas_presente.empty:
        alertas_recientes = df_alertas_presente.tail(10).copy()
        alertas_recientes['fecha_solo'] = alertas_recientes['timestamp'].dt.date
        alertas_unicas = alertas_recientes.sort_values('timestamp').drop_duplicates(subset=['fecha_solo', 'mensaje'], keep='last')
        
        for _, fila in alertas_unicas.tail(3).iterrows():
            st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")
    else:
        st.write("Sin alertas registradas.")

# 8. VISTAS (Lógica de Navegación Corregida)
if not df_raw.empty:
    if st.session_state.vista == "datos":
        st.header("📊 Historial de Telemetría")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
        meses = df_presente['timestamp'].dt.month_name().unique()
        mes_sel = st.selectbox("Selecciona Mes", options=meses)
        dias = df_presente[df_presente['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique()
        dia_sel = st.selectbox("Selecciona Día", options=dias)
        df_filtrado = df_presente[(df_presente['timestamp'].dt.month_name() == mes_sel) & (df_presente['timestamp'].dt.day == dia_sel)]
        st.dataframe(df_filtrado.sort_values(by='timestamp', ascending=False), use_container_width=True)

    elif st.session_state.vista == "alarmas":
        st.header("🚨 Histórico de Alarmas")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
        
        if not df_alertas_presente.empty:
            meses_al = df_alertas_presente['timestamp'].dt.month_name().unique()
            mes_sel_al = st.selectbox("Selecciona Mes de Alarma", options=meses_al)
            dias_al = df_alertas_presente[df_alertas_presente['timestamp'].dt.month_name() == mes_sel_al]['timestamp'].dt.day.unique()
            dia_sel_al = st.selectbox("Selecciona Día de Alarma", options=dias_al)
            
            df_al_filtrado = df_alertas_presente[
                (df_alertas_presente['timestamp'].dt.month_name() == mes_sel_al) & 
                (df_alertas_presente['timestamp'].dt.day == dia_sel_al)
            ]
            st.table(df_al_filtrado.sort_values(by='timestamp', ascending=False))
        else:
            st.info("No hay alarmas registradas.")

    elif st.session_state.vista == "directorio":
        st.header("📞 Directorio de Servicios")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
        
        col_add, col_list = st.columns([1, 2])
        with col_add:
            st.subheader("Añadir Contacto")
            with st.form("nuevo_contacto", clear_on_submit=True):
                nombre_s = st.text_input("Nombre del Servicio")
                numero_s = st.text_input("Número")
                if st.form_submit_button("Guardar"):
                    if nombre_s and numero_s:
                        guardar_contacto(nombre_s, numero_s)
                        st.success("Guardado")
                        st.rerun()
        
        with col_list:
            st.subheader("Lista de Contactos")
            df_dir = cargar_directorio()
            for idx, row in df_dir.iterrows():
                c_info, c_del = st.columns([3, 1])
                c_info.write(f"**{row['Servicio']}**: {row['Número']}")
                if c_del.button("Eliminar", key=f"del_{idx}"):
                    eliminar_contacto(idx)
                    st.rerun()

    elif st.session_state.vista == "principal":
        st.title("🏠 Monitoreo Familia Montoya")
        st.caption(f"Simulación: {t_presente.strftime('%d/%m/%Y %H:%M:%S')}")
        
        cols = st.columns(4)
        met = [("Agua (L) 💧", actual_row["consumo_agua"], "{:.1f}"), ("Energía (kWh) ⚡", actual_row["consumo_electrico"], "{:.3f}"),
               ("Humedad (%) ☁️", actual_row["humedad_interior"], "{:.1f}"), ("Temp (°C) 🌡️", actual_row["temperatura_int"], "{:.1f}")]
        for i, (l, v, f) in enumerate(met):
            with cols[i]: st.markdown(f'<div class="metric-card"><div class="metric-title">{l}</div><div class="metric-value">{f.format(v)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
        
        c_graf, c_gas = st.columns([4, 0.8])
        ventana = df_presente.tail(30).set_index('timestamp')
        with c_graf:
            g1, g2 = st.columns(2)
            with g1: 
                st.caption("📈 Histórico Reciente: Agua")
                st.area_chart(ventana['consumo_agua'], height=250)
            with g2: 
                st.caption("📈 Histórico Reciente: Energía")
                st.line_chart(ventana['consumo_electrico'], height=250, color="#FFB703")
        
        with c_gas:
            st.caption("⛽ Nivel de Gas")
            v_gas_ui = float(actual_row['gas_nivel'])
            st.markdown(f"""
                <div class="gas-wrapper">
                    <div class="gas-container">
                        <div class="gas-fill" style="height: {v_gas_ui}%;"></div>
                    </div>
                    <div class="gas-percentage">{v_gas_ui:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        n1, n2, n3, _ = st.columns([1, 1, 1, 1])
        if n1.button("📊 Historial Datos", use_container_width=True): 
            st.session_state.vista = "datos"
            st.rerun()
        if n2.button("🚨 Historial Alarmas", use_container_width=True): 
            st.session_state.vista = "alarmas"
            st.rerun()
        if n3.button("📞 Directorio", use_container_width=True): 
            st.session_state.vista = "directorio"
            st.rerun()

# 9. BUCLE SIMULACIÓN
if st.session_state.corriendo and st.session_state.vista == "principal":
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.1)
        st.rerun()
