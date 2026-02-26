

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Questionário SWING - Itaipu", layout="wide")

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

# --- FUNÇÃO PARA SALVAR NO GOOGLE SHEETS ---
def save_to_sheets(data_dict, nome):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # --- SISTEMA DE SEGURANÇA ---
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open("Respostas_SWING_Itaipu").sheet1

        # PASSO A: Verificação do cabeçalho
        try:
            valor_a1 = sheet.acell('A1').value
        except:
            valor_a1 = None

        if valor_a1 != "Data/Hora":
            sheet.insert_row(COLUNAS, 1)

        # PASSO B: Monta a linha de dados
        row = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nome]
        
        for val in data_dict["Dimensões"].values(): row.append(val)
        for cat in ["Econômica", "Ambiental", "Técnica", "Estratégica", "Social"]:
            for val in data_dict[cat].values(): row.append(val)

        # PASSO C: Salva os dados
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- INTERFACE INICIAL ---
st.title("Questionário de Pesos: Método SWING Hierárquico")
st.markdown("Avaliação de viabilidade: **Geradores a Diesel vs. Hidrogênio** no Data Center da Itaipu.")

# Captura do nome (usa strip() para evitar que a pessoa digite apenas um "espaço")
nome_decisor = st.text_input("Por favor, insira seu nome ou identificação profissional:", placeholder="Ex: Engenheiro João Silva").strip()

if not nome_decisor:
    st.warning("⚠️ O botão de envio no final da página só será liberado após você preencher o seu nome aqui.")

# --- FUNÇÃO DO COMPONENTE SWING ---
def swing_method_component(section_title, items_data, key_suffix):
    st.header(section_title)
    st.info(f"🛑 **PASSO 1:** Imagine que todos os itens abaixo estão no **PIOR NÍVEL**.")
    for item, description in items_data.items():
        st.markdown(f"- **{item}:** {description}")

    st.divider()
    selected_best = st.radio(f"🏆 **PASSO 2:** Qual melhoraria primeiro?", list(items_data.keys()), key=f"radio_{key_suffix}")
    st.success(f"**{selected_best}** recebeu 100 pontos.")

    st.divider()
    st.write(f"⚖️ **PASSO 3:** Pontue os outros em relação a {selected_best} (0-100).")

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
data_dim = {"Econômica": "Custos máximos.", "Ambiental": "Impacto máximo.", "Técnica": "Baixa confiabilidade.", "Estratégica": "Sem alinhamento.", "Social": "Baixa aceitação."}
data_eco = {"CAPEX": "Investimento altíssimo.", "OPEX": "Custo operacional alto.", "LCOE": "Energia cara."}
data_amb = {"CO2": "GEE alto.", "NOx": "Poluição local.", "Ruído": "Barulho alto.", "Clima": "Sem metas."}
data_tec = {"Confiabilidade": "Falhas frequentes.", "Maturidade": "Tecnologia experimental."}
data_est = {"Alinhamento": "Desalinhado com Itaipu.", "Liderança": "Sem inovação.", "PeD": "Sem fomento H2."}
data_soc = {"Aceitação": "Rejeição local.", "Legitimidade": "Sem apoio parceiros.", "Reputação": "Dano à imagem."}

# --- ABAS E COLETA DE RESULTADOS ---
tabs = st.tabs(["1. Dimensões", "2. Econômica", "3. Ambiental", "4. Técnica", "5. Estratégica", "6. Social"])
results = {}

with tabs[0]: results["Dimensões"] = swing_method_component("Nível 1", data_dim, "dim")
with tabs[1]: results["Econômica"] = swing_method_component("Nível 2: Econômica", data_eco, "eco")
with tabs[2]: results["Ambiental"] = swing_method_component("Nível 2: Ambiental", data_amb, "amb")
with tabs[3]: results["Técnica"] = swing_method_component("Nível 2: Técnica", data_tec, "tec")
with tabs[4]: results["Estratégica"] = swing_method_component("Nível 2: Estratégica", data_est, "est")
with tabs[5]: results["Social"] = swing_method_component("Nível 2: Social", data_soc, "soc")

# --- BOTÃO DE ENVIO COM TRAVA ---
st.divider()

# A variável 'liberar_botao' será Verdadeira se o nome tiver pelo menos 1 letra
liberar_botao = len(nome_decisor) > 0

if st.button("Finalizar e Enviar Respostas", disabled=not liberar_botao):
    with st.spinner("Salvando na planilha oficial..."):
        if save_to_sheets(results, nome_decisor):
            st.balloons()
            st.success(f"Excelente, {nome_decisor}! Seus dados foram salvos com sucesso.")

