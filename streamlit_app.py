"""
ConcursoFocus — Sistema de Estudos para Concursos Públicos
Deploy gratuito: https://streamlit.io/cloud
"""
import streamlit as st
import json, os, csv, io
from datetime import datetime, date, timedelta

# ── CONFIG ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ConcursoFocus",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
MATERIAS_FILE = os.path.join(DATA_DIR, "materias.json")
SESSOES_FILE  = os.path.join(DATA_DIR, "sessoes.json")

# ── CSS — Navy Blue Theme ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }

/* BG */
.stApp { background: #1a1f3a !important; }
section[data-testid="stSidebar"] { background: #1e2447 !important; border-right: 1px solid rgba(255,255,255,.07) !important; }
section[data-testid="stSidebar"] * { color: #a0aac8 !important; }

/* esconde header padrão */
header[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 1.5rem !important; }

/* Métricas */
[data-testid="stMetric"] {
  background: #232b50 !important;
  border: 1px solid rgba(255,255,255,.07) !important;
  border-radius: 12px !important;
  padding: 16px 18px !important;
}
[data-testid="stMetricLabel"] { color: #6b7a9e !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: .5px; }
[data-testid="stMetricValue"] { color: #e8ecff !important; font-size: 26px !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input { background: #1c2340 !important; border: 1px solid rgba(255,255,255,.1) !important; border-radius: 9px !important; color: #e8ecff !important; }
.stSelectbox [data-baseweb="select"] { background: #1c2340 !important; border: 1px solid rgba(255,255,255,.1) !important; border-radius: 9px !important; }
.stSelectbox [data-baseweb="select"] * { color: #e8ecff !important; }
.stSelectbox [data-baseweb="popover"] { background: #232b50 !important; }

/* Botões */
.stButton > button {
  background: linear-gradient(135deg, #5b7cfd, #6c63ff) !important;
  color: white !important; border: none !important; border-radius: 9px !important;
  font-weight: 600 !important; font-size: 13px !important;
  box-shadow: 0 4px 14px rgba(91,124,253,.3) !important;
  transition: filter .18s !important;
}
.stButton > button:hover { filter: brightness(1.1) !important; }

/* Download */
[data-testid="stDownloadButton"] > button {
  background: rgba(255,255,255,.06) !important; color: #a0aac8 !important;
  border: 1px solid rgba(255,255,255,.1) !important; border-radius: 9px !important;
  font-weight: 600 !important; box-shadow: none !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #1e2447 !important; border-radius: 10px !important; gap: 4px !important; padding: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border-radius: 7px !important; color: #6b7a9e !important; font-weight: 600 !important; font-size: 13px !important; }
.stTabs [aria-selected="true"] { background: #232b50 !important; color: #7b96ff !important; }
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: 1rem !important; }

/* DataFrames / Tables */
.stDataFrame { background: #232b50 !important; border-radius: 12px !important; }

/* Dividers */
hr { border-color: rgba(255,255,255,.07) !important; }

/* Expander */
[data-testid="stExpander"] { background: #232b50 !important; border: 1px solid rgba(255,255,255,.07) !important; border-radius: 12px !important; }
[data-testid="stExpander"] summary { color: #e8ecff !important; }

/* Checkbox / Radio */
.stRadio label, .stCheckbox label { color: #a0aac8 !important; }
.stRadio [data-testid="stMarkdownContainer"] p { color: #a0aac8 !important; }

/* Alerta de sucesso */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* Texto geral */
p, li, label, span { color: #a0aac8; }
h1,h2,h3 { color: #e8ecff !important; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────
def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def get_materias(): return load_json(MATERIAS_FILE, [])
def get_sessoes():  return load_json(SESSOES_FILE, [])

# ── ALGORITMO DE PRIORIDADE ──────────────────────────────────────────────────
def calcular_score(materia, sessoes, modo):
    nome = materia["nome"]
    prio = materia.get("prioridade", 2)
    q_edital = materia.get("questoes_edital", 10)
    sess_mat = [s for s in sessoes if s.get("materia") == nome]

    if sess_mat:
        datas = [datetime.fromisoformat(s["data_inicio"]) for s in sess_mat]
        dias_sem = (datetime.now() - max(datas)).days
    else:
        dias_sem = 30

    fator_erro = 1.0
    if modo == "questoes":
        ac = sum(s.get("acertos", 0) for s in sess_mat)
        er = sum(s.get("erros", 0) for s in sess_mat)
        tot = ac + er
        if tot > 0:
            fator_erro = 2.0 - (ac / tot)

    peso = {1: 3.0, 2: 2.0, 3: 1.0}.get(prio, 2.0)
    return peso * (q_edital / 10) * (1 + dias_sem / 7) * fator_erro

def sugerir(modo, turbo):
    materias = get_materias()
    sessoes  = get_sessoes()
    if not materias:
        return None
    candidatas = materias if turbo else [m for m in materias if m.get("prioridade", 2) <= 2] or materias
    scores = sorted([(m, calcular_score(m, sessoes, modo)) for m in candidatas], key=lambda x: x[1], reverse=True)
    melhor = scores[0][0]
    sess_mat = [s for s in sessoes if s.get("materia") == melhor["nome"]]
    cont_count = {s.get("conteudo", ""): 0 for s in sess_mat}
    for s in sess_mat:
        cont_count[s.get("conteudo", "")] = cont_count.get(s.get("conteudo", ""), 0) + 1
    conts = sorted(melhor.get("conteudos", []), key=lambda c: c.get("prioridade", 2) * 10 - cont_count.get(c["nome"], 0), reverse=True)
    return {
        "materia": melhor["nome"],
        "conteudo": conts[0]["nome"] if conts else "Geral",
        "prioridade": melhor.get("prioridade", 2),
        "questoes_edital": melhor.get("questoes_edital", 0),
        "top5": [{"nome": m["nome"], "score": round(s, 1)} for m, s in scores[:5]],
    }

# ── DASHBOARD CARDS ──────────────────────────────────────────────────────────
def calc_dashboard():
    sessoes = get_sessoes()
    hoje = date.today().isoformat()
    sem_ini = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    total_h = sum(s.get("duracao_min", 0) for s in sessoes) / 60
    total_ac = sum(s.get("acertos", 0) for s in sessoes)
    total_er = sum(s.get("erros", 0) for s in sessoes)
    total_q  = total_ac + total_er
    taxa     = round(total_ac / total_q * 100, 1) if total_q else 0
    sess_hj  = [s for s in sessoes if s.get("data_inicio", "").startswith(hoje)]
    sess_sem = [s for s in sessoes if s.get("data_inicio", "") >= sem_ini]
    h_hj  = sum(s.get("duracao_min", 0) for s in sess_hj) / 60
    h_sem = sum(s.get("duracao_min", 0) for s in sess_sem) / 60
    streak = 0
    for i in range(30):
        d = (date.today() - timedelta(days=i)).isoformat()
        if any(s.get("data_inicio", "").startswith(d) for s in sessoes):
            streak += 1
        else:
            break
    # por matéria
    pm = {}
    for s in sessoes:
        m = s.get("materia", "?")
        pm.setdefault(m, {"horas": 0, "acertos": 0, "erros": 0, "sessoes": 0})
        pm[m]["horas"]   += s.get("duracao_min", 0) / 60
        pm[m]["acertos"] += s.get("acertos", 0)
        pm[m]["erros"]   += s.get("erros", 0)
        pm[m]["sessoes"] += 1
    for m in pm:
        t = pm[m]["acertos"] + pm[m]["erros"]
        pm[m]["taxa"]  = round(pm[m]["acertos"] / t * 100, 1) if t else 0
        pm[m]["horas"] = round(pm[m]["horas"], 1)
    # evolução 14 dias
    evo = {}
    for i in range(13, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        evo[d] = 0.0
    for s in sessoes:
        d = s.get("data_inicio", "")[:10]
        if d in evo:
            evo[d] += s.get("duracao_min", 0) / 60
    return {
        "total_h": round(total_h, 1), "taxa": taxa, "total_q": total_q,
        "streak": streak, "h_hj": round(h_hj, 1), "h_sem": round(h_sem, 1),
        "pm": pm, "evo": evo,
        "recentes": sorted(sessoes, key=lambda x: x.get("data_inicio", ""), reverse=True)[:5],
    }

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:4px 0 18px'>
      <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px'>
        <div style='width:36px;height:36px;background:linear-gradient(135deg,#5b7cfd,#9b72f7);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px'>⚡</div>
        <div>
          <div style='font-size:15px;font-weight:700;color:#e8ecff'>ConcursoFocus</div>
          <div style='font-size:10px;color:#6b7a9e'>Sistema de Aprovação</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    pagina = st.radio(
        "Navegação",
        ["📊 Dashboard", "🎯 Estudar", "✏️ Registrar", "📚 Matérias", "🗂️ Histórico"],
        label_visibility="collapsed",
    )
    st.divider()
    d = calc_dashboard()
    st.markdown(f"<div style='font-size:11px;color:#6b7a9e;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px'>Resumo Rápido</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='display:flex;flex-direction:column;gap:6px'>
      <div style='background:#232b50;border-radius:9px;padding:9px 12px;display:flex;justify-content:space-between'>
        <span style='font-size:12px;color:#6b7a9e'>Horas totais</span>
        <span style='font-size:12px;font-weight:700;color:#7b96ff'>{d['total_h']}h</span>
      </div>
      <div style='background:#232b50;border-radius:9px;padding:9px 12px;display:flex;justify-content:space-between'>
        <span style='font-size:12px;color:#6b7a9e'>Taxa de acerto</span>
        <span style='font-size:12px;font-weight:700;color:#4ac98a'>{d['taxa']}%</span>
      </div>
      <div style='background:#232b50;border-radius:9px;padding:9px 12px;display:flex;justify-content:space-between'>
        <span style='font-size:12px;color:#6b7a9e'>Sequência</span>
        <span style='font-size:12px;font-weight:700;color:#f5a623'>{d['streak']} 🔥</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "📊 Dashboard":
    hoje_br = date.today().strftime("%A, %d de %B").capitalize()
    st.markdown(f"<h2 style='margin-bottom:2px;color:#e8ecff'>Painel de Desempenho</h2><p style='color:#6b7a9e;margin-bottom:20px'>{hoje_br}</p>", unsafe_allow_html=True)

    d = calc_dashboard()

    # Banner
    msg = (f"🔥 {d['streak']} dias seguidos! Modo aprovação ativado!" if d["streak"] >= 7
           else f"{d['total_h']}h estudadas · {d['taxa']}% de acerto geral" if d["total_h"] > 0
           else "Nenhuma sessão ainda — comece hoje! 🚀")
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#2a3578,#3040a0,#4050c0);border-radius:14px;padding:20px 24px;margin-bottom:20px;border:1px solid rgba(91,124,253,.3);position:relative;overflow:hidden'>
      <div style='font-size:18px;font-weight:700;color:#fff;margin-bottom:3px'>Bom estudo, Candidato! 👋</div>
      <div style='font-size:12.5px;color:rgba(255,255,255,.65)'>{msg}</div>
      <div style='position:absolute;right:20px;bottom:-5px;font-size:58px;opacity:.18'>🎯</div>
    </div>""", unsafe_allow_html=True)

    # Métricas
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("⏱️ Horas Totais",    f"{d['total_h']}h")
    c2.metric("✅ Taxa de Acerto",  f"{d['taxa']}%")
    c3.metric("📝 Questões",        d["total_q"])
    c4.metric("🔥 Dias Seguidos",   d["streak"])
    c5.metric("📅 Horas Hoje",      f"{d['h_hj']}h")
    c6.metric("📆 Horas Semana",    f"{d['h_sem']}h")

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:14px'>📈 Horas de Estudo — 14 dias</div>", unsafe_allow_html=True)
        evo = d["evo"]
        dts = list(evo.keys())
        vals = [evo[k] for k in dts]
        labels = [k[5:].replace("-", "/") for k in dts]
        max_v = max(vals) if any(v > 0 for v in vals) else 1
        bars_html = "<div style='display:flex;align-items:flex-end;gap:4px;height:90px;margin-top:8px'>"
        for lbl, v in zip(labels, vals):
            pct = max(v / max_v * 100, v > 0 and 5 or 0)
            color = "linear-gradient(180deg,#7b96ff,#5b7cfd)" if v > 0 else "#2d3561"
            bars_html += f"""<div style='flex:1;display:flex;flex-direction:column;align-items:center;gap:3px'>
              <div style='width:100%;height:{pct}%;background:{color};border-radius:3px 3px 0 0;min-height:3px'></div>
              <div style='font-size:8px;color:#6b7a9e'>{lbl}</div></div>"""
        bars_html += "</div>"
        st.markdown(bars_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        streak_msg = ("Estude hoje para iniciar!" if d["streak"] == 0
                      else "Ótimo começo! Continue!" if d["streak"] < 3
                      else "Pegando ritmo! 🔥" if d["streak"] < 7
                      else "Sequência de campeão! 💪" if d["streak"] < 14
                      else "Imparável! 🏆")
        st.markdown(f"""
        <div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px;text-align:center;height:100%'>
          <div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:14px;text-align:left'>🔥 Sequência</div>
          <div style='font-size:28px;margin-bottom:4px'>🔥</div>
          <div style='font-size:48px;font-weight:800;background:linear-gradient(135deg,#f5a623,#f56565);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1'>{d['streak']}</div>
          <div style='font-size:11px;color:#6b7a9e;margin-top:3px'>dias consecutivos</div>
          <div style='font-size:12px;color:#a0aac8;margin-top:10px'>{streak_msg}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela por matéria
    if d["pm"]:
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:14px'>📚 Desempenho por Matéria</div>", unsafe_allow_html=True)
        rows = []
        for m, r in sorted(d["pm"].items(), key=lambda x: x[1]["horas"], reverse=True):
            tot = r["acertos"] + r["erros"]
            taxa_str = f"{r['taxa']}%" if tot > 0 else "—"
            prog = "🟢" if r["taxa"] >= 70 else "🟡" if r["taxa"] >= 50 else "🔴" if tot > 0 else "⚪"
            rows.append({"Matéria": m, "Horas": f"{r['horas']}h", "Questões": tot, "Acerto": taxa_str, "Status": prog})
        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Sessões recentes
    if d["recentes"]:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:14px'>🕒 Últimas Sessões</div>", unsafe_allow_html=True)
        for s in d["recentes"]:
            dt  = datetime.fromisoformat(s["data_inicio"]).strftime("%d/%m %H:%M")
            dur = f"{s.get('duracao_min',0)}min" if s.get("duracao_min",0) < 60 else f"{s.get('duracao_min',0)/60:.1f}h"
            q   = s.get("acertos", 0) + s.get("erros", 0)
            q_str = f" · {s['acertos']}/{q} acertos" if q > 0 else ""
            enc = " · <span style='color:#4ac98a'>✓ Concluído</span>" if s.get("encerrou_assunto") else ""
            ico = "🧩" if s.get("tipo") == "questoes" else "📖"
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:11px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.05)'>
              <div style='width:34px;height:34px;border-radius:9px;background:rgba(91,124,253,.14);display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0'>{ico}</div>
              <div>
                <div style='font-size:12.5px;font-weight:600;color:#e8ecff'>{s['materia']} · <span style='font-weight:400'>{s['conteudo']}</span></div>
                <div style='font-size:11px;color:#6b7a9e'>{dt} · {dur}{q_str}{enc}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ESTUDAR
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🎯 Estudar":
    st.markdown("<h2 style='margin-bottom:2px;color:#e8ecff'>Iniciar Estudo</h2><p style='color:#6b7a9e;margin-bottom:20px'>Algoritmo de revisão espaçada + peso edital</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        modo = st.radio("Modo", ["📖 Estudar Matéria", "🧩 Resolver Questões"], horizontal=True, key="modo_est")
    with c2:
        plano = st.radio("Plano", ["📋 Pré-Edital", "⚡ Pós-Edital Turbo"], horizontal=True, key="plano_est")

    modo_key  = "questoes" if "Questões" in modo else "materia"
    turbo_key = "Turbo" in plano

    sug = sugerir(modo_key, turbo_key)
    if not sug:
        st.warning("Nenhuma matéria cadastrada. Vá até **📚 Matérias** e importe uma planilha CSV.")
    else:
        prio_labels = {1: "🔴 Alta", 2: "🟡 Média", 3: "⚪ Baixa"}
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#2a3578,#1e2a60 60%,#232b52);border:1px solid rgba(91,124,253,.35);border-radius:14px;padding:24px;margin:16px 0;position:relative;overflow:hidden'>
          <div style='position:absolute;top:-50px;right:-40px;width:160px;height:160px;background:radial-gradient(circle,rgba(91,124,253,.18) 0%,transparent 70%)'></div>
          <div style='font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:#7b96ff;margin-bottom:7px'>📌 Sugestão do Sistema</div>
          <div style='font-size:22px;font-weight:700;color:#fff;margin-bottom:5px'>{sug['materia']}</div>
          <div style='font-size:13px;color:#a0aac8;margin-bottom:14px'>{sug['conteudo']}</div>
          <div style='display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px'>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>📋 {sug['questoes_edital']} questões no edital</span>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>{prio_labels.get(sug['prioridade'], '')}</span>
            <span style='background:rgba(255,255,255,.08);border-radius:20px;padding:3px 11px;font-size:11px;color:#a0aac8'>{'🧩 Questões' if modo_key=='questoes' else '📖 Teoria'}</span>
          </div>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("▶ Registrar esta sessão", key="btn_iniciar"):
                st.session_state["sug_mat"]  = sug["materia"]
                st.session_state["sug_cont"] = sug["conteudo"]
                st.session_state["sug_tipo"] = modo_key
                st.info(f"✅ Matéria selecionada! Vá para **✏️ Registrar** para lançar os dados.")
        with col2:
            if st.button("↻ Nova sugestão", key="btn_nova"):
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='background:#232b50;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:18px'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:14px'>🏆 Ranking de Prioridade</div>", unsafe_allow_html=True)
        for i, item in enumerate(sug["top5"]):
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)'>
              <div style='width:20px;font-size:11px;color:#6b7a9e;font-weight:600'>{i+1}</div>
              <div style='flex:1;font-size:12.5px;color:#a0aac8'>{item['nome']}</div>
              <span style='padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(91,124,253,.14);color:#7b96ff'>{item['score']} pts</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# REGISTRAR
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "✏️ Registrar":
    st.markdown("<h2 style='margin-bottom:2px;color:#e8ecff'>Registrar Sessão</h2><p style='color:#6b7a9e;margin-bottom:20px'>Lançar resultado da bateria de estudos</p>", unsafe_allow_html=True)

    materias = get_materias()
    if not materias:
        st.warning("Nenhuma matéria cadastrada. Vá até **📚 Matérias** primeiro.")
    else:
        with st.form("form_sessao", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tipo = st.selectbox("Tipo de Sessão", ["📖 Estudo de Matéria", "🧩 Resolução de Questões"])
            with c2:
                mat_names = [m["nome"] for m in materias]
                # pré-preenche se vier da sugestão
                def_mat = st.session_state.get("sug_mat", mat_names[0])
                def_idx = mat_names.index(def_mat) if def_mat in mat_names else 0
                mat_sel = st.selectbox("Matéria", mat_names, index=def_idx)

            mat_obj  = next((m for m in materias if m["nome"] == mat_sel), None)
            cont_lst = [c["nome"] for c in mat_obj.get("conteudos", [])] if mat_obj else []
            def_cont = st.session_state.get("sug_cont", "")
            def_ci   = cont_lst.index(def_cont) if def_cont in cont_lst else 0
            conteudo = st.selectbox("Conteúdo", cont_lst if cont_lst else ["Geral"], index=def_ci)

            c1, c2 = st.columns(2)
            with c1:
                data_ini = st.date_input("Data Início", value=date.today())
                hora_ini = st.time_input("Hora Início", value=datetime.now().replace(hour=max(datetime.now().hour-1,0), minute=0, second=0))
            with c2:
                data_fim = st.date_input("Data Fim", value=date.today())
                hora_fim = st.time_input("Hora Fim", value=datetime.now().replace(second=0, microsecond=0))

            acertos = erros = 0
            if "Questões" in tipo:
                c1, c2 = st.columns(2)
                with c1: acertos = st.number_input("✅ Acertos", min_value=0, value=0)
                with c2: erros   = st.number_input("❌ Erros",   min_value=0, value=0)

            encerrou = st.checkbox("Encerrei esse assunto ✓")
            obs = st.text_area("Observações", placeholder="Anotações, dificuldades, dúvidas...")

            if st.form_submit_button("💾 Salvar Sessão", use_container_width=True):
                dt_ini = datetime.combine(data_ini, hora_ini)
                dt_fim = datetime.combine(data_fim, hora_fim)
                dur    = max(int((dt_fim - dt_ini).total_seconds() / 60), 0)
                sessoes = get_sessoes()
                sessoes.append({
                    "id": datetime.now().isoformat(),
                    "materia": mat_sel, "conteudo": conteudo,
                    "tipo": "questoes" if "Questões" in tipo else "materia",
                    "data_inicio": dt_ini.isoformat(), "data_fim": dt_fim.isoformat(),
                    "duracao_min": dur, "encerrou_assunto": encerrou,
                    "acertos": int(acertos), "erros": int(erros), "observacoes": obs,
                })
                save_json(SESSOES_FILE, sessoes)
                # limpa sugestão pré-carregada
                for k in ("sug_mat", "sug_cont", "sug_tipo"):
                    st.session_state.pop(k, None)
                st.success(f"✅ Sessão de {dur}min salva com sucesso!")

# ══════════════════════════════════════════════════════════════════════════════
# MATÉRIAS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "📚 Matérias":
    st.markdown("<h2 style='margin-bottom:2px;color:#e8ecff'>Gestão de Matérias</h2><p style='color:#6b7a9e;margin-bottom:20px'>Edital, conteúdos e prioridades</p>", unsafe_allow_html=True)

    # ── Modelo CSV para download
    modelo_rows = [
        ["materia", "conteudo", "prioridade"],
        ["Direito Constitucional", "Princípios Fundamentais", 1],
        ["Direito Constitucional", "Direitos e Garantias", 1],
        ["Direito Constitucional", "Organização do Estado", 2],
        ["Direito Administrativo", "Atos Administrativos", 1],
        ["Direito Administrativo", "Licitações e Contratos", 1],
        ["Língua Portuguesa", "Interpretação de Texto", 1],
        ["Língua Portuguesa", "Gramática", 2],
        ["Raciocínio Lógico", "Proposições Lógicas", 1],
        ["Informática", "Segurança da Informação", 1],
    ]
    buf = io.StringIO()
    csv.writer(buf).writerows(modelo_rows)
    csv_bytes = buf.getvalue().encode("utf-8-sig")

    c1, c2 = st.columns([1, 1])
    with c1:
        arquivo = st.file_uploader("📤 Importar Planilha CSV", type=["csv"], help="Use o modelo ao lado")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("⬇ Baixar Modelo CSV", csv_bytes, "modelo_materias.csv", "text/csv")

    # ── Upload + configuração
    if arquivo:
        content = arquivo.read().decode("utf-8-sig")
        reader  = csv.DictReader(io.StringIO(content))
        md = {}
        for row in reader:
            nome = row.get("materia", "").strip()
            cont = row.get("conteudo", "").strip()
            prio = int(row.get("prioridade", 2) or 2)
            if not nome: continue
            if nome not in md:
                md[nome] = {"nome": nome, "prioridade": prio, "questoes_edital": 10, "conteudos": []}
            if cont:
                md[nome]["conteudos"].append({"nome": cont, "prioridade": prio})
            if prio < md[nome]["prioridade"]:
                md[nome]["prioridade"] = prio

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:13px;font-weight:700;color:#e8ecff;margin-bottom:12px'>⚙️ Configure questões do edital e prioridade</div>", unsafe_allow_html=True)

        materias_novas = list(md.values())
        with st.form("form_import"):
            for i, m in enumerate(materias_novas):
                cc1, cc2, cc3 = st.columns([3, 1, 1])
                with cc1:
                    st.markdown(f"<div style='padding:8px 0;font-size:13px;color:#a0aac8'>{m['nome']}</div>", unsafe_allow_html=True)
                with cc2:
                    prio_opt = ["🔴 Alta (1)", "🟡 Média (2)", "⚪ Baixa (3)"]
                    p_idx = m["prioridade"] - 1
                    p_sel = st.selectbox("Prioridade", prio_opt, index=p_idx, key=f"p_{i}", label_visibility="collapsed")
                    materias_novas[i]["prioridade"] = prio_opt.index(p_sel) + 1
                with cc3:
                    q = st.number_input("Questões", min_value=0, value=m["questoes_edital"], key=f"q_{i}", label_visibility="collapsed")
                    materias_novas[i]["questoes_edital"] = int(q)

            if st.form_submit_button("✅ Salvar Matérias", use_container_width=True):
                save_json(MATERIAS_FILE, materias_novas)
                st.success(f"✅ {len(materias_novas)} matérias salvas!")
                st.rerun()

    # ── Listagem atual
    materias = get_materias()
    if materias:
        st.markdown("<br>", unsafe_allow_html=True)
        import pandas as pd
        rows = []
        for m in materias:
            prio_str = {1: "🔴 Alta", 2: "🟡 Média", 3: "⚪ Baixa"}.get(m.get("prioridade", 2), "—")
            rows.append({"Matéria": m["nome"], "Prioridade": prio_str, "Questões Edital": m.get("questoes_edital", 0),
                         "Conteúdos": len(m.get("conteudos", []))})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma matéria cadastrada ainda. Importe um CSV acima.")

# ══════════════════════════════════════════════════════════════════════════════
# HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "🗂️ Histórico":
    st.markdown("<h2 style='margin-bottom:2px;color:#e8ecff'>Histórico de Sessões</h2><p style='color:#6b7a9e;margin-bottom:20px'>Todos os seus registros de estudo</p>", unsafe_allow_html=True)
    sessoes = get_sessoes()
    if not sessoes:
        st.info("Nenhuma sessão registrada ainda.")
    else:
        import pandas as pd
        rows = []
        for s in reversed(sessoes):
            dt  = datetime.fromisoformat(s["data_inicio"]).strftime("%d/%m/%Y %H:%M")
            dur = f"{s.get('duracao_min',0)}min" if s.get("duracao_min", 0) < 60 else f"{s.get('duracao_min',0)/60:.1f}h"
            q   = s.get("acertos", 0) + s.get("erros", 0)
            pct = round(s.get("acertos", 0) / q * 100) if q > 0 else None
            rows.append({
                "Data": dt,
                "Matéria": s.get("materia", ""),
                "Conteúdo": s.get("conteudo", ""),
                "Tipo": "🧩 Questões" if s.get("tipo") == "questoes" else "📖 Estudo",
                "Duração": dur,
                "Resultado": f"{s.get('acertos',0)}/{q} ({pct}%)" if q > 0 else "—",
                "Encerrou": "✓" if s.get("encerrou_assunto") else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Export
        buf2 = io.StringIO()
        pd.DataFrame(rows).to_csv(buf2, index=False)
        st.download_button("⬇ Exportar CSV", buf2.getvalue().encode("utf-8-sig"), "historico_sessoes.csv", "text/csv")
