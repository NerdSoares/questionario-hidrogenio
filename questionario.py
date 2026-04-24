import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Questionário Completo - Itaipu", layout="centered")

# --- LISTA DE COLUNAS ATUALIZADA (CABEÇALHO) ---
COLUNAS = [
    "Data/Hora", "Nome", "Cargo",
    "Dim_Econômica", "Dim_Ambiental", "Dim_Técnica", "Dim_Estratégica", "Dim_Social",
    "Eco_CAPEX", "Eco_OPEX", "Eco_LCOE",
    "Amb_CO2", "Amb_NOx", "Amb_Ruído", "Amb_Clima",
    "Tec_Confiabilidade", "Tec_Maturidade",
    "Est_Alinhamento", "Est_Liderança", "Est_PeD",
    "Soc_Aceitação", "Soc_Legitimidade", "Soc_Reputação",
    # Desempenhos Qualitativos (Diesel vs H2)
    "Perf_Clima_Diesel", "Perf_Clima_H2",
    "Perf_Inst_Diesel", "Perf_Inst_H2",
    "Perf_Lider_Diesel", "Perf_Lider_H2",
    "Perf_PD_Diesel", "Perf_PD_H2",
    "Perf_Soc_Diesel", "Perf_Soc_H2",
    "Perf_Legit_Diesel", "Perf_Legit_H2",
    "Perf_Reput_Diesel", "Perf_Reput_H2"
]

# --- INICIALIZAÇÃO DA MEMÓRIA ---
if 'passo' not in st.session_state: st.session_state.passo = 0
if 'respostas' not in st.session_state: st.session_state.respostas = {"Pesos": {}, "Desempenhos": {}}
if 'nome' not in st.session_state: st.session_state.nome = ""
if 'cargo' not in st.session_state: st.session_state.cargo = ""

# --- FUNÇÃO PARA SALVAR NO GOOGLE SHEETS ---
def save_to_sheets(respostas, nome, cargo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open("Respostas_SWING_Itaipu").sheet1

        # Prepara a linha com Data, Nome e Cargo
        row = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nome, cargo]
        
        # Adiciona os Pesos na ordem das colunas
        p = respostas["Pesos"]
        # Ordem: Dimensões -> Econômica -> Ambiental -> Técnica -> Estratégica -> Social
        if "Dimensões Principais" in p:
            for val in p["Dimensões Principais"].values(): row.append(val)
        
        categorias = ["Dimensão Econômica", "Dimensão Ambiental", "Dimensão Técnica", "Dimensão Estratégica", "Dimensão Social"]
        for cat in categorias:
            if cat in p:
                for val in p[cat].values(): row.append(val)
        
        # Adiciona os Desempenhos
        d = respostas["Desempenhos"]
        ordem_perf = ["Clima", "Inst", "Lider", "PD", "Soc", "Legit", "Reput"]
        for crit in ordem_perf:
            row.append(d.get(f"{crit}_Diesel", 0))
            row.append(d.get(f"{crit}_H2", 0))

        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- COMPONENTES VISUAIS ---
def swing_method_component(section_title, items_data, key_suffix, texto_explicativo):
    st.header(section_title)
    st.info(texto_explicativo)
    selected_best = st.radio(f"🏆 Qual critério você melhoraria primeiro?", list(items_data.keys()), key=f"radio_{key_suffix}")
    st.write(f"⚖️ Pontue os outros em relação a {selected_best} (0-100):")
    scores = {}
    for item in items_data.keys():
        val = 100 if item == selected_best else 50
        scores[item] = st.slider(f"{item}", 0, 100, val, disabled=(item == selected_best), key=f"s_{item}_{key_suffix}")
    return scores

def performance_component(title, description, key_prefix):
    st.header(title)
    st.info(f"📊 {description}")
    col1, col2 = st.columns(2)
    with col1: n_d = st.select_slider(f"Nota DIESEL", options=list(range(11)), value=5, key=f"{key_prefix}_d")
    with col2: n_h = st.select_slider(f"Nota HIDROGÊNIO", options=list(range(11)), value=5, key=f"{key_prefix}_h")
    return n_d, n_h

# --- CABEÇALHO (LOGOS) ---
# Alinhado conforme sua última imagem unificada ou ajuste de colunas
logocol1, logocol2 = st.columns([4, 6])
if os.path.exists("itaipu_binacional.jpg"): 
    with logocol1: st.image("itaipu_binacional.jpg", use_column_width=True)
if os.path.exists("itaipu_parquetec.jpg"): 
    with logocol2: st.image("itaipu_parquetec.jpg", use_column_width=True)
st.divider()

# --- NAVEGAÇÃO ---

# PASSO 0: INÍCIO (NOME E CARGO)
if st.session_state.passo == 0:
    st.title("Pesquisa de Transição Energética")
    st.markdown("Bem-vindo! Esta pesquisa avalia a viabilidade do Hidrogênio para o Data Center da Itaipu.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        nome_input = st.text_input("Seu Nome (Opcional):", value=st.session_state.nome).strip()
    with col_b:
        cargo_input = st.text_input("Seu Cargo (Obrigatório):", value=st.session_state.cargo).strip()
    
    if st.button("Iniciar Questionário 🚀", type="primary"):
        if cargo_input: 
            st.session_state.nome = nome_input
            st.session_state.cargo = cargo_input
            st.session_state.passo = 1
            st.rerun()
        else:
            st.error("⚠️ Por favor, informe o seu Cargo para prosseguir.")

# PASSOS 1-6: PESOS (SWING)
elif 1 <= st.session_state.passo <= 6:
    vids = ["9xgrM1Unbmk", "T21b2c8yjm4", "ZFjj2DgvHYI", "gNoDM3wVYwM", "FpnmfL2XqEo", "8XzA2ZWt0Ck"]
    st.video(f"https://youtu.be/{vids[st.session_state.passo-1]}")
    
    data_map = [None, 
        ("Dimensões Principais", {"Econômica": "Custos", "Ambiental": "Impactos", "Técnica": "Engenharia", "Estratégica": "Visão", "Social": "Sociedade"}, "dim"),
        ("Dimensão Econômica", {"CAPEX": "Investimento", "OPEX": "Operação", "LCOE": "Custo Energia"}, "eco"),
        ("Dimensão Ambiental", {"CO2": "Emissões GEE", "NOx": "Poluentes", "Ruído": "Barulho", "Clima": "Metas"}, "amb"),
        ("Dimensão Técnica", {"Confiabilidade": "Falhas", "Maturidade": "Tecnologia"}, "tec"),
        ("Dimensão Estratégica", {"Alinhamento": "Visão Itaipu", "Liderança": "Inovação", "PeD": "Cadeia H2"}, "est"),
        ("Dimensão Social", {"Aceitação": "Comunidade", "Legitimidade": "Parceiros", "Reputação": "Imagem"}, "soc")
    ]
    
    curr_data = data_map[st.session_state.passo]
    res = swing_method_component(curr_data[0], curr_data[1], curr_data[2], f"Defina as prioridades para {curr_data[0]}.")
    
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("⬅️ Voltar"): st.session_state.passo -= 1; st.rerun()
    with col2:
        if st.button("Próximo ➡️"):
            st.session_state.respostas["Pesos"][curr_data[0]] = res
            st.session_state.passo += 1; st.rerun()

# PASSO 7: TRANSIÇÃO E EXPLICAÇÃO DAS NOTAS
elif st.session_state.passo == 7:
    st.title("🎯 Nova Etapa: Avaliação de Desempenho")
    st.video("https://youtu.be/69oZ8pPBJIY")
    st.success("Prioridades definidas! Agora, dê notas de 0 a 10 para cada tecnologia.")
    st.markdown("""
    Nesta fase, avaliamos como o **Diesel** e o **Hidrogênio** se comportam nos critérios qualitativos.
    - **0** = Desempenho Péssimo
    - **10** = Desempenho Excelente
    """)
    if st.button("Começar Avaliações ➡️", type="primary"): st.session_state.passo = 8; st.rerun()

# PASSOS 8-14: NOTAS (0-10)
elif 8 <= st.session_state.passo <= 14:
    perfs = [
        ("Alinhamento Climático", "Contribuição para descarbonização.", "Clima"),
        ("Alinhamento Institucional", "Aderência aos valores da Itaipu.", "Inst"),
        ("Liderança Tecnológica", "Potencial de referência em inovação.", "Lider"),
        ("P&D em Hidrogênio", "Desenvolvimento do mercado de H2.", "PD"),
        ("Aceitação Social", "Percepção da comunidade local.", "Soc"),
        ("Legitimidade", "Validação por parceiros e critérios ESG.", "Legit"),
        ("Reputação", "Impacto na imagem da instituição.", "Reput")
    ]
    curr = perfs[st.session_state.passo - 8]
    d_val, h2_val = performance_component(curr[0], curr[1], curr[2])
    
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("⬅️ Voltar"): st.session_state.passo -= 1; st.rerun()
    with col2:
        if st.button("Próximo ➡️"):
            st.session_state.respostas["Desempenhos"][f"{curr[2]}_Diesel"] = d_val
            st.session_state.respostas["Desempenhos"][f"{curr[2]}_H2"] = h2_val
            st.session_state.passo += 1; st.rerun()

# PASSO 15: ENVIO FINAL
elif st.session_state.passo == 15:
    st.header("Concluído!")
    st.write(f"Obrigado, {st.session_state.nome if st.session_state.nome else 'Decisor'}. Suas respostas estão prontas para envio.")
    if st.button("📤 Enviar Respostas Definitivas", type="primary"):
        with st.spinner("Enviando dados..."):
            if save_to_sheets(st.session_state.respostas, st.session_state.nome, st.session_state.cargo):
                st.balloons(); st.session_state.passo = 16; st.rerun()

elif st.session_state.passo == 16:
    st.title("Muito Obrigado!")
    st.info("Suas respostas foram registradas com sucesso. Sua contribuição é fundamental.")
