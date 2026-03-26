import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os # Necessário para verificar a existência dos arquivos de imagem

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Questionário SWING - Itaipu", layout="centered")

# --- LISTA DEFINITIVA DE COLUNAS (CABEÇALHO) ---
COLUNAS = [
    "Data/Hora", "Nome do Decisor",
    "Dim_Econômica", "Dim_Ambiental", "Dim_Técnica", "Dim_Estratégica", "Dim_Social",
    "Eco_CAPEX", "Eco_OPEX", "Eco_LCOE",
    "Amb_CO2", "Amb_NOx", "Amb_Ruído", "Amb_Clima",
    "Tec_Confiabilidade", "Tec_Maturidade",
    "Est_Alinhamento", "Est_Liderança", "Est_PeD",
    "Soc_Aceitação", "Soc_Legitimidade", "Soc_Reputação"
]

# --- INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
if 'passo' not in st.session_state:
    st.session_state.passo = 0
if 'respostas' not in st.session_state:
    st.session_state.respostas = {}
if 'nome' not in st.session_state:
    st.session_state.nome = ""

# --- FUNÇÃO PARA SALVAR NO GOOGLE SHEETS ---
def save_to_sheets(data_dict, nome):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open("Respostas_SWING_Itaipu").sheet1

        try:
            valor_a1 = sheet.acell('A1').value
        except:
            valor_a1 = None

        if valor_a1 != "Data/Hora":
            sheet.insert_row(COLUNAS, 1)

        row = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nome]
        
        for val in data_dict["Dimensões"].values(): row.append(val)
        for cat in ["Econômica", "Ambiental", "Técnica", "Estratégica", "Social"]:
            for val in data_dict[cat].values(): row.append(val)

        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- COMPONENTE SWING ---
def swing_method_component(section_title, items_data, key_suffix, texto_explicativo):
    st.header(section_title)
    
    st.info(f"💡 **Contexto desta etapa:**\n\n{texto_explicativo}")
    
    st.markdown("🛑 **PASSO 1:** Imagine que todos os critérios abaixo estão no **PIOR NÍVEL POSSÍVEL**.")
    for item, description in items_data.items():
        st.markdown(f"- **{item}:** {description}")
    
    st.divider()
    selected_best = st.radio(f"🏆 **PASSO 2:** Qual critério você melhoraria primeiro, puxando do pior para o melhor nível?", list(items_data.keys()), key=f"radio_{key_suffix}")
    st.success(f"**{selected_best}** recebeu 100 pontos automaticamente.")
    
    st.divider()
    st.write(f"⚖️ **PASSO 3:** Agora, pontue os outros critérios em relação a {selected_best} (0-100).")
    
    scores = {}
    cols = st.columns(2)
    for i, item in enumerate(items_data.keys()):
        col = cols[i % 2]
        with col:
            if item == selected_best:
                scores[item] = st.slider(f"{item}", 0, 100, 100, disabled=True, key=f"s_{item}_{key_suffix}")
            else:
                scores[item] = st.slider(f"{item}", 0, 100, 50, key=f"s_{item}_{key_suffix}")
    return scores

# --- DEFINIÇÃO DOS DADOS ---
data_dim = {"Econômica": "Custos e tarifas máximas.", "Ambiental": "Alto impacto e emissões.", "Técnica": "Baixa confiabilidade.", "Estratégica": "Sem alinhamento corporativo.", "Social": "Baixa aceitação local."}
data_eco = {"CAPEX": "Investimento altíssimo.", "OPEX": "Custo operacional alto.", "LCOE": "Energia cara."}
data_amb = {"CO2": "Emissões de GEE altas.", "NOx": "Alta poluição local.", "Ruído": "Nível de ruído inaceitável.", "Clima": "Sem metas sustentáveis."}
data_tec = {"Confiabilidade": "Falhas frequentes.", "Maturidade": "Tecnologia experimental."}
data_est = {"Alinhamento": "Desalinhado com a visão da Itaipu.", "Liderança": "Sem promoção de inovação.", "PeD": "Sem fomento à cadeia de H2."}
data_soc = {"Aceitação": "Rejeição da comunidade.", "Legitimidade": "Sem apoio de parceiros.", "Reputação": "Dano à imagem institucional."}


# ==============================================================================
# --- CABEÇALHO GLOBAL: LOGOS AJUSTADOS (FIXOS NO TOPO) ---
# ==============================================================================

# Definição dos nomes dos arquivos (Melhor prática: evitar espaços e maiúsculas)
# USUÁRIO DEVE RENOMEAR OS ARQUIVOS JPEG NO GITHUB PARA ESTES NOMES ABAIXO:
LOGO_BINACIONAL = "itaipu_binacional.jpeg"

# Criação de colunas com proporção para dar mais espaço ao Parquetec (que é mais alto/largo)
# logocol1 é 40% da largura, logocol2 é 60% da largura. Isso centraliza o conjunto.
logocol1, logocol2 = st.columns([4, 6])

# Coluna 1: Itaipu Binacional (na frente/esquerda)
with logocol1:
    if os.path.exists(LOGO_BINACIONAL):
        # use_column_width=True faz o logo Binacional preencher toda a sua coluna,
        # ficando o maior possível e preenchendo o espaço de forma centralizada.
        st.image(LOGO_BINACIONAL, use_column_width=True)
    else:
        st.warning(f"⚠️ Arquivo '{LOGO_BINACIONAL}' não encontrado no GitHub.")


# Linha divisória fina abaixo dos logos
st.divider()

# ==============================================================================
# ==============================================================================


# --- LÓGICA DE NAVEGAÇÃO DE PÁGINAS ---

# PASSO 0: INÍCIO E NOME
if st.session_state.passo == 0:
    st.title("Avaliação Multicritério da Viabilidade Econômica do Data Center com Uso de Hidrogênio")
    st.markdown("Bem-vindo ao sistema de levantamento de pesos para o Data Center da Itaipu e Parquetec. Utilizaremos o **Método SWING** para entender as suas prioridades.")
    
    nome = st.text_input("Por favor, insira seu nome ou cargo para iniciarmos:", value=st.session_state.nome).strip()
    
    if st.button("Iniciar Questionário", type="primary"):
        if nome:
            st.session_state.nome = nome
            st.session_state.passo = 1
            st.rerun()
        else:
            st.error("⚠️ O preenchimento da identificação é obrigatório.")

# PASSO 1: DIMENSÕES PRINCIPAIS
elif st.session_state.passo == 1:
    st.video("https://youtu.be/9xgrM1Unbmk") # Vídeo 1
    txt_exp = "Nesta etapa, não pense nos detalhes técnicos ainda. Queremos saber a sua visão macro do projeto: qual a importância relativa entre as 5 grandes áreas (Dimensões) da avaliação?"
    scores = swing_method_component("Etapa 1 de 6: Dimensões Principais", data_dim, "dim", txt_exp)
    
    st.divider()
    if st.button("Avançar para Dimensão Econômica ➡️", type="primary"):
        st.session_state.respostas["Dimensões"] = scores
        st.session_state.passo = 2
        st.rerun()

# PASSO 2: ECONÔMICA
elif st.session_state.passo == 2:
    st.video("https://youtu.be/T21b2c8yjm4") # Vídeo 2
    txt_exp = "Avalie a importância entre os diferentes tipos de custos envolvidos na implementação da nova tecnologia de hidrogênio."
    scores = swing_method_component("Etapa 2 de 6: Dimensão Econômica", data_eco, "eco", txt_exp)
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar"): st.session_state.passo = 1; st.rerun()
    with col2:
        if st.button("Avançar para Ambiental ➡️", type="primary"):
            st.session_state.respostas["Econômica"] = scores
            st.session_state.passo = 3
            st.rerun()

# PASSO 3: AMBIENTAL
elif st.session_state.passo == 3:
    st.video("https://youtu.be/ZFjj2DgvHYI") # Vídeo 3
    txt_exp = "Foco no Meio Ambiente. Avalie quais impactos ambientais devem ter mais peso na decisão de substituir os geradores a diesel."
    scores = swing_method_component("Etapa 3 de 6: Dimensão Ambiental", data_amb, "amb", txt_exp)
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar"): st.session_state.passo = 2; st.rerun()
    with col2:
        if st.button("Avançar para Técnica ➡️", type="primary"):
            st.session_state.respostas["Ambiental"] = scores
            st.session_state.passo = 4
            st.rerun()

# PASSO 4: TÉCNICA
elif st.session_state.passo == 4:
    st.video("https://youtu.be/gNoDM3wVYwM") # Vídeo 4
    txt_exp = "Olhando para a Engenharia. O que é mais crítico para o Data Center: a maturidade da tecnologia escolhida ou a sua confiabilidade operacional?"
    scores = swing_method_component("Etapa 4 de 6: Dimensão Técnica", data_tec, "tec", txt_exp)
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar"): st.session_state.passo = 3; st.rerun()
    with col2:
        if st.button("Avançar para Estratégica ➡️", type="primary"):
            st.session_state.respostas["Técnica"] = scores
            st.session_state.passo = 5
            st.rerun()

# PASSO 5: ESTRATÉGICA
elif st.session_state.passo == 5:
    st.video("https://youtu.be/FpnmfL2XqEo") # Vídeo 5
    txt_exp = "Pensando no longo prazo. Como essa escolha tecnológica se alinha com as diretrizes de inovação e liderança?"
    scores = swing_method_component("Etapa 5 de 6: Dimensão Estratégica", data_est, "est", txt_exp)
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar"): st.session_state.passo = 4; st.rerun()
    with col2:
        if st.button("Avançar para Social ➡️", type="primary"):
            st.session_state.respostas["Estratégica"] = scores
            st.session_state.passo = 6
            st.rerun()

# PASSO 6: SOCIAL
elif st.session_state.passo == 6:
    st.video("https://youtu.be/8XzA2ZWt0Ck") # Vídeo 6 (O mais recente!)
    txt_exp = "Impacto Social e Reputação. Avalie os aspectos de aceitação da comunidade e legitimidade perante a sociedade."
    scores = swing_method_component("Etapa 6 de 6: Dimensão Social", data_soc, "soc", txt_exp)
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar"): st.session_state.passo = 5; st.rerun()
    with col2:
        if st.button("Revisar e Finalizar ➡️", type="primary"):
            st.session_state.respostas["Social"] = scores
            st.session_state.passo = 7
            st.rerun()

# PASSO 7: TELA FINAL (ENVIO)
elif st.session_state.passo == 7:
    st.header("Tudo Pronto, " + st.session_state.nome + "!")
    st.success("Você concluiu todas as etapas de avaliação. Muito obrigado pelo seu tempo e dedicação.")
    st.write("Clique no botão abaixo para registrar oficialmente suas escolhas na base de dados da pesquisa.")
    
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Voltar e revisar respostas"): st.session_state.passo = 6; st.rerun()
    with col2:
        if st.button("📤 Enviar Respostas Definitivas", type="primary"):
            with st.spinner("Conectando ao banco de dados..."):
                if save_to_sheets(st.session_state.respostas, st.session_state.nome):
                    st.balloons()
                    st.success("✅ Suas respostas foram salvas com sucesso! Você já pode fechar esta página.")
                    st.session_state.passo = 8 
                    st.rerun()

# PASSO 8: TELA DE SUCESSO (PÓS ENVIO)
elif st.session_state.passo == 8:
    st.title("Questionário Finalizado")
    st.info("Suas respostas já foram recebidas no servidor. Muito obrigado pela sua contribuição com o projeto de transição energética!")
