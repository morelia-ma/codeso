import streamlit as st
import pandas as pd
import time
from datetime import timedelta

# 1. Configuración de página
st.set_page_config(page_title="Smart Home HMI", layout="wide")

# 2. Estilos CSS
st.markdown("""
    <style>
    .gas-container {
        height: 350px; width: 100%; background-color: #f0f2f6;
        border-radius: 15px; position: relative; overflow: hidden; border: 2px solid #dfe3e6;
    }
    .gas-fill {
        background-color: #2ECC71; width: 100%; position: absolute;
        bottom: 0; transition: height 0.5s ease-in-out;
    }
    .gas-label {
        position: absolute; width: 100%; text-align: center;
        top: 45%; font-weight: bold; color: #1f2d3d; font-size: 1.3rem; z-index: 2;
    }
    .stMetric { 
        border-radius: 12px; background-color: #ffffff; padding: 15px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-bottom: 4px solid #0077B6; 
    }
    .bitacora-item { padding: 8px; border-bottom: 1px solid #eee; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. Carga de Datos
@st.cache_data
def load_all_data():
    try:
        df_gen = pd.read_csv('datos_domotia_final.csv')
        df_gen['timestamp'] = pd.to_datetime(df_gen['timestamp']).dt.tz_localize(None)
        df_gen['gas_nivel'] = pd.to_numeric(df_gen['gas_nivel'], errors='coerce').ffill().fillna(0)
        
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df_gen, df_al
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, df_alertas = load_all_data()

# Estado de la Sesión
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista_actual' not in st.session_state: st.session_state.vista_actual = "principal"
if 'lista_contactos' not in st.session_state:
    st.session_state.lista_contactos = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🕹️ Panel de Control")
    if st.button("▶️ Iniciar / ⏸️ Pausar", use_container_width=True):
        st.session_state.corriendo = not st.session_state.corriendo
    
    if st.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0
        st.session_state.corriendo = False
        st.rerun()

    st.divider()
    st.subheader("🔔 Alertas (Últimas 24h)")
    t_actual = df.iloc[st.session_state.indice]['timestamp']
    alertas_v = df_alertas[(df_alertas['timestamp'] <= t_actual) & (df_alertas['timestamp'] >= t_actual - timedelta(hours=24))]
    
    if not alertas_v.empty:
        for _, row in alertas_v.tail(5).iterrows():
            st.warning(f"{row['mensaje']}")
    else:
        st.success("✅ Sin alertas recientes")

# --- CUERPO PRINCIPAL ---
if not df.empty:
    actual = df.iloc[st.session_state.indice]

    if st.session_state.vista_actual == "principal":
        # Encabezado
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AGUA", f"{actual['consumo_agua']:.1f} L 💧")
        m2.metric("ENERGÍA", f"{actual['consumo_electrico']:.3f} kWh ⚡")
        m3.metric("HUMEDAD", f"{actual['humedad_interior']:.1f} % 💧")
        m4.metric("TEMP. INT", f"{actual['temperatura_int']:.1f} °C 🌡️")

        st.divider()

        col_graficas, col_tanque = st.columns([3, 1])

        with col_graficas:
            st.subheader("📊 Monitoreo en Tiempo Real")
            ventana = df.iloc[max(0, st.session_state.indice-50):st.session_state.indice+1].set_index('timestamp')
            
            st.caption("Consumo de Agua (L)")
            st.area_chart(ventana['consumo_agua'], color="#0077B6", height=180)
            
            st.caption("Consumo Eléctrico (kWh)")
            st.line_chart(ventana['consumo_electrico'], color="#FFB703", height=180)
            
            st.caption("Nivel de Gas (%)")
            st.line_chart(ventana['gas_nivel'], color="#2ECC71", height=120)

        with col_tanque:
            st.subheader("⛽ Tanque")
            p_gas = float(actual['gas_nivel'])
            st.markdown(f"""
                <div class="gas-container">
                    <div class="gas-label">{p_gas:.1f}%</div>
                    <div class="gas-fill" style="height: {p_gas}%;"></div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("📑 Historial de Datos", use_container_width=True): st.session_state.vista_actual = "datos"
        if c2.button("📜 Registro de Alarmas", use_container_width=True): st.session_state.vista_actual = "alarmas"
        if c3.button("📞 Directorio", use_container_width=True): st.session_state.vista_actual = "directorio"

    elif st.session_state.vista_actual == "directorio":
        st.subheader("📞 Directorio de Contactos")
        if st.button("⬅️ Volver al Panel"): st.session_state.vista_actual = "principal"; st.rerun()
        
        col_form, col_lista = st.columns([1, 1])
        
        with col_form:
            with st.form("nuevo_contacto", clear_on_submit=True):
                tipo = st.selectbox("Tipo de Servicio", ["Emergencia", "Bomberos", "Agua", "Luz", "Gas"])
                nombre = st.text_input("Nombre del Responsable/Servicio")
                numero = st.text_input("Número de Teléfono")
                if st.form_submit_button("Guardar Contacto"):
                    if nombre and numero:
                        st.session_state.lista_contactos.append({"Tipo": tipo, "Nombre": nombre, "Número": numero})
                        st.success("Guardado")
                    else:
                        st.error("Llena todos los campos")
        
        with col_lista:
            st.write("### Contactos Guardados")
            if st.session_state.lista_contactos:
                st.table(pd.DataFrame(st.session_state.lista_contactos))
            else:
                st.info("No hay contactos guardados.")

    elif st.session_state.vista_actual == "datos":
        st.subheader("📑 Historial Completo")
        if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
        # Aquí puedes añadir selectores de fecha si lo deseas
        st.dataframe(df[df['timestamp'] <= t_actual].tail(100), use_container_width=True)

    elif st.session_state.vista_actual == "alarmas":
        st.subheader("📜 Registro Histórico de Alarmas")
        if st.button("⬅️ Volver"): st.session_state.vista_actual = "principal"; st.rerun()
        st.table(df_alertas[df_alertas['timestamp'] <= t_actual].tail(20))

# Ejecución
if st.session_state.corriendo and st.session_state.indice < len(df) - 1:
    st.session_state.indice += 1
    time.sleep(0.1)
    st.rerun()
