import streamlit as st
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm import ServicioLLM
from core.prompting import construir_mensajes
from core.conversation import GestorConversacion

load_dotenv()

st.set_page_config(
    page_title="AI Copilot", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0" />
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px !important;
        padding-left: 20px;
        border: 1px solid #303030;
    }
    .stChatInput > div > div > textarea {
        border-radius: 25px !important;
    }
    .stButton > button {
        border-radius: 20px !important;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    
    div[data-testid="stSidebar"] {
        background-color: #161a24;
        border-right: 1px solid #2b303b;
    }
    
    .metric-card {
        background-color: #1f2533;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #2b303b;
        margin-bottom: 10px;
    }
    
    .icon {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        vertical-align: middle;
        margin-right: 8px;
        color: #7d8ba1;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
    }
    .highlight {
        color: #4facfe;
        font-weight: bold;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if "gestor" not in st.session_state:
    st.session_state.gestor = GestorConversacion()
if "servicio_llm" not in st.session_state:
    st.session_state.servicio_llm = ServicioLLM()

if "salida_total" not in st.session_state:
    st.session_state.salida_total = 0
if "historial_latencias" not in st.session_state:
    st.session_state.historial_latencias = []

gestor = st.session_state.gestor
servicio = st.session_state.servicio_llm

def calcular_metricas_estabilidad(latencias):
    if not latencias: return 0, 0
    datos = sorted(latencias)
    n = len(datos)
    p50 = datos[int(n * 0.5)]
    idx95 = int(n * 0.95)
    if idx95 >= n: idx95 = n - 1
    p95 = datos[idx95]
    return p50, p95

with st.sidebar:
    st.markdown("### <span class='icon'>tune</span>Configuración", unsafe_allow_html=True)
    
    with st.container():
        temperatura = st.slider("Temperatura", 0.0, 1.0, 0.7)
        top_p = st.slider("Top P", 0.0, 1.0, 1.0)
        max_tokens = st.number_input("Max Tokens", 50, 4096, 512)
        seed = st.number_input("Seed", value=0)

    st.markdown("---")

    st.markdown("### <span class='icon'>credit_card</span>Plan", unsafe_allow_html=True)
    
    turnos = gestor.contador_turnos
    limite = gestor.limite_turnos
    pct = min(turnos / limite, 1.0)
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="color:#aaa; font-size:14px;">Mensajes</span>
            <span style="color:#fff; font-weight:bold;">{turnos} / {limite}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if pct < 0.8:
        st.progress(pct, "Activo")
    else:
        st.progress(pct, "Límite próximo")
    
    if turnos >= limite:
        st.error("Límite alcanzado.")

    st.markdown("---")

    with st.expander("Ver Comandos de Ayuda"):
        st.markdown("""
        | Comando | Acción |
        | :--- | :--- |
        | `/nota` | Guardar nota |
        | `/recordatorio` | Agendar |
        | `/busqueda` | Investigar |
        | `/misnotas` | Ver lista |
        | `/limpiar` | Reiniciar |
        """)

    st.markdown("---")

    st.markdown("### <span class='icon'>analytics</span>Rendimiento", unsafe_allow_html=True)
    
    val_p50, val_p95 = calcular_metricas_estabilidad(st.session_state.historial_latencias)
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; text-align: center;">
            <div>
                <div style="color:#7d8ba1; font-size:12px;">Latencia (p50)</div>
                <div style="color:#4facfe; font-size:18px; font-weight:bold;">{val_p50}s</div>
            </div>
            <div>
                <div style="color:#7d8ba1; font-size:12px;">Latencia (p95)</div>
                <div style="color:#ff6b6b; font-size:18px; font-weight:bold;">{val_p95}s</div>
            </div>
        </div>
        <div style="margin-top:10px; border-top:1px solid #2b303b; paddingTop:5px; text-align:center;">
            <span style="color:#aaa; font-size:12px;">Total Tokens: </span>
            <span style="color:#fff; font-weight:bold;">{st.session_state.salida_total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Limpiar Sesión", type="primary", use_container_width=True):
        gestor.procesar_comando("/limpiar")
        st.session_state.salida_total = 0
        st.session_state.historial_latencias = []
        if "ultimas_metricas" in st.session_state:
            del st.session_state.ultimas_metricas
        st.rerun()

st.markdown("## <span class='icon' style='font-size:32px; color:#4facfe'>smart_toy</span>AI Copilot", unsafe_allow_html=True)
st.markdown("<div style='margin-top: -15px; color: #777; margin-bottom: 30px;'>Asistente Inteligente de Productividad y Aprendizaje</div>", unsafe_allow_html=True)

for mensaje in gestor.obtener_historial():
    role_icon = "assistant" if mensaje["role"] == "assistant" else "user"
    
    with st.chat_message(mensaje["role"], avatar=role_icon):
        st.markdown(mensaje["content"])

if prompt_usuario := st.chat_input("Escribe tu consulta..."):
    
    with st.chat_message("user", avatar="user"):
        st.markdown(prompt_usuario)
    gestor.actualizar_historial("user", prompt_usuario)

    with st.chat_message("assistant", avatar="assistant"):
        contenedor = st.empty()
        contenedor.markdown("""
            <div style="display:flex; align-items:center; color:#aaa;">
                <span class="icon" style="font-size:18px; animation: spin 2s linear infinite;">sync</span>
                Generando respuesta...
            </div>
        """, unsafe_allow_html=True)
        
        try:
            resultado_sistema = gestor.procesar_comando(prompt_usuario)
            
            if resultado_sistema and resultado_sistema.startswith("BLOCK:"):
                error_msg = resultado_sistema.replace("BLOCK: ", "")
                contenedor.error(error_msg, icon="⚠️")
                st.rerun()
                st.stop()

            mensajes_api = construir_mensajes(gestor.obtener_historial()[:-1], prompt_usuario)
            if resultado_sistema:
                mensajes_api.append({"role": "system", "content": resultado_sistema})

            seed_val = int(seed) if seed != 0 else None
            resultado = servicio.generar_respuesta(
                mensajes=mensajes_api,
                temperatura=temperatura,
                max_tokens=max_tokens,
                top_p=top_p,
                seed=seed_val
            )
            
            texto = resultado.get("contenido", "")
            
            if resultado.get("error"):
                st.error(texto, icon="⚠️")
            else:
                contenedor.markdown(texto)
                gestor.actualizar_historial("assistant", texto)
                
                st.session_state.historial_latencias.append(resultado.get("latencia", 0))
                if resultado.get("uso"):
                    st.session_state.salida_total += resultado['uso']['tokens_salida']
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Error crítico: {str(e)}")