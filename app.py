"""
Übungs-App zur Vorbereitung auf die PMP(R)-Zertifizierungsprüfung.
Lädt pmp_question_bank.json und stellt Single-Choice- sowie alle interaktiven
Fragetypen der Prüfung 2026 zum Üben bereit.

PMI, PMP und PMBOK sind eingetragene Marken des Project Management Institute, Inc.
Diese App ist ein eigenständiges Übungsangebot und wird von PMI weder unterstützt
noch geprüft, autorisiert oder zertifiziert.

Start:  streamlit run app.py
"""
import json, random, pathlib, re
import streamlit as st
import streamlit.components.v1 as components

BANK = pathlib.Path(__file__).parent / "pmp_question_bank.json"

RED, TEAL, INK, GREIGE = "#A51B34", "#0D5966", "#211F20", "#E8E5DE"

TRADEMARK_NOTICE = (
    "PMI, PMP, PMBOK und das PMI-Logo sind eingetragene Marken des Project Management Institute, Inc. Diese Übungssammlung ist ein eigenständiges Angebot von Mielke PM Training & Coaching und wird von PMI weder unterstützt noch geprüft, autorisiert oder zertifiziert. Die Fragen sind eigens für diesen Kurs formuliert und sind keine Originalfragen des PMI. (C) Nicole SChelter"
)


def trademark_footer():
    """Markenhinweis - wird auf jeder Seitenansicht ausgegeben."""
    st.divider()
    st.caption(TRADEMARK_NOTICE)


TYPE_LABEL = {
    "single_choice": "Single Choice",
    "multiple_response": "Multiple Response",
    "matching": "Matching",
    "drag_drop": "Drag & Drop",
    "ordering": "Reihenfolge",
    "fill_in_blank": "Lückentext",
    "graphic_interpretation": "Graphic Interpretation",
    "hotspot": "Point & Click",
    "case_study": "Case Study",
}

st.set_page_config(
    page_title="Übungsfragen Projektmanagement-Zertifizierung",
    page_icon="🎓",
    layout="wide",
)


def _qp(name, default=""):
    """Query-Parameter robust lesen (Liste oder String)."""
    v = st.query_params.get(name, default)
    return v[0] if isinstance(v, list) and v else v


def _qp_list(name):
    raw = _qp(name)
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else []


def _qp_flag(name):
    return str(_qp(name)).lower() in ("1", "true", "yes")


# Kompakt-Modus: fuer die Einbettung per iframe (?compact=1 oder ?embed=true)
COMPACT = _qp_flag("compact") or _qp_flag("embed")

if COMPACT:
    st.markdown(
        """<style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
        .block-container {padding-top:1.2rem; padding-bottom:1rem;}
        </style>""",
        unsafe_allow_html=True,
    )


@st.cache_data
def load_bank():
    with open(BANK, encoding="utf-8") as f:
        return json.load(f)


def svg(markup: str, height: int = 300):
    """Rendert Inline-SVG in einem festen Rahmen.

    Ohne explizite width/height am <svg>-Tag skaliert der Browser die Grafik
    je nach verfügbarer Breite unterschiedlich hoch - dadurch konnte sie
    höher werden als der Rahmen und wurde oben/unten abgeschnitten.

    Fix: Wir lesen Breite/Höhe aus dem viewBox-Attribut aus, schreiben sie
    explizit als width/height auf das <svg>-Tag (damit es IMMER in seiner
    festen, nativen Pixelgröße rendert - unabhängig von der Spaltenbreite)
    und setzen die Rahmenhöhe exakt danach. Ist die Grafik breiter als die
    verfügbare Spalte, entsteht dadurch bewusst ein horizontaler
    Scrollbalken statt eines abgeschnittenen Bildes.
    """
    m = re.search(r'viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"', markup)
    if m:
        vb_w, vb_h = float(m.group(1)), float(m.group(2))
        sized_markup = re.sub(
            r"^<svg\s", f'<svg width="{vb_w:g}" height="{vb_h:g}" ', markup, count=1
        )
        frame_height = int(vb_h) + 40
    else:
        sized_markup = markup
        frame_height = height + 20

    block = (
        '<div style="overflow-x:auto; overflow-y:hidden; background:#FBFAF7; '
        'padding:8px; border-radius:6px;">'
        f"{sized_markup}"
        "</div>"
    )
    if hasattr(st, "iframe"):
        st.iframe(block, height=frame_height, width="stretch")
    else:
        components.html(block, height=frame_height, scrolling=False)


# ---------------------------------------------------------------- renderers
def render_single_choice(q, key):
    opts = q["payload"]["options"]
    labels = [f"{o['id'].upper()}) {o['text']}" for o in opts]
    choice = st.radio("Antwort wählen:", labels, index=None, key=key)
    return opts[labels.index(choice)]["id"] if choice else None


def render_multiple_response(q, key):
    opts = q["payload"]["options"]
    hint = q["payload"].get("select_hint", "Mehrfachauswahl möglich")
    st.caption(hint)
    picked = []
    for o in opts:
        if st.checkbox(f"{o['id'].upper()}) {o['text']}", key=f"{key}_{o['id']}"):
            picked.append(o["id"])
    return picked or None


def render_assign(q, key, target_key):
    """matching + drag_drop: one selectbox per item."""
    targets = q["payload"][target_key]
    tmap = {t["text"]: t["id"] for t in targets}
    result = {}
    for it in q["payload"]["items"]:
        pick = st.selectbox(
            it["text"], ["– bitte wählen –"] + list(tmap), key=f"{key}_{it['id']}"
        )
        if pick != "– bitte wählen –":
            result[it["id"]] = tmap[pick]
    return result if len(result) == len(q["payload"]["items"]) else None


def render_ordering(q, key):
    items = q["payload"]["items"]
    imap = {i["text"]: i["id"] for i in items}
    st.caption("Jeder Position genau einen Eintrag zuordnen.")
    seq = []
    for pos in range(len(items)):
        pick = st.selectbox(
            f"Position {pos + 1}", ["– bitte wählen –"] + list(imap), key=f"{key}_{pos}"
        )
        if pick != "– bitte wählen –":
            seq.append(imap[pick])
    if len(seq) != len(items):
        return None
    if len(set(seq)) != len(seq):
        st.warning("Jeder Eintrag darf nur einmal verwendet werden.")
        return None
    return seq


def render_blanks(q, key, show_svg=False):
    if show_svg:
        svg(q["payload"]["svg"], 300)
    if "sentence" in q["payload"]:
        st.markdown(f"> {q['payload']['sentence']}")
    answers = {}
    for b in q["payload"]["blanks"]:
        label = b.get("label", f"Lücke {b['id']}")
        pick = st.selectbox(
            label, ["– bitte wählen –"] + b["options"], key=f"{key}_{b['id']}"
        )
        if pick != "– bitte wählen –":
            answers[b["id"]] = pick
    return answers if len(answers) == len(q["payload"]["blanks"]) else None


def render_hotspot(q, key):
    svg(q["payload"]["svg"], 310)
    regions = q["payload"]["regions"]
    labels = [r["label"] for r in regions]
    pick = st.radio("Bereich wählen:", labels, index=None, key=key)
    return regions[labels.index(pick)]["id"] if pick else None


def render_case_study(q, key):
    st.info(q["payload"]["scenario"])
    answers = {}
    for sub in q["payload"]["subquestions"]:
        st.markdown(f"**{sub['prompt']}**")
        if sub["type"] == "multiple_response":
            picked = [
                o["id"]
                for o in sub["options"]
                if st.checkbox(
                    f"{o['id'].upper()}) {o['text']}", key=f"{key}_{sub['id']}_{o['id']}"
                )
            ]
            if picked:
                answers[sub["id"]] = picked
        else:
            labels = [f"{o['id'].upper()}) {o['text']}" for o in sub["options"]]
            pick = st.radio(
                "Antwort wählen:", labels, index=None, key=f"{key}_{sub['id']}"
            )
            if pick:
                answers[sub["id"]] = sub["options"][labels.index(pick)]["id"]
        st.divider()
    return answers if len(answers) == len(q["payload"]["subquestions"]) else None


def render(q, key):
    t = q["type"]
    if t == "single_choice":
        return render_single_choice(q, key)
    if t == "multiple_response":
        return render_multiple_response(q, key)
    if t == "matching":
        return render_assign(q, key, "targets")
    if t == "drag_drop":
        return render_assign(q, key, "categories")
    if t == "ordering":
        return render_ordering(q, key)
    if t == "fill_in_blank":
        return render_blanks(q, key)
    if t == "graphic_interpretation":
        return render_blanks(q, key, show_svg=True)
    if t == "hotspot":
        return render_hotspot(q, key)
    if t == "case_study":
        return render_case_study(q, key)
    st.error(f"Unbekannter Fragetyp: {t}")
    return None


# ---------------------------------------------------------------- grading
def grade(q, given):
    """Returns (is_correct, list_of_feedback_lines)."""
    t, exp = q["type"], q.get("answer")
    lines = []
    if t == "single_choice":
        ok = given == exp
        for o in q["payload"]["options"]:
            r = q.get("option_rationales", {}).get(o["id"], "")
            mark = "✅" if o["id"] == exp else "❌"
            picked = "  ← Ihre Antwort" if o["id"] == given else ""
            lines.append(f"{mark} **{o['id'].upper()})** {o['text']}{picked}  \n{r}")
        return ok, lines
    if t == "multiple_response":
        ok = set(given or []) == set(exp)
        lines.append(f"Richtig: **{', '.join(a.upper() for a in exp)}**")
        return ok, lines
    if t in ("matching", "drag_drop"):
        tk = "targets" if t == "matching" else "categories"
        tname = {x["id"]: x["text"] for x in q["payload"][tk]}
        ok = given == exp
        for it in q["payload"]["items"]:
            good = (given or {}).get(it["id"]) == exp[it["id"]]
            lines.append(
                f"{'✅' if good else '❌'} {it['text']} → **{tname[exp[it['id']]]}**"
            )
        return ok, lines
    if t == "ordering":
        ok = given == exp
        names = {i["id"]: i["text"] for i in q["payload"]["items"]}
        lines.append("Richtige Reihenfolge:")
        for n, iid in enumerate(exp, 1):
            lines.append(f"{n}. {names[iid]}")
        return ok, lines
    if t in ("fill_in_blank", "graphic_interpretation"):
        ok = given == exp
        for b in q["payload"]["blanks"]:
            good = (given or {}).get(b["id"]) == exp[b["id"]]
            lines.append(
                f"{'✅' if good else '❌'} {b.get('label', b['id'])} → **{exp[b['id']]}**"
            )
        return ok, lines
    if t == "hotspot":
        ok = given == exp
        rname = {r["id"]: r["label"] for r in q["payload"]["regions"]}
        lines.append(f"Richtig: **{rname[exp]}**")
        return ok, lines
    if t == "case_study":
        allok = True
        for sub in q["payload"]["subquestions"]:
            g = (given or {}).get(sub["id"])
            e = sub["answer"]
            good = set(g or []) == set(e) if isinstance(e, list) else g == e
            allok &= good
            shown = ", ".join(x.upper() for x in e) if isinstance(e, list) else e.upper()
            lines.append(f"{'✅' if good else '❌'} {sub['prompt']} → **{shown}**")
            lines.append(f"　{sub['rationale']}")
        return allok, lines
    return False, ["Bewertung für diesen Typ nicht implementiert."]


# ---------------------------------------------------------------- app
bank = load_bank()
questions = bank["questions"]

st.markdown(
    f"<h1 style='color:{INK};margin-bottom:0'>"
    f"Prüfungsvorbereitung PMP&reg;-Zertifizierung — Übungsfragen</h1>"
    f"<p style='color:#6E6A64'>{bank['meta']['standard']} · {bank['meta']['owner']}</p>",
    unsafe_allow_html=True,
)

def start_round(mod, sec, typ, only_interactive, shuffle, limit):
    pool = [
        q
        for q in questions
        if q["module"] in mod and q["section"] in sec and q["type"] in typ
    ]
    if only_interactive:
        pool = [q for q in pool if q["type"] != "single_choice"]
    if shuffle:
        random.shuffle(pool)
    if limit:
        pool = pool[: int(limit)]
    st.session_state.pool = pool
    st.session_state.idx = 0
    st.session_state.results = {}
    st.session_state.checked = {}
    st.session_state.finished = False


def filter_controls(box, prefix):
    """Auswahl-Widgets rendern - in der Seitenleiste oder im Hauptbereich."""
    modules = sorted({q["module"] for q in questions})
    types = sorted({q["type"] for q in questions})

    # Vorbelegung aus URL-Parametern (nur gueltige Werte)
    pre_mod = [m for m in _qp_list("module") if m in modules] or modules
    pre_typ = [t for t in _qp_list("type") if t in types] or types

    with box:
        mod = st.multiselect("Modul", modules, default=pre_mod, key=f"{prefix}_mod")
        secs = sorted({q["section"] for q in questions if q["module"] in mod})
        pre_sec = [x for x in _qp_list("section") if x in secs] or secs
        sec = st.multiselect("Abschnitt", secs, default=pre_sec, key=f"{prefix}_sec")
        typ = st.multiselect(
            "Fragetyp",
            types,
            default=pre_typ,
            format_func=lambda t: TYPE_LABEL.get(t, t),
            key=f"{prefix}_typ",
        )
        c1, c2 = st.columns(2) if prefix == "main" else (st, st)
        only_interactive = c1.checkbox(
            "Nur interaktive Formate", value=_qp_flag("interactive"), key=f"{prefix}_int"
        )
        shuffle = c2.checkbox("Fragen mischen", value=True, key=f"{prefix}_shuf")
        try:
            pre_n = int(_qp("n", "10"))
        except ValueError:
            pre_n = 10
        limit = st.number_input(
            "Anzahl Fragen (0 = alle)", 0, 250, min(pre_n, 250), step=5, key=f"{prefix}_n"
        )
        if st.button(
            "Runde starten / neu mischen",
            type="primary",
            use_container_width=True,
            key=f"{prefix}_go",
        ):
            start_round(mod, sec, typ, only_interactive, shuffle, limit)
        return mod, sec, typ, only_interactive, shuffle, limit


# Automatischer Start bei ?autostart=1 (z. B. fuer eine eingebettete Uebungsseite)
if _qp_flag("autostart") and "pool" not in st.session_state:
    modules = sorted({q["module"] for q in questions})
    types = sorted({q["type"] for q in questions})
    a_mod = [m for m in _qp_list("module") if m in modules] or modules
    a_typ = [t for t in _qp_list("type") if t in types] or types
    a_sec = [s for s in _qp_list("section")] or sorted(
        {q["section"] for q in questions if q["module"] in a_mod}
    )
    try:
        a_n = int(_qp("n", "10"))
    except ValueError:
        a_n = 10
    start_round(a_mod, a_sec, a_typ, _qp_flag("interactive"), True, a_n)

if COMPACT:
    with st.expander("Auswahl", expanded="pool" not in st.session_state):
        filter_controls(st.container(), "main")
        st.caption(f"Fragen gesamt: {bank['meta']['counts']['total']} · "
                   f"davon interaktiv: {bank['meta']['counts']['interactive']}")
else:
    with st.sidebar:
        st.header("Auswahl")
        filter_controls(st.container(), "side")
        st.divider()
        st.caption(f"Fragen gesamt: {bank['meta']['counts']['total']}")
        st.caption(f"davon interaktiv: {bank['meta']['counts']['interactive']}")
        st.divider()
        st.caption(TRADEMARK_NOTICE)

if "pool" not in st.session_state:
    st.info("Oben unter **Auswahl** filtern und **Runde starten** klicken."
            if COMPACT else
            "Links Auswahl treffen und **Runde starten** klicken.")
    trademark_footer()
    st.stop()

pool = st.session_state.pool
st.session_state.setdefault("finished", False)
if not pool:
    st.warning("Keine Fragen für diese Auswahl gefunden.")
    trademark_footer()
    st.stop()

idx = st.session_state.idx
q = pool[idx]
done = len(st.session_state.results)
correct = sum(1 for v in st.session_state.results.values() if v)

c1, c2, c3 = st.columns([3, 1, 1])
c1.progress((idx + 1) / len(pool), text=f"Frage {idx + 1} von {len(pool)}")
c2.metric("Beantwortet", done)
c3.metric("Richtig", f"{correct}/{done}" if done else "–")

st.markdown(
    f"<span style='background:{TEAL};color:#fff;padding:3px 10px;border-radius:10px;font-size:12px'>"
    f"{TYPE_LABEL.get(q['type'], q['type'])}</span>&nbsp;"
    f"<span style='background:{GREIGE};color:{INK};padding:3px 10px;border-radius:10px;font-size:12px'>"
    f"{q['module']} · {q['section']}</span>",
    unsafe_allow_html=True,
)
st.subheader(q["prompt"])

key = f"q_{q['id']}"
given = render(q, key)

b1, b2, b3 = st.columns([1, 1, 4])
if b1.button("Antwort prüfen", key=f"check_{q['id']}", disabled=given is None):
    ok, lines = grade(q, given)
    st.session_state.results[q["id"]] = ok
    st.session_state.checked[q["id"]] = (ok, lines)

# Beim Nachschauen (nach "Beenden") automatisch bewerten, auch wenn die
# Frage vorher nie explizit mit "Antwort prüfen" geprüft wurde.
if (
    st.session_state.finished
    and q["id"] not in st.session_state.checked
    and given is not None
):
    ok, lines = grade(q, given)
    st.session_state.results[q["id"]] = ok
    st.session_state.checked[q["id"]] = (ok, lines)

if q["id"] in st.session_state.checked:
    ok, lines = st.session_state.checked[q["id"]]
    (st.success if ok else st.error)("Richtig!" if ok else "Nicht richtig.")
    with st.container(border=True):
        for ln in lines:
            st.markdown(ln)
        st.markdown(f"**Erläuterung:** {q['rationale']}")
elif st.session_state.finished:
    st.info("Diese Frage wurde nicht beantwortet.")


def _go(delta: int):
    """Callback: läuft vor dem Skript-Rerun, daher ohne st.rerun()."""
    st.session_state.idx = max(0, min(len(pool) - 1, st.session_state.idx + delta))


def _jump(i: int):
    st.session_state.idx = i


nav1, nav2, nav3 = st.columns([1, 1, 4])
nav1.button("◀ Zurück", disabled=idx == 0, on_click=_go, args=(-1,))
nav2.button("Weiter ▶", disabled=idx >= len(pool) - 1, on_click=_go, args=(1,))
if not st.session_state.finished:
    if nav3.button("🏁 Runde beenden & Ergebnis anzeigen", use_container_width=True):
        st.session_state.finished = True
        st.rerun()

if st.session_state.finished or done == len(pool):
    st.session_state.finished = True
    st.divider()
    pct = round(100 * correct / len(pool)) if pool else 0
    st.subheader(f"Runde abgeschlossen: {correct}/{len(pool)} richtig ({pct} %)")
    unanswered = len(pool) - done
    if unanswered:
        st.caption(f"{unanswered} Frage(n) nicht beantwortet.")

    weak = {}
    for qq in pool:
        if not st.session_state.results.get(qq["id"], True):
            weak.setdefault(f"{qq['module']} · {qq['section']}", 0)
            weak[f"{qq['module']} · {qq['section']}"] += 1
    if weak:
        st.markdown("**Schwerpunkte zum Nacharbeiten:**")
        for k, v in sorted(weak.items(), key=lambda x: -x[1]):
            st.markdown(f"- {k} — {v} Fehler")

    st.markdown("**Fragenübersicht – anklicken, um Antwort und Begründung anzusehen:**")
    n_cols = 3 if COMPACT else 6
    cols = st.columns(n_cols)
    for i, qq in enumerate(pool):
        status = st.session_state.results.get(qq["id"])
        if status is True:
            icon = "✅"
        elif status is False:
            icon = "❌"
        else:
            icon = "⚪"
        label = f"{icon} Frage {i + 1}"
        col = cols[i % n_cols]
        col.button(
            label,
            key=f"jump_{qq['id']}",
            on_click=_jump,
            args=(i,),
            use_container_width=True,
            type="primary" if i == idx else "secondary",
        )

    if st.button("🔄 Neue Runde mit gleicher Auswahl starten"):
        st.session_state.idx = 0
        st.session_state.results = {}
        st.session_state.checked = {}
        st.session_state.finished = False
        st.rerun()

trademark_footer()
