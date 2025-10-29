import streamlit as st
from transformers import pipeline
import re
import requests
from bs4 import BeautifulSoup
import base64, pathlib
import unicodedata
from html import unescape
from urllib.parse import urlparse
import ipaddress, socket


# ======= CABEÇALHO ALINHADO LADO A LADO =======
def img_b64(path):
    return base64.b64encode(pathlib.Path(path).read_bytes()).decode()

icon_b64 = img_b64("17604803.png")  # ajuste o caminho se estiver em outra pasta

st.markdown(f"""
<div style="
    display:flex; align-items:center; justify-content:center; gap:16px;
    margin-top:10px; margin-bottom:6px;
">
    <img src="data:image/png;base64,{icon_b64}" width="70" style="margin-top:-4px;">
    <h1 style="color:white; font-size:38px; font-weight:800; margin:0;">
        IA Antifraude Bot
    </h1>
</div>
<p style='text-align:center; color:#9aa4b2; font-size:16px; margin-top:-4px;'>
Analise mensagens e identifique possíveis golpes com inteligência artificial.
</p>
""", unsafe_allow_html=True)


# ---------- ESTILO VISUAL ----------
st.markdown("""
<style>
/* ====== LAYOUT GERAL ====== */
.alert-header{
  padding:18px 20px;
  border-radius:10px;
  color:#fff;
  font-weight:800;
  text-align:center;
  margin:28px 0 24px 0;
  font-size:20px;
  letter-spacing:0.4px;
  box-shadow:0 3px 6px rgba(0,0,0,0.25);
}

.alerts{
  list-style:none;
  margin:0;
  padding:0;
  display:flex;
  flex-direction:column;
  gap:16px; /* espaço entre os cards de alerta */
}

.alert-item{
  background:#151922;
  border:1px solid #2b3038;
  border-radius:12px;
  padding:16px 18px;
  display:flex;
  gap:14px;
  align-items:flex-start;
  transition:all 0.25s ease-in-out;
}
.alert-item:hover{
  background:#1c212c;
  border-color:#3b414b;
}

.alert-emoji{
  font-size:22px;
  line-height:1.1;
  flex-shrink:0;
}

.alert-text{
  font-size:16px;
  line-height:1.5;
  color:#e1e5eb;
}

/* ====== PÍLULAS (STATUS) ====== */
.pill{
  display:inline-block;
  padding:8px 18px;
  border-radius:999px;
  font-weight:700;
  font-size:13px;
  color:#fff;
  margin:10px 0 18px 0;
  text-transform:uppercase;
  letter-spacing:0.5px;
}
.pill.red{background:#e03131}
.pill.orange{background:#f59f00}
.pill.green{background:#2f9e44}

/* ====== BARRA DE RISCO ====== */
.risk-box{
  background:#10131a;
  border:1px solid #2b3038;
  border-radius:12px;
  padding:16px 18px;
  margin:20px 0 28px 0;
  box-shadow:inset 0 0 8px rgba(0,0,0,0.4);
}
.risk-label{
  display:flex;
  justify-content:space-between;
  font-size:13px;
  color:#b2b8c3;
  margin-bottom:10px;
  font-weight:600;
  text-transform:uppercase;
  letter-spacing:0.3px;
}
.risk-bar{
  height:12px;
  background:#1e2430;
  border-radius:999px;
  overflow:hidden;
}
.risk-bar>div{
  height:100%;
  transition:width 0.5s ease;
}

/* ====== SEÇÃO DE LINK ====== */
.stMarkdown h3{
  margin-top:36px;
}

div[data-testid="stMarkdownContainer"] hr{
  margin:34px 0 26px 0;
  border-color:#333a44;
}
</style>
""", unsafe_allow_html=True)


st.sidebar.title("👩‍💻 Matheus Henrique")
st.sidebar.markdown("💼 [LinkedIn](https://www.linkedin.com/in/matheus4807/)")
st.sidebar.markdown("🐙 [GitHub](https://github.com/Matheusdisk)")
st.sidebar.markdown("✉️ matheuscruzhenrique@hotmail.com")
st.sidebar.markdown("---")
st.sidebar.info("🚀 Projeto desenvolvido para análise de mensagens suspeitas de fraude usando IA.")

st.write("")

# ---------- CARREGAR MODELO ----------
@st.cache_resource
def carregar_modelo():
    modelo = pipeline("sentiment-analysis", model="pysentimiento/bertweet-pt-sentiment")
    return modelo

detector = carregar_modelo()

# ---------- FUNÇÃO PARA PEGAR META-DADOS DO LINK ----------
import unicodedata
from html import unescape
from urllib.parse import urlparse
import ipaddress, socket

def _is_private_ip(host):
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except:
        return True

def _clean_text(s: str) -> str:
    if not s:
        return "Sem título"
    s = unescape(s)
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if ch.isprintable())
    s = " ".join(s.split())                    # colapsa espaços
    return s[:160]                             # limita tamanho

def get_link_preview(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Protocolo não permitido.")
        if _is_private_ip(parsed.hostname):
            raise ValueError("Host não permitido.")

        headers = {"User-Agent": "Mozilla/5.0"}
        # baixa só até 500KB para não travar
        r = requests.get(url, headers=headers, timeout=6, allow_redirects=True, stream=True)
        r.raise_for_status()
        raw = r.raw.read(500_000, decode_content=True)

        # detecta encoding (requests tenta charset-normalizer)
        encoding = r.encoding or "utf-8"
        try:
            html = raw.decode(encoding, errors="ignore")
        except:
            html = raw.decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")

        # título: og:title > meta name=title > <title>
        title = None
        ogt = soup.find("meta", property="og:title")
        if ogt and ogt.get("content"):
            title = ogt["content"]
        if not title:
            mt = soup.find("meta", attrs={"name": "title"})
            if mt and mt.get("content"):
                title = mt["content"]
        if not title:
            title = soup.title.string if soup.title and soup.title.string else "Sem título"

        img = None
        ogimg = soup.find("meta", property="og:image")
        if ogimg and ogimg.get("content"):
            img = ogimg["content"]

        return {"title": _clean_text(title), "img": img, "url": r.url}
    except Exception:
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

    # ---------- CLASSIFICAÇÃO (UMA VEZ SÓ) ----------
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

    # Cabeçalho
    header_html = f"<div class='alert-header' style='background:{cor};'>{retorno['gravidade']}</div>"

    # Barra de risco
    risco_max = 10
    fill = min(retorno["risco"]/risco_max, 1.0)
    fill_color = {"red":"#e03131", "orange":"#f08c00", "green":"#2f9e44"}[cor]
    risk_html = f"""
    <div class='risk-box'>
      <div class='risk-label'><span>Nível de risco</span><span>{retorno['risco']}/{risco_max}</span></div>
      <div class='risk-bar'><div style='width:{fill*100:.0f}%; background:{fill_color};'></div></div>
    </div>
    """

    # Chip
    chip = f"<span class='pill {'red' if cor=='red' else 'orange' if cor=='orange' else 'green'}'>{gravidade.split(':')[0].replace('**','')}</span>"

    # Lista de alertas
    itens = ""
    for a in retorno["alertas"]:
        em = a.strip().split(" ")[0]
        resto = a[len(em):].strip() if em and len(em) <= 3 else a
        emoji_html = f"<div class='alert-emoji'>{em}</div>" if len(em) <= 3 else "<div class='alert-emoji'>•</div>"
        texto_html = f"<div class='alert-text'>{resto}</div>"
        itens += f"<li class='alert-item'>{emoji_html}{texto_html}</li>"

    lista_html = (
        f"<ul class='alerts'>{itens}</ul>"
        if itens
        else f"<div class='alert-item'><div class='alert-emoji'>✅</div><div class='alert-text'>Confiabilidade do modelo: <b>{score:.2f}</b></div></div>"
    )

    # 👉 removido o chip — agora mostramos apenas cabeçalho + barra de risco + lista
    html_final = header_html + risk_html + lista_html

    # ---------- EXIBIR PRÉVIA DE LINK ----------
    if links:
        for link in links:
            preview = get_link_preview(link)
            st.markdown("---")
            st.markdown("### ⚠️ **NÃO CLIQUE NESSE LINK!**")
            st.markdown(
                f"<div style='background-color:#ff4d4d;padding:15px;border-radius:10px;color:white;'>"
                f"<b>🚫 ESTE LINK PODE SER PERIGOSO</b><br><br>"
                f"<b>Endereço:</b> {preview['url']}<br>"
                f"<b>Título detectado:</b> {preview['title']}<br></div>",
                unsafe_allow_html=True
            )
            if preview["img"]:
                st.image(preview["img"], caption="Prévia do site", use_column_width=True)
            st.markdown(
                "<div style='color:white;background:#b30000;padding:8px;border-radius:5px;text-align:center;'>"
                "🚷 <b>NÃO PROSSIGA — ESTE LINK PODE ROUBAR SEUS DADOS OU INDUZIR AO ERRO!</b></div>",
                unsafe_allow_html=True
            )

    return html_final


# ---------- INTERFACE ----------
texto = st.text_area("Cole aqui a mensagem recebida:", placeholder="Ex: Oi, clique aqui para atualizar seus dados bancários.")

if st.button("Analisar"):
    resposta = analisar_mensagem(texto)
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)



st.markdown("---")
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
st.caption("Feito com IA — Projeto de segurança cibernética com Python.")
