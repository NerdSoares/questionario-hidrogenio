import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Questionário Completo - Itaipu", layout="centered")

# --- LISTA DEFINITIVA DE COLUNAS ATUALIZADA (CABEÇALHO) ---
COLUNAS = [
    "Data/Hora", "Nome do Decisor",
    # Pesos (SWING)
    "Dim_Econômica", "Dim_Ambiental", "Dim_Técnica", "Dim_Estratégica", "Dim_Social",
    "Eco_CAPEX", "Eco_OPEX", "Eco_LCOE",
    "Amb_CO2", "Amb_NOx", "Amb_Ruído", "Amb_Clima",
    "Tec_Confiabilidade", "Tec_Maturidade",
    "Est_Alinhamento", "Est_Liderança", "Est_PeD",
    "Soc_Aceitação", "Soc_Legitimidade", "Soc_Reputação",
    # Desempenhos (0-10) - Diesel vs Hidrogênio
    "Perf_Clima_Diesel", "Perf_Clima_H2",
    "Perf_Inst_Diesel", "Perf_Inst_H2",
    "Perf_Lider_Diesel", "Perf_Lider_H2",
    "Perf_PD_Diesel", "Perf_PD_H2",
    "Perf_Soc_Diesel", "Perf_Soc_H2",
    "Perf_Legit_Diesel", "Perf_Legit_H2",
    "Perf_Reput_Diesel", "Perf_Reput_H2"
]

# --- INICIALIZAÇÃO DA MEMÓRIA (SESSION STATE) ---
if 'passo' not in st.session_state: st.session_state.passo = 0
if 'respostas' not in st.session_state: st.session_state.respostas = {"Pesos": {}, "Desempenhos": {}}
if 'nome' not in st.session_state: st.session_state.nome = ""

# --- FUNÇÃO PARA SALVAR NO GOOGLE SHEETS ---
def save_to_sheets(respostas, nome):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

        client = gspread.authorize(creds)
        sheet = client.open("Respostas_SWING_Itaipu").sheet1

        try:
            if sheet.acell('A1').value != "Data/Hora": sheet.insert_row(COLUNAS, 1)
        except:
            sheet.insert_row(COLUNAS, 1)

        row = [datetime.now().strftime("%d/%m/%Y %H:%M:%S"), nome]
        
        # Puxa os Pesos na ordem correta
        p = respostas["Pesos"]
        for val in p["Dimensões"].values(): row.append(val)
        for cat in ["Econômica", "Ambiental", "Técnica", "Estratégica", "Social"]:
            for val in p[cat].values(): row.append(val)
        
        # Puxa os Desempenhos na ordem correta
        d = respostas["Desempenhos"]
        ordem_perf = ["Clima", "Inst", "Lider", "PD", "Soc", "Legit", "Reput"]
        for crit in ordem_perf:
            row.append(d[f"{crit}_Diesel"])
            row.append(d[f"{crit}_H2"])

        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- COMPONENTE SWING (PESOS) ---
def swing_method_component(section_title, items_data, key_suffix, texto_explicativo):
    st.header(section_title)
    st.info(f"💡 **Contexto desta etapa:**\n\n{texto_explicativo}")
    st.markdown("🛑 **PASSO 1:** Imagine que todos os critérios abaixo estão no **PIOR NÍVEL POSSÍVEL**.")
    for item, description in items_data.items(): st.markdown(f"- **{item}:** {description}")
    st.divider()
    selected_best = st.radio(f"🏆 **PASSO 2:** Qual critério você melhoraria primeiro?", list(items_data.keys()), key=f"radio_{key_suffix}")
    st.divider()
    st.write(f"⚖️ **PASSO 3:** Agora, pontue os outros critérios em relação a {selected_best} (0-100).")
    scores = {}
    cols = st.columns(2)
    for i, item in enumerate(items_data.keys()):
        col = cols[i % 2]
        with col:
            val = 100 if item == selected_best else 50
            scores[item] = st.slider(f"{item}", 0, 100, val, disabled=(item == selected_best), key=f"s_{item}_{key_suffix}")
    return scores

# --- COMPONENTE DE DESEMPENHO (0-10) ---
def performance_component(title, description, key_prefix):
    st.header(title)
    st.info(f"📊 **Critério:** {description}")
    st.markdown("Dê uma nota de **0 a 10** para cada tecnologia neste critério:")
    st.caption("0 = Péssimo | 5 = Regular | 10 = Excelente")
    
    col1, col2 = st.columns(2)
    with col1:
        nota_diesel = st.select_slider(f"Nota para o DIESEL", options=list(range(11)), value=5, key=f"{key_prefix}_d")
    with col2:
        nota_h2 = st.select_slider(f"Nota para o HIDROGÊNIO", options=list(range(11)), value=5, key=f"{key_prefix}_h2")
    return nota_diesel, nota_h2

# --- DADOS DOS CRITÉRIOS ---
data_dim = {"Econômica": "Custos e tarifas máximas.", "Ambiental": "Alto impacto e emissões.", "Técnica": "Baixa confiabilidade.", "Estratégica": "Sem alinhamento corporativo.", "Social": "Baixa aceitação local."}
data_eco = {"CAPEX": "Investimento altíssimo.", "OPEX": "Custo operacional alto.", "LCOE": "Energia cara."}
data_amb = {"CO2": "Emissões de GEE altas.", "NOx": "Alta poluição local.", "Ruído": "Nível de ruído inaceitável.", "Clima": "Sem metas sustentáveis."}
data_tec = {"Confiabilidade": "Falhas frequentes.", "Maturidade": "Tecnologia experimental."}
data_est = {"Alinhamento": "Desalinhado com a visão da Itaipu.", "Liderança": "Sem promoção de inovação.", "PeD": "Sem fomento à cadeia de H2."}
data_soc = {"Aceitação": "Rejeição da comunidade.", "Legitimidade": "Sem apoio de parceiros.", "Reputação": "Dano à imagem institucional."}

# --- CABEÇALHO GLOBAL: LOGOS ---
LOGO_BINACIONAL = "itaipu_binacional.jpg"
LOGO_PARQUETEC = "itaipu_parquetec.jpg"
logocol1, logocol2 = st.columns([4, 6])
with logocol1: 
    if os.path.exists(LOGO_BINACIONAL): st.image(LOGO_BINACIONAL, use_column_width=True)
with logocol2:
    if os.path.exists(LOGO_PARQUETEC): st.image(LOGO_PARQUETEC, use_column_width=True)
st.divider()

# --- LÓGICA DE NAVEGAÇÃO ---

# PASSO 0: INÍCIO
if st.session_state.passo == 0:
    st.title("Avaliação Diesel vs. Hidrogênio")
    st.markdown("Bem-vindo! Esta pesquisa está dividida em duas partes: **Pesos (Prioridades)** e **Desempenhos (Notas)**.")
    nome = st.text_input("Seu nome ou cargo:", value=st.session_state.nome).strip()
    if st.button("Iniciar Questionário", type="primary"):
        if nome: st.session_state.nome = nome; st.session_state.passo = 1; st.rerun()
        else: st.error("⚠️ Identificação obrigatória.")

# PASSOS 1-6: SWING WEIGHTING (PESOS)
elif 1 <= st.session_state.passo <= 6:
    vids = ["9xgrM1Unbmk", "T21b2c8yjm4", "ZFjj2DgvHYI", "gNoDM3wVYwM", "FpnmfL2XqEo", "8XzA2ZWt0Ck"]
    st.video(f"https://youtu.be/{vids[st.session_state.passo-1]}")
    
    if st.session_state.passo == 1:
        res = swing_method_component("Etapa 1: Dimensões", data_dim, "dim", "Qual a importância relativa entre as 5 grandes áreas?")
        if st.button("Avançar ➡️"): st.session_state.respostas["Pesos"]["Dimensões"] = res; st.session_state.passo = 2; st.rerun()
    elif st.session_state.passo == 2:
        res = swing_method_component("Etapa 2: Econômica", data_eco, "eco", "Avalie a importância entre os custos envolvidos.")
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("⬅️ Voltar"): st.session_state.passo = 1; st.rerun()
        with col2: 
            if st.button("Avançar ➡️"): st.session_state.respostas["Pesos"]["Econômica"] = res; st.session_state.passo = 3; st.rerun()
    # ... Repetir lógica para passos 3, 4, 5 e 6 mantendo a estrutura original ...
    elif st.session_state.passo == 3:
        res = swing_method_component("Etapa 3: Ambiental", data_amb, "amb", "Quais impactos ambientais pesam mais na sua decisão?")
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("⬅️ Voltar"): st.session_state.passo = 2; st.rerun()
        with col2: 
            if st.button("Avançar ➡️"): st.session_state.respostas["Pesos"]["Ambiental"] = res; st.session_state.passo = 4; st.rerun()
    elif st.session_state.passo == 4:
        res = swing_method_component("Etapa 4: Técnica", data_tec, "tec", "O que é mais crítico: maturidade ou confiabilidade?")
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("⬅️ Voltar"): st.session_state.passo = 3; st.rerun()
        with col2: 
            if st.button("Avançar ➡️"): st.session_state.respostas["Pesos"]["Técnica"] = res; st.session_state.passo = 5; st.rerun()
    elif st.session_state.passo == 5:
        res = swing_method_component("Etapa 5: Estratégica", data_est, "est", "Alinhamento, liderança ou P&D?")
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("⬅️ Voltar"): st.session_state.passo = 4; st.rerun()
        with col2: 
            if st.button("Avançar ➡️"): st.session_state.respostas["Pesos"]["Estratégica"] = res; st.session_state.passo = 6; st.rerun()
    elif st.session_state.passo == 6:
        res = swing_method_component("Etapa 6: Social", data_soc, "soc", "Aceitação, legitimidade ou reputação?")
        col1, col2 = st.columns(2)
        with col1: 
            if st.button("⬅️ Voltar"): st.session_state.passo = 5; st.rerun()
        with col2: 
            if st.button("Ir para Notas de Desempenho ➡️"): st.session_state.respostas["Pesos"]["Social"] = res; st.session_state.passo = 7; st.rerun()

# PASSOS 7-13: DESEMPENHOS (NOTAS 0-10)
elif 7 <= st.session_state.passo <= 13:
    perfs = [
        ("Alinhamento Climático", "Contribuição para descarbonização institucional e global.", "Clima"),
        ("Alinhamento Institucional", "Aderência aos valores e missão da Itaipu Binacional.", "Inst"),
        ("Liderança Tecnológica", "Potencial para posicionar a Itaipu como referência em inovação.", "Lider"),
        ("P&D em Hidrogênio", "Contribuição para o desenvolvimento do conhecimento e mercado.", "PD"),
        ("Aceitação Social", "Como a comunidade percebe e aceita cada tecnologia.", "Soc"),
        ("Legitimidade", "Validação por parceiros, governo e critérios ESG.", "Legit"),
        ("Reputação", "Impacto geral na imagem institucional da Itaipu.", "Reput")
    ]
    curr = perfs[st.session_state.passo - 7]
    d_val, h2_val = performance_component(f"Desempenho: {curr[0]}", curr[1], curr[2])
    
    col1, col2 = st.columns(2)
    with col1: 
        if st.button("⬅️ Voltar"): st.session_state.passo -= 1; st.rerun()
    with col2:
        btn_txt = "Revisar e Enviar ➡️" if st.session_state.passo == 13 else "Próximo Critério ➡️"
        if st.button(btn_txt):
            st.session_state.respostas["Desempenhos"][f"{curr[2]}_Diesel"] = d_val
            st.session_state.respostas["Desempenhos"][f"{curr[2]}_H2"] = h2_val
            st.session_state.passo += 1; st.rerun()

# PASSO 14: FINALIZAÇÃO
elif st.session_state.passo == 14:
    st.header("Tudo Pronto!")
    st.success("Você concluiu os Pesos e os Desempenhos qualitativos.")
    if st.button("📤 Enviar Respostas Definitivas", type="primary"):
        if save_to_sheets(st.session_state.respostas, st.session_state.nome):
            st.balloons(); st.session_state.passo = 15; st.rerun()

elif st.session_state.passo == 15:
    st.title("Obrigado!")
    st.info("Suas respostas foram registradas com sucesso.")
