import streamlit as st
import pandas as pd
import time

# 1. Configuración de pantalla completa y tema
st.set_page_config(page_title="CODESO Smart Home HMI", layout="wide", initial_sidebar_state="collapsed")

# 2. Estilo CSS Avanzado para que se vea "Premium"
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Roboto', sans-serif; }
    .stMetric { border-radius: 15px; background-color: #ffffff; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #0077B6; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; }
    .status-box { padding: 20px; border-radius: 15px; text-align: center; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('datos_domotia.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df_full = load_data()

# Título con estilo de Tablero de Control
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏠 Centro de Control Residencial</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B;'>Monitoreo en Tiempo Real - Plan Sonora / CODESO</p>", unsafe_allow_html=True)

# Espacios dinámicos
kpi_zone = st.empty()
alert_zone = st.empty()
chart_zone = st.empty()

# Botón de inicio en el sidebar
if st.sidebar.button("▶️ Iniciar HMI"):
    for i in range(1, len(df_full)):
        actual = df_full.iloc[i]
        anterior = df_full.iloc[i-1]
        # Ventana de las últimas 12 horas para que la gráfica no se sature
        ventana = df_full.iloc[max(0, i-24):i]

        # --- SECCIÓN DE MÉTRICAS (KPIs) ---
        with kpi_zone.container():
            c1, c2, c3, c4 = st.columns(4)
            # Aplicando Semiótica del Color de tu documento
            c1.metric("FLUJO AGUA 💧", f"{actual['consumo_agua']:.1f} L", f"{actual['consumo_agua'] - anterior['consumo_agua']:.1f} L", delta_color="inverse")
            c2.metric("ENERGÍA ⚡", f"{actual['consumo_electrico']:.3f} kWh", f"{actual['consumo_electrico'] - anterior['consumo_electrico']:.3f} kWh", delta_color="inverse")
            c3.metric("GAS LP 🔥", f"{actual['gas_nivel'] if pd.notnull(actual['gas_nivel']) else 98}%")
            c4.metric("CONFORT TÉRMICO 🌡️", f"{actual['temperatura_int']:.1f} °C")

        # --- SISTEMA DE ALERTAS ESPECÍFICAS (¿Qué pasó?) ---
        with alert_zone.container():
            if actual['anomalia']:
                tipo = str(actual['tipo_anomalia']).lower()
                # Lógica para identificar el tipo de falla
                if 'agua' in tipo or 'fuga' in tipo:
                    st.error(f"⚠️ **FALLA DETECTADA:** Posible fuga de AGUA. Revisa las tuberías en {actual['timestamp'].strftime('%H:%M')}.")
                elif 'gas' in tipo:
                    st.warning(f"🚨 **PELIGRO:** Concentración de GAS detectada. Ventila el área inmediatamente.")
                elif 'voltaje' in tipo or 'eléctrico' in tipo:
                    st.info(f"⚡ **AVISO:** Pico de consumo ELÉCTRICO detectado.")
                else:
                    st.error(f"❗ **ANOMALÍA DESCONOCIDA:** {actual['tipo_anomalia']}")
            else:
                st.success("✅ Todos los sistemas operando con normalidad.")

        # --- GRÁFICAS DE ALTA FIDELIDAD ---
        with chart_zone.container():
            col_a, col_b = st.columns(2)
