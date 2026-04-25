import streamlit as st
import pandas as pd
import time

# 1. Configuración de pantalla
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide")

# 2. Estilo CSS "Premium"
st.markdown("""
    <style>
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    .stAlert { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Gestión del estado de la simulación
if 'indice' not in st.session_state:
    st.session_state.indice = 1 # Empezamos en 1 para tener un "anterior"
if 'corriendo' not in st.session_state:
    st.session_state.corriendo = False

@st.cache_data
def load_data():
    df = pd.read_csv('datos_domotia.csv')
    # LIMPIEZA DE COLUMNAS: Quita espacios vacíos en los nombres de las columnas
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# --- SIDEBAR CONTROL ---
st.sidebar.title("🕹️ Panel de Control")
if st.sidebar.button("▶️ Iniciar Simulación"):
    st.session_state.corriendo = True

if st.sidebar.button("⏹️ Detener"):
    st.session_state.corriendo = False
    st.session_state.indice = 1

st.sidebar.divider()
st.sidebar.write(f"Registro: {st.session_state.indice} / {len(df)}")

# --- CUERPO PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)

if st.session_state.corriendo:
    i = st.session_state.indice
    actual = df.iloc[i]
    anterior = df.iloc[i-1]
    
    # Ventana para gráficas (últimos 30 registros)
    ventana = df.iloc[max(0, i-30):i+1]

    # KPIs Principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AGUA 💧", f"{actual['consumo_agua']:.1f} L", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f} L", delta_color="inverse")
    c2.metric("ENERGÍA ⚡", f"{actual['consumo_electrico']:.3f} kWh", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f} kWh", delta_color="inverse")
    c3.metric("GAS LP 🔥", f"{actual['gas_nivel'] if pd.notnull(actual['gas_nivel']) else '95'}%")
    c4.metric("TEMP 🌡️", f"{actual['temperatura_int']:.1f} °C")

    # Diagnóstico de Alertas (¿Qué pasó?)
    if actual['anomalia'] == True or str(actual['anomalia']).lower() == 'true':
        tipo = str(actual['tipo_anomalia']).upper()
        if "FUGA" in tipo or "AGUA" in tipo:
            st.error(f"🚨 **ALERTA DE SEGURIDAD:** Se detectó una **FUGA DE AGUA**. Revisa las llaves de paso.")
        elif "GAS" in tipo:
            st.warning(f"☢️ **PELIGRO:** Anomalía en sistema de **GAS**. Ventila la casa.")
        else:
            st.error(f"⚠️ **ANOMALÍA DETECTADA:** {tipo}")
    else:
        st.success("✅ Sistemas estables. Consumo dentro del rango normal.")

    # Gráficas dinámicas
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Histórico de Agua (L)**")
        # Usamos el índice numérico si el timestamp falla
        st.area_chart(ventana['consumo_agua'], color="#0077B6")
    with col_b:
        st.write("**Histórico de Energía (kWh)**")
        st.line_chart(ventana['consumo_electrico'], color="#FFB703")

    # Control de tiempo y repetición
    if st.session_state.indice < len(df) - 1:
        st.session_state.indice += 1
        time.sleep(0.4)
        st.rerun()
    else:
        st.session_state.corriendo = False
        st.balloons()
        st.success("Simulación finalizada exitosamente.")
else:
    st.info("Sistema HMI en espera. Haz clic en 'Iniciar Simulación' en el panel izquierdo.")
