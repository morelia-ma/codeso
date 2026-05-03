import streamlit as st
import pandas as pd
import time
import os

# 1. CONFIGURACIÓN
st.set_page_config(page_title="HMI Fam Montoya", layout="wide", initial_sidebar_state="expanded")

# Estilos (Mantenemos tus estilos originales)
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

# 2. FUNCIONES DE APOYO
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('datos_domotia_final.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        df['gas_nivel'] = df['gas_nivel'].ffill().bfill().fillna(0)
        df_al = pd.read_csv('alertas_historico.csv')
        df_al['timestamp'] = pd.to_datetime(df_al['timestamp']).dt.tz_localize(None)
        return df, df_al
    except:
        return pd.DataFrame(), pd.DataFrame()

def cargar_directorio():
    if os.path.exists('directorio.csv'):
        return pd.read_csv('directorio.csv')
    return pd.DataFrame({"Servicio": ["Emergencias", "Fugas Gas"], "Número": ["911", "800-GAS-LINE"]})

# 3. LÓGICA PRINCIPAL
def main():
    if 'indice' not in st.session_state: st.session_state.indice = 0
    if 'corriendo' not in st.session_state: st.session_state.corriendo = False
    if 'vista' not in st.session_state: st.session_state.vista = "principal"

    df_raw, df_alertas_raw = load_data()
    if df_raw.empty:
        st.error("No se encontraron datos.")
        return

    # SIDEBAR
    with st.sidebar:
        st.header("🎮 Control")
        c1, c2 = st.columns(2)
        if c1.button("▶️ Iniciar"): st.session_state.corriendo = True
        if c2.button("🔄 Reiniciar"):
            st.session_state.indice = 0
            st.session_state.corriendo = False
            st.session_state.vista = "principal"
            st.rerun()
        
        st.markdown("---")
        t_actual = df_raw.iloc[st.session_state.indice]['timestamp']
        st.subheader("🔔 Últimas Alertas")
        alertas = df_alertas_raw[df_alertas_raw['timestamp'] <= t_actual].tail(3)
        for _, fila in alertas.iterrows():
            st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")

    # --- CONTROL DE VISTAS ---
    
    # 1. VISTA DIRECTORIO
    if st.session_state.vista == "directorio":
        if st.button("⬅ Volver al Panel Principal"):
            st.session_state.vista = "principal"
            st.rerun()
        
        st.header("📞 Directorio de Contactos")
        col_f, col_l = st.columns([1, 2])
        with col_f:
            with st.form("nuevo_contacto", clear_on_submit=True):
                s = st.text_input("Servicio")
                n = st.text_input("Número")
                if st.form_submit_button("Guardar"):
                    df_d = cargar_directorio()
                    pd.concat([df_d, pd.DataFrame({"Servicio":[s],"Número":[n]})]).to_csv('directorio.csv', index=False)
                    st.rerun()
        with col_l:
            df_d = cargar_directorio()
            for idx, r in df_d.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.info(f"**{r['Servicio']}**: {r['Número']}")
                if c2.button("Eliminar", key=f"del_{idx}"):
                    df_d.drop(idx).to_csv('directorio.csv', index=False)
                    st.rerun()
        return # IMPORTANTE: Detiene la ejecución aquí para que no se dibuje lo de abajo

    # 2. VISTA DASHBOARD PRINCIPAL
    actual_row = df_raw.iloc[st.session_state.indice]
    t_presente = actual_row['timestamp']
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]

    st.title("🏠 Monitoreo Familia Montoya")
    st.caption(f"Simulación: {t_presente.strftime('%d/%m/%Y %H:%M:%S')}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-card"><div class="metric-title">AGUA (L) 💧</div><div class="metric-value">{actual_row["consumo_agua"]:.1f}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-card"><div class="metric-title">ENERGÍA (KWH) ⚡</div><div class="metric-value">{actual_row["consumo_electrico"]:.3f}</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-card"><div class="metric-title">HUMEDAD (%) ☁️</div><div class="metric-value">{actual_row["humedad_interior"]:.1f}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-card"><div class="metric-title">TEMP (°C) 🌡️</div><div class="metric-value">{actual_row["temperatura_int"]:.1f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)
    
    col_grafs, col_gas = st.columns([4, 1])
    with col_grafs:
        g1, g2 = st.columns(2)
        g1.write("📊 **Histórico Agua**")
        g1.area_chart(df_presente.tail(30).set_index('timestamp')['consumo_agua'], height=220)
        g2.write("📊 **Histórico Energía**")
        g2.line_chart(df_presente.tail(30).set_index('timestamp')['consumo_electrico'], height=220)
    
    with col_gas:
        st.write("⛽ **Nivel Gas**")
        gv = float(actual_row['gas_nivel'])
        st.markdown(f'<div class="gas-wrapper"><div class="gas-container"><div class="gas-fill" style="height:{gv}%;"></div></div><div class="gas-percentage">{gv:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📞 Abrir Directorio de Contactos", use_container_width=True):
        st.session_state.vista = "directorio"
        st.rerun()

    # BUCLE DE ANIMACIÓN
    if st.session_state.corriendo:
        if st.session_state.indice < len(df_raw) - 1:
            st.session_state.indice += 1
            time.sleep(0.05)
            st.rerun()

if __name__ == "__main__":
    main()
