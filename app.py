import streamlit as st
from transformers import pipeline
import re
import requests
from bs4 import BeautifulSoup

# ---------- CONFIGURAÇÕES ----------

st.markdown("<h1 style='text-align:center;'>🤖 IA Antifraude Bot</h1>", unsafe_allow_html=True)

# ---------- ESTILO VISUAL ----------
st.markdown("""
<style>
.alert-header{
  padding:12px 14px;border-radius:10px;color:#fff;font-weight:700;
  text-align:center;margin:4px 0 12px 0; font-size:18px
}
.alerts{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.alert-item{background:#111418;border:1px solid #2a2f36;border-radius:10px;padding:10px 12px;display:flex;gap:10px;align-items:flex-start}
.alert-emoji{font-size:18px;line-height:1.1}
.alert-text{font-size:15px}
.pill{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:700;font-size:12px;color:#fff;margin-bottom:6px}
.pill.red{background:#e03131}
.pill.orange{background:#f08c00}
.pill.green{background:#2f9e44}
.risk-box{background:#0f1320;border:1px solid #2a2f36;border-radius:10px;padding:10px;margin-bottom:8px}
.risk-label{display:flex;justify-content:space-between;font-size:12px;color:#9aa4b2;margin-bottom:6px}
.risk-bar{height:8px;background:#1e2430;border-radius:999px;overflow:hidden}
.risk-bar>div{height:100%}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("👩‍💻 Matheus Henrique")
st.sidebar.markdown("💼 [LinkedIn](https://www.linkedin.com/in/matheus4807/)")
st.sidebar.markdown("🐙 [GitHub](https://github.com/Matheusdisk)")
st.sidebar.markdown("✉️ matheuscruzhenrique@hotmail.com")
st.sidebar.markdown("---")
st.sidebar.info("🚀 Projeto desenvolvido para análise de mensagens suspeitas de fraude usando IA.")


with st.expander("ℹ️ Sobre este projeto"):
    st.write("""
    Este aplicativo utiliza inteligência artificial para detectar possíveis **golpes e fraudes** em mensagens.
    
    🔍 **Como funciona:**  
    O texto é analisado por um modelo BERT treinado em português, que classifica o tom da mensagem e detecta padrões suspeitos (links, promessas de dinheiro, palavras-chave de golpe etc.)

    🧠 **Tecnologias usadas:**  
    - Streamlit (frontend e hospedagem)  
    - Transformers (modelo BERTweet)  
    - BeautifulSoup + Requests (pré-visualização de links)  

    💡 Desenvolvido por **Matheus Henrique** como parte do portfólio de projetos em IA aplicada à segurança digital.
    """)

st.write("Analise mensagens e veja se parecem **golpes, enganos ou mensagens seguras** usando inteligência artificial.")

# ---------- CARREGAR MODELO ----------
@st.cache_resource
def carregar_modelo():
    modelo = pipeline("sentiment-analysis", model="pysentimiento/bertweet-pt-sentiment")
    return modelo

detector = carregar_modelo()

# ---------- FUNÇÃO PARA PEGAR META-DADOS DO LINK ----------
def get_link_preview(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "Sem título"
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag and "content" in img_tag.attrs else None

        return {"title": title, "img": img, "url": url}
    except:
        return {"title": "Link inacessível ou perigoso", "img": None, "url": url}


# ---------- FUNÇÃO DE ANÁLISE ----------
def analisar_mensagem(texto):
    if not texto.strip():
        return "Por favor, digite uma mensagem."

    texto_lower = texto.lower()
    resultado = detector(texto)[0]
    label = resultado["label"].lower()
    score = resultado["score"]

    alerta = []
    risco = 0
    links = re.findall(r"https?://\S+", texto)

    # 1. Palavras suspeitas
    palavras_suspeitas = ["pix", "ganhou", "retirada", "clique", "confirme", "prêmio", "transferido", "saldo"]
    if any(p in texto_lower for p in palavras_suspeitas):
        alerta.append("🚨 Termos muito usados em **golpes** detectados.")
        risco += 2

    # 2. Links
    if links:
        alerta.append("🔗 Mensagem contém **link suspeito**.")
        risco += 3
        if any(encurtador in texto_lower for encurtador in ["bit.ly", "tinyurl", "cut.ly", "is.gd"]):
            alerta.append("⚠️ O link é **encurtado**, comum em tentativas de **phishing**.")
            risco += 3

    # 3. Jogos de azar
    if any(p in texto_lower for p in ["cassino", "aposta", "bet", "jogo"]):
        alerta.append("🎰 Menciona **cassino ou apostas online**, muito usados em **fraudes**.")
        risco += 3

    # 4. Promessa de dinheiro
    if any(p in texto_lower for p in ["r$", "ganhe", "receba", "transferido", "saldo", "verificado"]):
        alerta.append("💸 Promete **dinheiro fácil ou transferência**, típico de **golpe de premiação falsa**.")
        risco += 2

    # ---------- CLASSIFICAÇÃO ----------
    if risco >= 4:
        gravidade = "🚨 **ALERTA MÁXIMO: ALTA PROBABILIDADE DE GOLPE!**"
        cor = "red"
    elif risco >= 2:
        gravidade = "⚠️ **Mensagem suspeita. Tenha cuidado.**"
        cor = "orange"
    else:
        gravidade = "✅ **Parece segura**"
        cor = "green"

    # ---------- SAÍDA ----------
    resultado_final = f"<div style='background-color:{cor};padding:10px;border-radius:8px;color:white;font-size:18px;font-weight:bold;text-align:center;'>{gravidade}</div><br>"
    resultado_final += "<br>".join(alerta) if alerta else f"Confiabilidade: {score:.2f}"

    # ---------- EXIBIR PRÉVIA DE LINK ----------
    if links:
        for link in links:
            preview = get_link_preview(link)

            st.markdown("---")
            st.markdown("### ⚠️ **NÃO CLIQUE NESSE LINK!**")
            st.markdown(f"<div style='background-color:#ff4d4d;padding:15px;border-radius:10px;color:white;'>"
                        f"<b>🚫 ESTE LINK PODE SER PERIGOSO</b><br><br>"
                        f"<b>Endereço:</b> {preview['url']}<br>"
                        f"<b>Título detectado:</b> {preview['title']}<br>", unsafe_allow_html=True)

            if preview['img']:
                st.image(preview['img'], caption="Prévia do site", use_column_width=True)

            st.markdown("<div style='color:white;background:#b30000;padding:8px;border-radius:5px;text-align:center;'>"
                        "🚷 **NÃO PROSSIGA — ESTE LINK PODE ROUBAR SEUS DADOS OU INDUZIR AO ERRO!**</div>",
                        unsafe_allow_html=True)

        # ---------- CLASSIFICAÇÃO ----------
    if risco >= 4:
        gravidade = "🚨 **ALERTA MÁXIMO: ALTA PROBABILIDADE DE GOLPE!**"
        cor = "red"
    elif risco >= 2:
        gravidade = "⚠️ **Mensagem suspeita. Tenha cuidado.**"
        cor = "orange"
    else:
        gravidade = "✅ **Parece segura**"
        cor = "green"

    # ---------- ESTRUTURA E RENDERIZAÇÃO BONITA ----------
    retorno = {
        "gravidade": gravidade,
        "cor": cor,
        "score": score,
        "risco": risco,
        "alertas": alerta,
        "links": links
    }

    # (aqui entra todo o bloco HTML que te mandei)
    # ...
    # ...
    return html_final

# ---------- INTERFACE ----------
texto = st.text_area("Cole aqui a mensagem recebida:", placeholder="Ex: Oi, clique aqui para atualizar seus dados bancários.")

if st.button("Analisar"):
    resposta = analisar_mensagem(texto)
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("---")
st.caption("Feito com 💡 e IA — Projeto de segurança cibernética com Python.")
