"""
ConcursoFocus — Sistema de Estudos para Concursos Públicos
==========================================================
PERSISTÊNCIA:
  - Modo local   : salva em ./data/ (desenvolvimento)
  - Modo Cloud   : salva via GitHub Gist (não apaga nunca)

SETUP GitHub Gist (faça 1 vez):
  1. Acesse https://github.com/settings/tokens → New token (classic)
     Permissão: marque apenas "gist"  →  copie o token
  2. Crie um Gist em https://gist.github.com
     - Crie dois arquivos: materias.json  e  sessoes.json (conteúdo: [])
     - Copie o Gist ID da URL (hash de 32 chars)
  3. No Streamlit Cloud → App Settings → Secrets:
     [gist]
     token   = "ghp_xxxxxxxxxxxx"
     gist_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
"""

import streamlit as st
import json, os, csv, io, requests
from datetime import datetime, date, timedelta

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ConcursoFocus",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PERSISTÊNCIA: GitHub Gist OU local ───────────────────────────────────────
def _gist_cfg():
    """Retorna (token, gist_id) se configurado nos secrets, senão None."""
    try:
        cfg = st.secrets.get("gist", {})
        t, g = cfg.get("token"), cfg.get("gist_id")
        return (t, g) if t and g else None
    except Exception:
        return None

def _gist_load(filename: str) -> list:
    cfg = _gist_cfg()
    if not cfg:
        return []
    token, gist_id = cfg
    try:
        r = requests.get(
            f"https://api.github.com/gists/{gist_id}",
            headers={"Authorization": f"token {token}"},
            timeout=8,
        )
        content = r.json()["files"][filename]["content"]
        return json.loads(content)
    except Exception:
        return []

def _gist_save(filename: str, data: list):
    cfg = _gist_cfg()
    if not cfg:
        return
    token, gist_id = cfg
    try:
        requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers={"Authorization": f"token {token}"},
            json={"files": {filename: {"content": json.dumps(data, ensure_ascii=False, indent=2, default=str)}}},
            timeout=10,
        )
    except Exception:
        pass

# Diretório local (fallback / desenvolvimento)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MATERIAS_FILE = os.path.join(DATA_DIR, "materias.json")
SESSOES_FILE  = os.path.join(DATA_DIR, "sessoes.json")

def _local_load(path: str) -> list:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def _local_save(path: str, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# Cache de sessão para evitar múltiplos requests ao Gist por rerun
if "db_materias" not in st.session_state:
    st.session_state.db_materias = None
if "db_sessoes" not in st.session_state:
    st.session_state.db_sessoes  = None

def get_materias(force=False) -> list:
    if st.session_state.db_materias is None or force:
        if _gist_cfg():
            st.session_state.db_materias = _gist_load("materias.json")
        else:
            st.session_state.db_materias = _local_load(MATERIAS_FILE)
    return st.session_state.db_materias

def get_sessoes(force=False) -> list:
    if st.session_state.db_sessoes is None or force:
        if _gist_cfg():
            st.session_state.db_sessoes = _gist_load("sessoes.json")
        else:
            st.session_state.db_sessoes = _local_load(SESSOES_FILE)
    return st.session_state.db_sessoes

def save_materias(data: list):
    st.session_state.db_materias = data
    if _gist_cfg():
        _gist_save("materias.json", data)
    else:
        _local_save(MATERIAS_FILE, data)

def save_sessoes(data: list):
    st.session_state.db_sessoes = data
    if _gist_cfg():
        _gist_save("sessoes.json", data)
    else:
        _local_save(SESSOES_FILE, data)

# ── CSS COMPLETO ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ── BASE ── */
html, body, [class*="css"], .stApp * {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stApp                    { background: #1a1f3a !important; }
.block-container          { padding-top: 1.2rem !important; max-width: 1200px !important; }
header[data-testid="stHeader"] { background: transparent !important; display: none !important; }
footer                    { display: none !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: #1e2447 !important;
  border-right: 1px solid rgba(255,255,255,.07) !important;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div { color: #a0aac8 !important; }

/* ── MÉTRICAS ── */
[data-testid="stMetric"] {
  background: #232b50 !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 12px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] p { color: #6b7a9e !important; font-size: 11px !important; text-transform: uppercase; letter-spacing:.5px; }
[data-testid="stMetricValue"]   { color: #e8ecff !important; font-size: 24px !important; font-weight: 700 !important; }

/* ── TODOS OS INPUTS — força fundo escuro e texto claro ── */
input[type="text"],
input[type="number"],
input[type="date"],
input[type="time"],
input[type="datetime-local"],
textarea,
select {
  background-color: #1c2340 !important;
  color: #e8ecff !important;
  border: 1px solid rgba(91,124,253,.25) !important;
  border-radius: 9px !important;
  caret-color: #7b96ff !important;
}
input::placeholder, textarea::placeholder { color: #4a5272 !important; }

/* ── SELECTBOX / DROPDOWN ── */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] div[class*="ValueContainer"],
div[data-baseweb="select"] div[class*="singleValue"],
div[data-baseweb="select"] input {
  background-color: #1c2340 !important;
  color: #e8ecff !important;
  border-color: rgba(91,124,253,.25) !important;
}
div[data-baseweb="select"] > div { border-radius: 9px !important; border: 1px solid rgba(91,124,253,.25) !important; }
div[data-baseweb="popover"],
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"]    { background: #1e2447 !important; border: 1px solid rgba(255,255,255,.1) !important; }
div[data-baseweb="option"]  { background: #1e2447 !important; color: #a0aac8 !important; }
div[data-baseweb="option"]:hover { background: #2d3561 !important; color: #e8ecff !important; }
/* seta do select */
div[data-baseweb="select"] svg { fill: #6b7a9e !important; }

/* ── DATE / TIME pickers ── */
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {
  background-color: #1c2340 !important;
  color: #e8ecff !important;
  border: 1px solid rgba(91,124,253,.25) !important;
  border-radius: 9px !important;
}
/* ícone do calendário */
div[data-testid="stDateInput"] button,
div[data-testid="stTimeInput"] button { color: #6b7a9e !important; background: transparent !important; }

/* ── TEXTAREA ── */
div[data-testid="stTextArea"] textarea {
  background-color: #1c2340 !important;
  color: #e8ecff !important;
  border: 1px solid rgba(91,124,253,.25) !important;
  border-radius: 9px !important;
}

/* ── NUMBER INPUT ── */
div[data-testid="stNumberInput"] input {
  background-color: #1c2340 !important;
  color: #e8ecff !important;
  border: 1px solid rgba(91,124,253,.25) !important;
}
div[data-testid="stNumberInput"] button { background: #2d3561 !important; color: #e8ecff !important; border: none !important; }

/* ── LABELS ── */
label, .stTextInput label, .stSelectbox label,
.stDateInput label, .stTimeInput label,
.stNumberInput label, .stTextArea label,
.stCheckbox label, .stRadio label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
  color: #6b7a9e !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: .5px !important;
}

/* ── BOTÕES ── */
.stButton > button {
  background: linear-gradient(135deg, #5b7cfd, #6c63ff) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 9px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  box-shadow: 0 4px 14px rgba(91,124,253,.3) !important;
  padding: 10px 20px !important;
}
.stButton > button:hover { filter: brightness(1.12) !important; transform: translateY(-1px) !important; }
[data-testid="stDownloadButton"] > button {
  background: rgba(255,255,255,.06) !important;
  color: #a0aac8 !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  box-shadow: none !important;
}
[data-testid="stFormSubmitButton"] > button {
  background: linear-gradient(135deg, #5b7cfd, #6c63ff) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 9px !important;
  font-weight: 700 !important;
  width: 100% !important;
  padding: 12px !important;
  box-shadow: 0 4px 16px rgba(91,124,253,.35) !important;
}

/* ── RADIO ── */
.stRadio > div { gap: 6px !important; }
.stRadio [data-testid="stMarkdownContainer"] p { color: #a0aac8 !important; font-size: 13px !important; }

/* ── CHECKBOX ── */
.stCheckbox span { color: #a0aac8 !important; }
.stCheckbox input[type="checkbox"] { accent-color: #5b7cfd !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] * { background: #1e2447 !important; color: #a0aac8 !important; }
[data-testid="stDataFrame"] th { color: #6b7a9e !important; font-size: 11px !important; text-transform: uppercase; }

/* ── ALERTS / SUCCESS ── */
[data-testid="stAlert"]       { border-radius: 10px !important; }
.stSuccess                    { background: rgba(74,201,138,.1) !important; border-color: rgba(74,201,138,.3) !important; }
.stWarning                    { background: rgba(245,166,35,.1) !important; }
.stInfo                       { background: rgba(91,124,253,.1) !important; }

/* ── DIVIDER ── */
hr { border-color: rgba(255,255,255,.07) !important; }

/* ── TEXTOS GENÉRICOS ── */
p, li, span { color: #a0aac8; }
h1, h2, h3  { color: #e8ecff !important; }

/* ── FORM container ── */
[data-testid="stForm"] {
  background: #232b50 !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 14px !important;
  padding: 20px !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
  background: #232b50 !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: #e8ecff !important; }

/* remove bordas brancas residuais do Streamlit */
div[class*="stTextInput"] > div,
div[class*="stSelectbox"] > div,
div[class*="stDateInput"] > div,
div[class*="stTimeInput"] > div,
div[class*="stNumberInput"] > div,
div[class*="stTextArea"] > div {
  background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ── ALGORITMO ─────────────────────────────────────────────────────────────────
def calcular_score(materia, sessoes, modo):
    nome     = materia["nome"]
    prio     = materia.get("prioridade", 2)
    q_edital = materia.get("questoes_edital", 10)
    sm       = [s for s in sessoes if s.get("materia") == nome]
    dias_sem = (datetime.now() - max([datetime.fromisoformat(s["data_inicio"]) for s in sm])).days if sm else 30
    fator    = 1.0
    if modo == "questoes":
        ac = sum(s.get("acertos", 0) for s in sm)
        tot = ac + sum(s.get("erros", 0) for s in sm)
        if tot > 0: fator = 2.0 - (ac / tot)
    return {1:3.0,2:2.0,3:1.0}.get(prio, 2.0) * (q_edital/10) * (1 + dias_sem/7) * fator

def sugerir(modo, turbo):
    materias = get_materias()
    sessoes  = get_sessoes()
    if not materias: return None
    cands  = materias if turbo else ([m for m in materias if m.get("prioridade",2)<=2] or materias)
    scores = sorted([(m, calcular_score(m, sessoes, modo)) for m in cands], key=lambda x: x[1], reverse=True)
    melhor = scores[0][0]
    sm     = [s for s in sessoes if s.get("materia")==melhor["nome"]]
    cc     = {}
    for s in sm: cc[s.get("conteudo","")] = cc.get(s.get("conteudo",""),0)+1
    conts = sorted(melhor.get("conteudos",[]), key=lambda c: c.get("prioridade",2)*10 - cc.get(c["nome"],0), reverse=True)
    return {"materia": melhor["nome"], "conteudo": conts[0]["nome"] if conts else "Geral",
            "prioridade": melhor.get("prioridade",2), "questoes_edital": melhor.get("questoes_edital",0),
            "top5": [{"nome":m["nome"],"score":round(s,1)} for m,s in scores[:5]]}

# ── DASHBOARD DATA ────────────────────────────────────────────────────────────
def calc_dash():
    sessoes = get_sessoes()
    hoje    = date.today().isoformat()
    sem_ini = (date.today()-timedelta(days=date.today().weekday())).isoformat()
    total_h = sum(s.get("duracao_min",0) for s in sessoes)/60
    ac_tot  = sum(s.get("acertos",0) for s in sessoes)
    er_tot  = sum(s.get("erros",0) for s in sessoes)
    q_tot   = ac_tot+er_tot
    taxa    = round(ac_tot/q_tot*100,1) if q_tot else 0
    h_hj    = sum(s.get("duracao_min",0) for s in sessoes if s.get("data_inicio","").startswith(hoje))/60
    h_sem   = sum(s.get("duracao_min",0) for s in sessoes if s.get("data_inicio","")>=sem_ini)/60
    streak  = 0
    for i in range(30):
        d = (date.today()-timedelta(days=i)).isoformat()
        if any(s.get("data_inicio","").startswith(d) for s in sessoes): streak+=1
        else: break
    pm={}
    for s in sessoes:
        m=s.get("materia","?")
        pm.setdefault(m,{"horas":0,"acertos":0,"erros":0})
        pm[m]["horas"]  +=s.get("duracao_min",0)/60
        pm[m]["acertos"]+=s.get("acertos",0)
        pm[m]["erros"]  +=s.get("erros",0)
    for m in pm:
        t=pm[m]["acertos"]+pm[m]["erros"]
        pm[m]["taxa"]=round(pm[m]["acertos"]/t*100,1) if t else 0
        pm[m]["horas"]=round(pm[m]["horas"],1)
    evo={}
    for i in range(13,-1,-1):
        d=(date.today()-timedelta(days=i)).isoformat(); evo[d]=0.0
    for s in sessoes:
        d=s.get("data_inicio","")[:10]
        if d in evo: evo[d]+=s.get("duracao_min",0)/60
    return {"total_h":round(total_h,1),"taxa":taxa,"q_tot":q_tot,"streak":streak,
            "h_hj":round(h_hj,1),"h_sem":round(h_sem,1),"pm":pm,"evo":evo,
            "recentes":sorted(sessoes,key=lambda x:x.get("data_inicio",""),reverse=True)[:5]}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:4px 0 16px'>
      <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>
        <div style='width:36px;height:36px;background:linear-gradient(135deg,#5b7cfd,#9b72f7);
             border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px'>⚡</div>
        <div>
          <div style='font-size:15px;font-weight:700;color:#e8ecff'>ConcursoFocus</div>
          <div style='font-size:10px;color:#6b7a9e'>Sistema de Aprovação</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    pagina = st.radio("nav", [
        "📊 Dashboard",
        "🎯 Estudar",
        "✏️ Registrar",
        "📚 Matérias",
        "🗂️ Histórico",
        "⚙️ Configurações",
    ], label_visibility="collapsed")

    st.divider()
    d_side = calc_dash()
    st.markdown(f"""
    <div style='display:flex;flex-direction:column;gap:5px'>
      <div style='background:#2d3561;border-radius:9px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center'>
        <span style='font-size:11.5px;color:#6b7a9e'>Horas totais</span>
        <span style='font-size:12px;font-weight:700;color:#7b96ff'>{d_side['total_h']}h</span>
      </div>
      <div style='background:#2d3561;border-radius:9px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center'>
        <span style='font-size:11.5px;color:#6b7a9e'>Taxa de acerto</span>
        <span style='font-size:12px;font-weight:700;color:#4ac98a'>{d_side['taxa']}%</span>
      </div>
      <div style='background:#2d3561;border-radius:9px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center'>
        <span style='font-size:11.5px;color:#6b7a9e'>Sequência</span>
        <span style='font-size:12px;font-weight:700;color:#f5a623'>{d_side['streak']} 🔥</span>
      </div>
    </div>""", unsafe_allow_html=True)

    # Indicador de persistência
    st.markdown("<br>", unsafe_allow_html=True)
    if _gist_cfg():
        st.markdown("<div style='font-size:10px;color:#4ac98a;text-align:center'>☁️ GitHub Gist — dados persistentes</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:10px;color:#f5a623;text-align:center'>💾 Modo local — configure Gist para nuvem</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    hoje_br = date.today().strftime("%A, %d de %B").capitalize()
    st.markdown(f"<h2 style='margin-bottom:2px'>Painel de Desempenho</h2>"
                f"<p style='color:#6b7a9e;margin-bottom:18px'>{hoje_br}</p>", unsafe_allow_html=True)

    d = calc_dash()
    msg = (f"🔥 {d['streak']} dias seguidos! Modo aprovação ativado!"
           if d["streak"]>=7 else
           f"{d['total_h']}h estudadas · {d['taxa']}% de acerto geral"
           if d["total_h"]>0 else
           "Nenhuma sessão ainda — comece hoje! 🚀")

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#2a3578,#3040a0,#4050c0);
         border-radius:14px;padding:20px 24px;margin-bottom:18px;
         border:1px solid rgba(91,124,253,.3);position:relative;overflow:hidden'>
      <div style='font-size:18px;font-weight:700;color:#fff;margin-bottom:3px'>Bom estudo, Candidato! 👋</div>
      <div style='font-size:12.5px;color:rgba(255,255,255,.65)'>{msg}</div>
      <div style='position:absolute;right:20px;bottom:-5px;font-size:56px;opacity:.18'>🎯</div>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("⏱️ Horas Totais",  f"{d['total_h']}h")
    c2.metric("✅ Taxa Acerto",   f"{d['taxa']}%")
    c3.metric("📝 Questões",      d["q_tot"])
    c4.metric("🔥 Dias Seguidos", d["streak"])
    c5.metric("📅 Hoje",          f"{d['h_hj']}h")
    c6.metric("📆 Semana",        f"{d['h_sem']}h")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])

    with col1:
        evo   = d["evo"]
        dts   = list(evo.keys())
        vals  = [evo[k] for k in dts]
        max_v = max(vals) if any(v>0 for v in vals) else 1
        lbls  = [k[5:].replace("-","/") for k in dts]
        bars  = "<div style='display:flex;align-items:flex-end;gap:4px;height:90px;margin-top:8px'>"
        for lbl,v in zip(lbls,vals):
            pct  = max(v/max_v*100, v>0 and 5 or 0)
            col  = "linear-gradient(180deg,#7b96ff,#5b7cfd)" if v>0 else "#2d3561"
            bars+= (f"<div style='flex:1;display:flex;flex-direction:column;align-items:center;gap:3px'>"
                    f"<div style='width:100%;height:{pct}%;background:{col};border-radius:3px 3px 0 0;min-height:3px'></div>"
                    f"<div style='font-size:8px;color:#6b7a9e'>{lbl}</div></div>")
        bars += "</div>"
        st.markdown(f"<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>"
                    f"<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:6px'>📈 Horas — 14 dias</div>"
                    f"{bars}</div>", unsafe_allow_html=True)

    with col2:
        sk_msg = ("Estude hoje!" if d["streak"]==0 else "Continue amanhã!" if d["streak"]<3
                  else "Pegando ritmo! 🔥" if d["streak"]<7 else "Sequência de campeão! 💪"
                  if d["streak"]<14 else "Imparável! 🏆")
        st.markdown(f"""
        <div style='background:#232b50;border:1px solid rgba(255,255,255,.07);
             border-radius:12px;padding:18px;text-align:center'>
          <div style='font-size:13px;font-weight:700;color:#e8ecff;text-align:left;margin-bottom:12px'>🔥 Sequência</div>
          <div style='font-size:28px'>🔥</div>
          <div style='font-size:46px;font-weight:800;background:linear-gradient(135deg,#f5a623,#f56565);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1'>{d['streak']}</div>
          <div style='font-size:11px;color:#6b7a9e;margin-top:3px'>dias consecutivos</div>
          <div style='font-size:12px;color:#a0aac8;margin-top:8px'>{sk_msg}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if d["pm"]:
        import pandas as pd
        rows=[]
        for m,r in sorted(d["pm"].items(),key=lambda x:x[1]["horas"],reverse=True):
            tot=r["acertos"]+r["erros"]
            rows.append({"Matéria":m,"Horas":f"{r['horas']}h","Questões":tot,
                         "Acerto":f"{r['taxa']}%" if tot else "—",
                         "Status":"🟢" if r["taxa"]>=70 else "🟡" if r["taxa"]>=50 else "🔴" if tot else "⚪"})
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:12px'>📚 Desempenho por Matéria</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if d["recentes"]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:12px'>🕒 Últimas Sessões</div>", unsafe_allow_html=True)
        for s in d["recentes"]:
            dt  = datetime.fromisoformat(s["data_inicio"]).strftime("%d/%m %H:%M")
            dur = f"{s.get('duracao_min',0)}min" if s.get("duracao_min",0)<60 else f"{s.get('duracao_min',0)/60:.1f}h"
            q   = s.get("acertos",0)+s.get("erros",0)
            q_s = f" · {s['acertos']}/{q} acertos" if q>0 else ""
            enc = " · <span style='color:#4ac98a'>✓ Concluído</span>" if s.get("encerrou_assunto") else ""
            ico = "🧩" if s.get("tipo")=="questoes" else "📖"
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.05)'>
              <div style='width:34px;height:34px;border-radius:9px;background:rgba(91,124,253,.14);
                   display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0'>{ico}</div>
              <div>
                <div style='font-size:12.5px;font-weight:600;color:#e8ecff'>{s['materia']} · <span style='font-weight:400'>{s['conteudo']}</span></div>
                <div style='font-size:11px;color:#6b7a9e'>{dt} · {dur}{q_s}{enc}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ESTUDAR
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🎯 Estudar":
    st.markdown("<h2 style='margin-bottom:2px'>Iniciar Estudo</h2>"
                "<p style='color:#6b7a9e;margin-bottom:18px'>Algoritmo de revisão espaçada + peso edital</p>",
                unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1: modo  = st.radio("Modo",  ["📖 Estudar Matéria","🧩 Resolver Questões"], horizontal=True, key="modo_e")
    with c2: plano = st.radio("Plano", ["📋 Pré-Edital","⚡ Pós-Edital Turbo"],       horizontal=True, key="plano_e")

    modo_k  = "questoes" if "Questões" in modo else "materia"
    turbo_k = "Turbo" in plano

    sug = sugerir(modo_k, turbo_k)
    if not sug:
        st.warning("Nenhuma matéria cadastrada. Vá até **📚 Matérias** e importe uma planilha CSV.")
    else:
        pl = {1:"🔴 Alta",2:"🟡 Média",3:"⚪ Baixa"}
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#2a3578,#1e2a60 60%,#232b52);
             border:1px solid rgba(91,124,253,.35);border-radius:14px;padding:24px;
             margin:14px 0;position:relative;overflow:hidden'>
          <div style='position:absolute;top:-50px;right:-40px;width:150px;height:150px;
               background:radial-gradient(circle,rgba(91,124,253,.18) 0%,transparent 70%)'></div>
          <div style='font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:2px;
               color:#7b96ff;margin-bottom:7px'>📌 Sugestão do Sistema</div>
          <div style='font-size:22px;font-weight:700;color:#fff;margin-bottom:4px'>{sug['materia']}</div>
          <div style='font-size:13px;color:#a0aac8;margin-bottom:14px'>{sug['conteudo']}</div>
          <div style='display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px'>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>📋 {sug['questoes_edital']} questões no edital</span>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>{pl.get(sug['prioridade'],'')}</span>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>{'🧩 Questões' if modo_k=='questoes' else '📖 Teoria'}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([1,4])
        with col1:
            if st.button("▶ Usar esta sugestão"):
                st.session_state["sug_mat"]  = sug["materia"]
                st.session_state["sug_cont"] = sug["conteudo"]
                st.session_state["sug_tipo"] = modo_k
                st.success("✅ Sugestão carregada! Vá para **✏️ Registrar**.")
        with col2:
            if st.button("↻ Nova sugestão"): st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:12px'>🏆 Ranking de Prioridade</div>", unsafe_allow_html=True)
        for i, item in enumerate(sug["top5"]):
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)'>
              <div style='width:20px;font-size:11px;color:#6b7a9e;font-weight:600'>{i+1}</div>
              <div style='flex:1;font-size:12.5px;color:#a0aac8'>{item['nome']}</div>
              <span style='padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;
                   background:rgba(91,124,253,.14);color:#7b96ff'>{item['score']} pts</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  REGISTRAR
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Registrar":
    st.markdown("<h2 style='margin-bottom:2px'>Registrar Sessão</h2>"
                "<p style='color:#6b7a9e;margin-bottom:18px'>Lançar resultado da bateria de estudos</p>",
                unsafe_allow_html=True)

    materias = get_materias()
    if not materias:
        st.warning("Nenhuma matéria cadastrada. Vá até **📚 Matérias** primeiro.")
    else:
        with st.form("form_reg", clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                tipo = st.selectbox("Tipo de Sessão",
                                    ["📖 Estudo de Matéria","🧩 Resolução de Questões"])
            with c2:
                nomes   = [m["nome"] for m in materias]
                def_mat = st.session_state.get("sug_mat", nomes[0])
                def_idx = nomes.index(def_mat) if def_mat in nomes else 0
                mat_sel = st.selectbox("Matéria", nomes, index=def_idx)

            mat_obj  = next((m for m in materias if m["nome"]==mat_sel), None)
            cont_lst = [c["nome"] for c in mat_obj.get("conteudos",[])] if mat_obj else ["Geral"]
            def_cont = st.session_state.get("sug_cont","")
            def_ci   = cont_lst.index(def_cont) if def_cont in cont_lst else 0
            conteudo = st.selectbox("Conteúdo", cont_lst, index=def_ci)

            c1,c2 = st.columns(2)
            with c1:
                d_ini = st.date_input("Data Início", value=date.today())
                h_ini = st.time_input("Hora Início",
                                      value=datetime.now().replace(
                                          hour=max(datetime.now().hour-1,0),
                                          minute=0, second=0, microsecond=0))
            with c2:
                d_fim = st.date_input("Data Fim", value=date.today())
                h_fim = st.time_input("Hora Fim",
                                      value=datetime.now().replace(second=0, microsecond=0))

            acertos = erros = 0
            if "Questões" in tipo:
                q1,q2 = st.columns(2)
                with q1: acertos = st.number_input("✅ Acertos", min_value=0, value=0)
                with q2: erros   = st.number_input("❌ Erros",   min_value=0, value=0)

            encerrou = st.checkbox("Encerrei esse assunto ✓")
            obs      = st.text_area("Observações", placeholder="Anotações, dificuldades, dúvidas...")

            salvar = st.form_submit_button("💾 Salvar Sessão")

        if salvar:
            dt_ini = datetime.combine(d_ini, h_ini)
            dt_fim = datetime.combine(d_fim, h_fim)
            dur    = max(int((dt_fim-dt_ini).total_seconds()/60), 0)
            sessoes = get_sessoes()
            sessoes.append({
                "id":              datetime.now().isoformat(),
                "materia":         mat_sel,
                "conteudo":        conteudo,
                "tipo":            "questoes" if "Questões" in tipo else "materia",
                "data_inicio":     dt_ini.isoformat(),
                "data_fim":        dt_fim.isoformat(),
                "duracao_min":     dur,
                "encerrou_assunto":encerrou,
                "acertos":         int(acertos),
                "erros":           int(erros),
                "observacoes":     obs,
            })
            save_sessoes(sessoes)
            for k in ("sug_mat","sug_cont","sug_tipo"): st.session_state.pop(k,None)
            st.success(f"✅ Sessão de **{dur} min** salva com sucesso!")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  MATÉRIAS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📚 Matérias":
    st.markdown("<h2 style='margin-bottom:2px'>Gestão de Matérias</h2>"
                "<p style='color:#6b7a9e;margin-bottom:18px'>Edital, conteúdos e prioridades</p>",
                unsafe_allow_html=True)

    modelo = [["materia","conteudo","prioridade"],
              ["Direito Constitucional","Princípios Fundamentais",1],
              ["Direito Constitucional","Direitos e Garantias",1],
              ["Direito Constitucional","Organização do Estado",2],
              ["Direito Administrativo","Atos Administrativos",1],
              ["Direito Administrativo","Licitações e Contratos",1],
              ["Língua Portuguesa","Interpretação de Texto",1],
              ["Língua Portuguesa","Gramática",2],
              ["Raciocínio Lógico","Proposições Lógicas",1],
              ["Informática","Segurança da Informação",1]]
    buf = io.StringIO()
    csv.writer(buf).writerows(modelo)

    c1,c2 = st.columns([2,1])
    with c1: arquivo = st.file_uploader("📤 Importar CSV", type=["csv"])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇ Baixar Modelo CSV", buf.getvalue().encode("utf-8-sig"),
                           "modelo_materias.csv", "text/csv")

    if arquivo:
        content = arquivo.read().decode("utf-8-sig")
        reader  = csv.DictReader(io.StringIO(content))
        md = {}
        for row in reader:
            nome = row.get("materia","").strip()
            cont = row.get("conteudo","").strip()
            prio = int(row.get("prioridade",2) or 2)
            if not nome: continue
            if nome not in md:
                md[nome] = {"nome":nome,"prioridade":prio,"questoes_edital":10,"conteudos":[]}
            if cont: md[nome]["conteudos"].append({"nome":cont,"prioridade":prio})
            if prio < md[nome]["prioridade"]: md[nome]["prioridade"] = prio

        st.markdown("<br><div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:10px'>"
                    "⚙️ Configure questões do edital</div>", unsafe_allow_html=True)
        novas = list(md.values())

        with st.form("form_import"):
            for i,m in enumerate(novas):
                cc1,cc2,cc3 = st.columns([3,1,1])
                with cc1:
                    st.markdown(f"<div style='padding:9px 0;font-size:13px;color:#a0aac8'>{m['nome']}</div>",
                                unsafe_allow_html=True)
                with cc2:
                    opts  = ["🔴 Alta","🟡 Média","⚪ Baixa"]
                    p_sel = st.selectbox("Prioridade", opts, index=m["prioridade"]-1,
                                         key=f"p_{i}", label_visibility="collapsed")
                    novas[i]["prioridade"] = opts.index(p_sel)+1
                with cc3:
                    q = st.number_input("Questões", min_value=0, value=int(m["questoes_edital"]),
                                        key=f"q_{i}", label_visibility="collapsed")
                    novas[i]["questoes_edital"] = int(q)

            if st.form_submit_button("✅ Salvar Matérias", use_container_width=True):
                save_materias(novas)
                st.success(f"✅ {len(novas)} matérias salvas!")
                st.rerun()

    materias = get_materias()
    if materias:
        st.markdown("<br>", unsafe_allow_html=True)
        import pandas as pd
        rows=[{"Matéria":m["nome"],
               "Prioridade":{1:"🔴 Alta",2:"🟡 Média",3:"⚪ Baixa"}.get(m.get("prioridade",2),"—"),
               "Questões Edital":m.get("questoes_edital",0),
               "Conteúdos":len(m.get("conteudos",[]))} for m in materias]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma matéria cadastrada. Importe um CSV acima.")

# ══════════════════════════════════════════════════════════════════════════════
#  HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🗂️ Histórico":
    st.markdown("<h2 style='margin-bottom:2px'>Histórico de Sessões</h2>"
                "<p style='color:#6b7a9e;margin-bottom:18px'>Todos os registros de estudo</p>",
                unsafe_allow_html=True)

    # Botão de atualizar (força reload do Gist)
    if st.button("🔄 Atualizar"):
        st.session_state.db_sessoes = None
        st.rerun()

    sessoes = get_sessoes()
    if not sessoes:
        st.info("Nenhuma sessão registrada ainda.")
    else:
        import pandas as pd
        rows=[]
        for s in reversed(sessoes):
            dt  = datetime.fromisoformat(s["data_inicio"]).strftime("%d/%m/%Y %H:%M")
            dur = f"{s.get('duracao_min',0)}min" if s.get("duracao_min",0)<60 else f"{s.get('duracao_min',0)/60:.1f}h"
            q   = s.get("acertos",0)+s.get("erros",0)
            pct = round(s.get("acertos",0)/q*100) if q>0 else None
            rows.append({"Data":dt,"Matéria":s.get("materia",""),"Conteúdo":s.get("conteudo",""),
                         "Tipo":"🧩 Questões" if s.get("tipo")=="questoes" else "📖 Estudo",
                         "Duração":dur,
                         "Resultado":f"{s.get('acertos',0)}/{q} ({pct}%)" if q>0 else "—",
                         "Encerrou":"✓" if s.get("encerrou_assunto") else "—"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        buf2=io.StringIO()
        pd.DataFrame(rows).to_csv(buf2,index=False)
        st.download_button("⬇ Exportar CSV", buf2.getvalue().encode("utf-8-sig"),
                           "historico.csv","text/csv")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "⚙️ Configurações":
    st.markdown("<h2 style='margin-bottom:2px'>Configurações</h2>"
                "<p style='color:#6b7a9e;margin-bottom:18px'>Persistência e backup de dados</p>",
                unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:22px;margin-bottom:18px'>
      <div style='font-size:14px;font-weight:700;color:#e8ecff;margin-bottom:12px'>☁️ Como configurar persistência no Streamlit Cloud</div>
      <div style='font-size:13px;color:#a0aac8;line-height:1.8'>
        <b style='color:#7b96ff'>1.</b> Acesse <a href='https://github.com/settings/tokens' target='_blank' style='color:#7b96ff'>github.com/settings/tokens</a> → New token (classic) → marque apenas <code style='background:#1c2340;padding:2px 6px;border-radius:4px'>gist</code><br>
        <b style='color:#7b96ff'>2.</b> Crie um Gist em <a href='https://gist.github.com' target='_blank' style='color:#7b96ff'>gist.github.com</a> com dois arquivos: <code style='background:#1c2340;padding:2px 6px;border-radius:4px'>materias.json</code> e <code style='background:#1c2340;padding:2px 6px;border-radius:4px'>sessoes.json</code>, ambos com conteúdo <code style='background:#1c2340;padding:2px 6px;border-radius:4px'>[]</code><br>
        <b style='color:#7b96ff'>3.</b> Copie o ID do Gist (hash na URL)<br>
        <b style='color:#7b96ff'>4.</b> No Streamlit Cloud → seu app → <b>Settings → Secrets</b>, cole:
      </div>
      <pre style='background:#1c2340;border-radius:9px;padding:14px;margin-top:12px;font-size:12px;color:#4ac98a'>[gist]
token   = "ghp_SeuTokenAqui"
gist_id = "SeuGistIdAqui"</pre>
    </div>""", unsafe_allow_html=True)

    # Status atual
    if _gist_cfg():
        st.success("✅ GitHub Gist configurado! Dados persistindo na nuvem.")
    else:
        st.warning("⚠️ Gist não configurado — dados salvam apenas localmente e serão perdidos ao reiniciar.")

    st.divider()
    st.markdown("<div style='font-size:14px;font-weight:700;color:#e8ecff;margin-bottom:12px'>📦 Backup / Restauração</div>", unsafe_allow_html=True)

    sessoes  = get_sessoes()
    materias = get_materias()

    col1, col2 = st.columns(2)
    with col1:
        backup = json.dumps({"materias": materias, "sessoes": sessoes},
                            ensure_ascii=False, indent=2, default=str)
        st.download_button("⬇ Baixar Backup Completo (JSON)",
                           backup.encode("utf-8"), "backup_concursofocus.json", "application/json")
    with col2:
        restore_file = st.file_uploader("📤 Restaurar Backup JSON", type=["json"])
        if restore_file:
            data = json.load(restore_file)
            if st.button("✅ Confirmar Restauração"):
                save_materias(data.get("materias",[]))
                save_sessoes(data.get("sessoes",[]))
                st.session_state.db_materias = None
                st.session_state.db_sessoes  = None
                st.success("✅ Dados restaurados com sucesso!")
                st.rerun()

    st.divider()
    st.markdown("<div style='font-size:14px;font-weight:700;color:#e8ecff;margin-bottom:12px'>🗑️ Zona de Perigo</div>", unsafe_allow_html=True)
    with st.expander("Limpar todos os dados"):
        st.warning("Esta ação é irreversível. Todos os dados serão apagados.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Apagar sessões"):
                save_sessoes([])
                st.session_state.db_sessoes = []
                st.success("Sessões apagadas.")
        with col2:
            if st.button("🗑️ Apagar TUDO"):
                save_sessoes([])
                save_materias([])
                st.session_state.db_sessoes  = []
                st.session_state.db_materias = []
                st.success("Todos os dados apagados.")
