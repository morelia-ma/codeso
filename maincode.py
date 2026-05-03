import streamlit as st
import pandas as pd
import time
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

# 3. CARGA DE DATOS
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

df_raw, df_alertas_raw = load_data()

# 4. ESTADO DE SESIÓN
if 'indice' not in st.session_state: st.session_state.indice = 0
if 'corriendo' not in st.session_state: st.session_state.corriendo = False
if 'vista' not in st.session_state: st.session_state.vista = "principal"

# 5. LÓGICA DE TIEMPO
if not df_raw.empty:
    actual_row = df_raw.iloc[st.session_state.indice]
    t_presente = actual_row['timestamp']
    df_presente = df_raw[df_raw['timestamp'] <= t_presente]
    df_alertas_presente = df_alertas_raw[df_alertas_raw['timestamp'] <= t_presente]

# 6. SIDEBAR (Lógica de alertas unificadas por día)
with st.sidebar:
    st.header("🎮 Control")
    c1, c2 = st.columns(2)
    if c1.button("▶️ Iniciar", use_container_width=True): st.session_state.corriendo = True
    if c2.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.indice = 0; st.session_state.corriendo = False; st.rerun()
    
    st.markdown("---")
    
    # Predicción de Gas
    if not df_raw.empty:
        nivel_gas_val = float(actual_row['gas_nivel'])
        if nivel_gas_val < 25:
            st.markdown(f"""
            <div class="prediction-card">
                <div class="prediction-title">🔮 Predicción</div>
                <div class="prediction-text">Nivel bajo ({nivel_gas_val:.1f}%). Agotamiento probable en <b>10 días</b>.</div>
            </div>
            """, unsafe_allow_html=True)

    st.subheader("🔔 Últimas Alertas")
    
    if not df_alertas_presente.empty:
        # 1. Filtramos por las últimas 24 horas
        filtro_24h = df_alertas_presente[df_alertas_presente['timestamp'] >= t_presente - timedelta(hours=24)].copy()
        
        if not filtro_24h.empty:
            # 2. Creamos una columna de 'fecha' para agrupar por día
            filtro_24h['fecha_solo'] = filtro_24h['timestamp'].dt.date
            
            # 3. Lógica: Si el mensaje contiene "Fuga de gas", solo mostramos la última de ese día
            # Para otros tipos de alertas (ej. temperatura), podrías dejar que se repitan si prefieres,
            # pero aquí aplicamos la regla de "una por día si es el mismo mensaje".
            alertas_unicas = filtro_24h.sort_values('timestamp').drop_duplicates(subset=['fecha_solo', 'mensaje'], keep='last')
            
            for _, fila in alertas_unicas.tail(3).iterrows():
                st.caption(f"🕒 {fila['timestamp'].strftime('%H:%M')} - {fila['mensaje']}")
        else:
            st.write("Sin alertas en las últimas 24h.")
    else:
        st.write("Sin alertas registradas.")

# 7. VISTAS
if not df_raw.empty:
    # --- VISTA: DATOS ---
    if st.session_state.vista == "datos":
        st.header("📊 Historial de Telemetría")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
        
        # Filtros para la tabla de datos
        meses = df_presente['timestamp'].dt.month_name().unique()
        mes_sel = st.selectbox("Selecciona Mes", options=meses)
        
        dias = df_presente[df_presente['timestamp'].dt.month_name() == mes_sel]['timestamp'].dt.day.unique()
        dia_sel = st.selectbox("Selecciona Día", options=dias)
        
        # Filtrado y visualización
        df_filtrado = df_presente[(df_presente['timestamp'].dt.month_name() == mes_sel) & 
                                 (df_presente['timestamp'].dt.day == dia_sel)]
        
        st.dataframe(df_filtrado.sort_values(by='timestamp', ascending=False), use_container_width=True)

    # --- VISTA: ALARMAS ---
    elif st.session_state.vista == "alarmas":
        st.header("🚨 Histórico de Alarmas")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
        
        if not df_alertas_presente.empty:
            # Filtros para la tabla de alarmas
            meses_al = df_alertas_presente['timestamp'].dt.month_name().unique()
            mes_al_sel = st.selectbox("Selecciona Mes", options=meses_al)
            
            dias_al = df_alertas_presente[df_alertas_presente['timestamp'].dt.month_name() == mes_al_sel]['timestamp'].dt.day.unique()
            dia_al_sel = st.selectbox("Selecciona Día", options=dias_al)
            
            # Aplicamos la misma lógica de no repetir gas por día en el historial si lo deseas, 
            # o mostramos todo el log detallado aquí:
            al_fil = df_alertas_presente[(df_alertas_presente['timestamp'].dt.month_name() == mes_al_sel) & 
                                        (df_alertas_presente['timestamp'].dt.day == dia_al_sel)]
            
            st.table(al_fil.sort_values(by='timestamp', ascending=False))
        else:
            st.info("No hay alarmas registradas hasta el momento.")

    # --- VISTA: DIRECTORIO ---
    elif st.session_state.vista == "directorio":
        st.header("📞 Directorio de Emergencia")
        if st.button("⬅ Volver"): 
            st.session_state.vista = "principal"
            st.rerun()
            
        directorio = pd.DataFrame({
            "Servicio": ["Emergencias", "Protección Civil", "Fugas de Gas", "Suministro de Agua"],
            "Número": ["911", "555-0199", "800-GAS-LINE", "555-0102"]
        })
        st.table(directorio)

    # --- VISTA: PANEL PRINCIPAL ---
    elif st.session_state.vista == "principal":
        # (Aquí va todo el código del Dashboard principal con las métricas y gráficas)
        # Asegúrate de mantener el código que ya teníamos para st.title, las columnas de métricas, etc.

# 8. BUCLE
if st.session_state.corriendo and st.session_state.vista == "principal":
    if st.session_state.indice < len(df_raw) - 1:
        st.session_state.indice += 1
        time.sleep(0.1)
        st.rerun()
