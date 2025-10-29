import streamlit as st
from transformers import pipeline
import re, requests, base64, pathlib, unicodedata, ipaddress, socket
from bs4 import BeautifulSoup
from html import unescape
from urllib.parse import urlparse

# ---------- CONFIGURAÇÕES INICIAIS ----------
st.set_page_config(page_title="IA Antifraude Bot", page_icon="17604803.png", layout="centered")

# ---------- IMAGEM DO CABEÇALHO ----------
def img_b64(path):
    return base64.b64encode(pathlib.Path(path).read_bytes()).decode()

icon_b64 = img_b64("17604803.png")

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:center; gap:16px; margin-top:10px; margin-bottom:6px;">
    <img src="data:image/png;base64,{icon_b64}" width="70" style="margin-top:-4px;">
    <h1 style="color:white; font-size:38px; font-weight:800; margin:0;">IA Antifraude Bot</h1>
</div>
<p style='text-align:center; color:#9aa4b2; font-size:16px; margin-top:-4px;'>
Analise mensagens e identifique possíveis golpes com inteligência artificial.
</p>
""", unsafe_allow_html=True)

# ---------- ESTILO VISUAL ----------
st.markdown("""
<style>
.alert-header{
  padding:18px 20px;border-radius:10px;color:#fff;font-weight:800;
  text-align:center;margin:28px 0 24px 0;font-size:20px;
  box-shadow:0 3px 6px rgba(0,0,0,0.25);
}
.alerts{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:16px;}
.alert-item{background:#151922;border:1px solid #2b3038;border-radius:12px;
  padding:16px 18px;display:flex;gap:14px;align-items:flex-start;transition:0.25s;}
.alert-item:hover{background:#1c212c;border-color:#3b414b;}
.alert-emoji{font-size:22px;line-height:1.1;flex-shrink:0;}
.alert-text{font-size:16px;line-height:1.5;color:#e1e5eb;}
.risk-box{background:#10131a;border:1px solid #2b3038;border-radius:12px;
  padding:16px 18px;margin:20px 0 28px 0;box-shadow:inset 0 0 8px rgba(0,0,0,0.4);}
.risk-label{display:flex;justify-content:space-between;font-size:13px;color:#b2b8c3;
  margin-bottom:10px;font-weight:600;text-transform:uppercase;}
.risk-bar{height:12px;background:#1e2430;border-radius:999px;overflow:hidden;}
.risk-bar>div{height:100%;transition:width 0.5s ease;}
.stMarkdown h3{margin-top:36px;}
div[data-testid="stMarkdownContainer"] hr{margin:34px 0 26px 0;border-color:#333a44;}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.title("👨‍💻 Matheus Henrique")
st.sidebar.markdown("💼 [LinkedIn](https://www.linkedin.com/in/matheus4807/)")
st.sidebar.markdown("🐙 [GitHub](https://github.com/Matheusdisk)")
st.sidebar.markdown("✉️ matheuscruzhenrique@hotmail.com")
st.sidebar.markdown("---")
st.sidebar.info("🚀 Projeto desenvolvido para análise de mensagens suspeitas de fraude usando IA.")

# ---------- CARREGAR MODELO ----------
@st.cache_resource
def carregar_modelo():
    return pipeline("sentiment-analysis", model="pysentimiento/bertweet-pt-sentiment")

detector = carregar_modelo()

# ---------- FUNÇÕES DE SUPORTE ----------
def _is_private_ip(host):
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except:
        return True

def _clean_text(s: str) -> str:
    if not s: return "Sem título"
    s = unescape(s)
    s = unicodedata.normalize("NFKC", s)
    s = "".join(ch for ch in s if ch.isprintable())
    return " ".join(s.split())[:160]

def get_link_preview(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http","https") or _is_private_ip(parsed.hostname):
            raise ValueError("Protocolo/host inválido.")
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=6, allow_redirects=True, stream=True)
        r.raise_for_status()
        raw = r.raw.read(500_000, decode_content=True)
        encoding = r.encoding or "utf-8"
        html = raw.decode(encoding, errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name":"title"})
        title = title.get("content") if title and title.get("content") else (
            soup.title.string if soup.title else "Sem título"
        )
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag and "content" in img_tag.attrs else None
        return {"title": _clean_text(title), "img": img, "url": r.url}
    except Exception:
        return {"title": "Link inacessível ou perigoso", "img": None, "url": url}

# --- Detectores de marketing/promoção ---
def _pct_or_money(text):
    # % de desconto ou preço em R$
    return (
        re.search(r"\b\d{1,3}\s?%\b", text) is not None or
        re.search(r"\bR\$\s?\d{1,3}([.,]\d{2})?\b", text) is not None
    )

def detectar_marketing(texto_lower: str):
    """
    Retorna (score_marketing:int, motivos:list[str]).
    Quanto maior o score, mais “cara” de anúncio legítimo.
    """
    motivos, score = [], 0

    gatilhos = [
        "cupom","código","desconto","frete grátis","promo","promoção","oferta",
        "aproveite","imperdível","lançamento","leve","ganhe","corre",
        "só hoje","somente hoje","últimas unidades","estoque limitado",
        "válido até","apenas","por tempo limitado","garanta","aproveite agora"
    ]
    if any(g in texto_lower for g in gatilhos):
        motivos.append("🛍️ Linguagem comercial/promocional detectada.")
        score += 2

    if _pct_or_money(texto_lower):
        motivos.append("💸 Menções a % de desconto ou preço em R$.")
        score += 2

    # Limite por CPF é comum em ofertas
    if re.search(r"\bcpf\b", texto_lower):
        motivos.append("🧾 Menção a CPF (limite por CPF é típico de oferta).")
        score += 1

    # Urgência (muitas maiúsculas)
    palavras_caps = re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{4,}\b", texto_lower, flags=re.I)
    if len(palavras_caps) >= 2:
        motivos.append("⏰ Urgência/ênfase (MUITAS MAIÚSCULAS).")
        score += 1

    # Várias exclamações
    if "!!" in texto_lower or texto_lower.count("!") >= 2:
        motivos.append("‼️ Ênfase com várias exclamações.")
        score += 1

    return score, motivos

import re

def _is_gambling(texto_lower: str) -> bool:
    """
    Detecta 'cassino'/'apostas'/'bet' com segurança.
    Usa bordas de palavra para evitar falsos positivos como 'Betta'.
    """
    padrao = r"\b(cassino|aposta|apostas|bet|bet365|pixbet)\b"
    return re.search(padrao, texto_lower, flags=re.IGNORECASE) is not None



# ---------- FUNÇÃO DE ANÁLISE ----------
def analisar_mensagem(texto):
    if not texto.strip():
        return "Por favor, digite uma mensagem."

    texto_lower = texto.lower()
    resultado = detector(texto)[0]
    score_modelo = resultado["score"]

    alerta = []
    # Vamos separar risco em duas camadas:
    phishing = 0   # sinais fortes de golpe (link encurtado + pedido de ação/senha/dado)
    risco_suave = 0  # sinais fracos/ambíguos (ter link, palavras soltas etc.)
    links = re.findall(r"https?://\S+", texto)

    # ---------------- Heurísticas de golpe (refinadas) ----------------
    # Sinais clássicos de phishing (ação + link)
    termos_acao = ["clique", "acesse", "confirme", "atualize", "verifique", "baixe", "faça login"]
    termos_sensiveis = ["senha", "token", "código", "codigo", "sms", "dados", "cartão", "cartao", "cvv"]

    if links:
        risco_suave += 1  # ter link já aumenta leve
        if any(e in texto_lower for e in ["bit.ly","tinyurl","cut.ly","is.gd"]):
            alerta.append("⚠️ Link **encurtado** (frequente em **phishing**).")
            phishing += 2
        if any(t in texto_lower for t in termos_acao):
            alerta.append("🧭 Pede uma **ação imediata** (clicar/confirmar/acessar).")
            phishing += 2
        if any(t in texto_lower for t in termos_sensiveis):
            alerta.append("🔐 Pede/menção a **dados sensíveis** (senha/código/sms).")
            phishing += 2

    # Palavras suspeitas (mais focadas; removi termos que causavam falso positivo em propaganda)
    suspeitas = ["pix", "prêmio", "premio"]  # mantemos poucas e realmente fortes
    if any(p in texto_lower for p in suspeitas):
        alerta.append("🚨 Termos comumente usados em **golpes**.")
        risco_suave += 2

    # Cassino/aposta com regex de borda (não pega 'Betta')
    if _is_gambling(texto_lower):
        alerta.append("🎰 Menciona **cassino/apostas** (muitas fraudes usam esse tema).")
        risco_suave += 2

    # “Dinheiro fácil”: só sobe risco se vier junto de AÇÃO+LINK (senão é típico de anúncio)
    promessas = ["ganhe", "receba", "transferido", "saldo", "r$"]
    if any(p in texto_lower for p in promessas) and (links and any(t in texto_lower for t in termos_acao)):
        alerta.append("💸 Promessa de **dinheiro** associada a ação + link.")
        phishing += 2

    # ---------------- Detector de Marketing/Promo ----------------
    score_mkt, motivos_mkt = detectar_marketing(texto_lower)  # você já tem essa função
    # Reforça marketing se há preços/CPF/urgência mas sem phishing forte
    if score_mkt >= 2 and phishing == 0:
        alerta.extend(motivos_mkt)

    # ---------------- Decisão de categoria (regra clara) ----------------
    # 1) Se há sinais fortes de phishing => golpe/suspeita
    # 2) Se há cara de marketing e phishing fraco/zero => marketing
    # 3) Caso contrário, usa risco_suave para suspeita/segura
    if phishing >= 3:
        categoria = "golpe"
        gravidade = "🚨 **ALERTA MÁXIMO: ALTA PROBABILIDADE DE GOLPE!**"
        header_color = "#e03131"; risk_color = "#e03131"
        risco_barra = min(phishing + risco_suave, 10)
    elif score_mkt >= 2 and phishing == 0:
        categoria = "marketing"
        gravidade = "🛍️ **Promoção/Marketing**"
        header_color = "#2b6ef3"; risk_color = "#2b6ef3"
        risco_barra = min(phishing + risco_suave, 10)  # geralmente baixo
    elif phishing > 0 or risco_suave >= 3:
        categoria = "suspeita"
        gravidade = "⚠️ **Mensagem suspeita. Tenha cuidado.**"
        header_color = "#f59f00"; risk_color = "#f59f00"
        risco_barra = min(phishing + risco_suave, 10)
    else:
        categoria = "segura"
        gravidade = "✅ **Parece segura**"
        header_color = "#2f9e44"; risk_color = "#2f9e44"
        risco_barra = min(phishing + risco_suave, 10)

    # ---------------- Renderização ----------------
    header_html = f"<div class='alert-header' style='background:{header_color};'>{gravidade}</div>"
    fill = (risco_barra/10)
    risk_html = f"""
    <div class='risk-box'>
      <div class='risk-label'><span>Nível de risco de golpe</span><span>{risco_barra}/10</span></div>
      <div class='risk-bar'><div style='width:{fill*100:.0f}%; background:{risk_color};'></div></div>
    </div>"""

    itens = ""
    for a in alerta + (motivos_mkt if (categoria=="marketing" and motivos_mkt) else []):
        em = a.strip().split(" ")[0]
        resto = a[len(em):].strip() if em and len(em) <= 3 else a
        emoji_html = f"<div class='alert-emoji'>{em}</div>" if len(em) <= 3 else "<div class='alert-emoji'>•</div>"
        texto_html = f"<div class='alert-text'>{resto}</div>"
        itens += f"<li class='alert-item'>{emoji_html}{texto_html}</li>"

    lista_html = (
        f"<ul class='alerts'>{itens}</ul>"
        if itens
        else f"<div class='alert-item'><div class='alert-emoji'>✅</div><div class='alert-text'>Confiabilidade do modelo: <b>{score_modelo:.2f}</b></div></div>"
    )

    html_final = header_html + risk_html + lista_html

    # Preview de links + dica
    for link in links:
        preview = get_link_preview(link)
        st.markdown("---")
        st.markdown("### ⚠️ **NÃO CLIQUE NESSE LINK!**")
        st.markdown(
            f"""
            <div style="
                background:#ef5350; padding:18px; border-radius:14px;
                color:white; box-shadow:0 4px 10px rgba(0,0,0,.25);
                line-height:1.45;">
              <b>🚫 ESTE LINK PODE SER PERIGOSO</b><br><br>
              <b>Endereço:</b> {preview['url']}<br>
              <b>Título detectado:</b> {preview['title']}
            </div>
            """, unsafe_allow_html=True)
        if preview.get("img"):
            st.image(preview["img"], caption="Prévia do site", use_column_width=True)

        if categoria == "marketing":
            st.info("ℹ️ Parece **promoção**. Acesse digitando o site oficial no navegador e evite links encurtados.")

    return html_final









# ---------- INTERFACE ----------
texto = st.text_area("Cole aqui a mensagem recebida:",
                     placeholder="Ex: Oi, clique aqui para atualizar seus dados bancários.")

if st.button("Analisar"):
    resposta = analisar_mensagem(texto)
    st.markdown(resposta, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

with st.expander("ℹ️ Sobre este projeto"):
    st.write("""
    Este aplicativo utiliza inteligência artificial para detectar possíveis **golpes e fraudes** em mensagens.
    
    🔍 **Como funciona:**  
    O texto é analisado por um modelo BERT treinado em português, que detecta padrões suspeitos
    como links, promessas de dinheiro e palavras-chave de golpe.

    🧠 **Tecnologias usadas:**  
    - Streamlit (frontend e hospedagem)  
    - Transformers (modelo BERTweet)  
    - BeautifulSoup + Requests (pré-visualização de links)  

    💡 Desenvolvido por **Matheus Henrique** como parte do portfólio de projetos em IA aplicada à segurança digital.
    """)
st.caption("Feito com 💡 IA — Projeto de segurança cibernética com Python.")
