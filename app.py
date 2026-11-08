import html
import re
import streamlit as st

st.set_page_config(page_title="Cervical Spondylosis Decision Support", page_icon="🩺", layout="wide")

# ------------------------------------------------------------------ THEME
st.markdown("""
<style>
.block-container{padding-top:1rem;max-width:1300px}
.hdr{background:linear-gradient(90deg,#0b6e99,#14a3a3);color:#fff;padding:16px 22px;border-radius:10px;margin-bottom:14px}
.hdr h1{color:#fff;font-size:22px;margin:0}.hdr p{color:#e6f6f6;margin:2px 0 0;font-size:13px}
.card{background:#fff;color:#1b2430;border:1px solid #d5e3ea;border-left:5px solid #0b6e99;border-radius:8px;padding:12px 16px;margin-bottom:12px}
.card h3{color:#0b6e99;font-size:15px;margin:0 0 8px}
.card li,.card td,.card th,.card div,.card span{color:#1b2430}
.card table{width:100%;border-collapse:collapse;font-size:13px}
.card th{background:#eaf4f8;text-align:left;padding:6px;border-bottom:1px solid #d5e3ea}
.card td{padding:6px;border-bottom:1px solid #eef2f5;vertical-align:top}
.kv{display:inline-block;min-width:200px;margin:0 8px 8px 0;padding:6px 10px;background:#f3f9fb;border:1px solid #d5e3ea;border-radius:6px}
.kv small{display:block;color:#5d6b7c}.kv b{font-size:15px}
.bd{display:inline-block;font-size:11px;font-weight:600;padding:0 6px;border-radius:8px;background:#eaf4f8;border:1px solid #b9d3df;color:#0b6e99}
.bd.cs{background:#fff3c4;border-color:#e6cf70;color:#6b5600}
.ok{background:#e6f6ee;border:1px solid #9fd8b8;color:#14663a;padding:10px 14px;border-radius:8px;font-weight:600;margin-bottom:8px}
.er{background:#fdecea;border:1px solid #f0aaa4;color:#9b1c14;padding:10px 14px;border-radius:8px;font-weight:600;margin-bottom:8px}
.wn{color:#8a5200}.mu{color:#5d6b7c;font-size:12px}
</style>
<div class="hdr"><h1>🩺 Cervical Spondylosis: Clinical Decision Support</h1>
<p>Rule-based support system. Decision support only; the treating clinician decides.</p></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ KNOWLEDGE BASE
# Evidence level of every rule: G APTA CPG, R trial/review, T textbook, C consensus, S system/safety
LV = {**{f"V{i}": "S" for i in range(1, 11)},
      "D1": "S", "D2": "S", "D3": "S", "D4a": "G", "D4b": "G", "D5": "R", "D6": "R", "D7": "R",
      "D8": "C", "D9": "T", "D10": "C", "D11": "T",
      "R1": "G", "R2": "S", "R3": "R", "R4": "C", "R5": "C", "R6": "C", "R7": "C",
      "X1": "T", "X2": "T", "X3": "T", "X4": "C", "X5": "C", "X6": "C", "X7": "C", "X8": "C",
      "X9": "T", "X10": "T", "X11": "C", "X12": "C", "X13": "C", "M1": "T", "M2": "T",
      "T1": "G/T", "T2": "T", "T3": "T", "T4": "G", "T5": "G/T", "T6a": "R", "T6b": "R", "T6c": "C",
      "T7": "T/G", "T8": "T/G", "T9": "T", "T10a": "R/T", "T10b": "C", "T11": "T", "T12": "T",
      "T13": "C", "T14a": "R", "T14b": "R", "Q1": "G/R/T", "Q2": "C", "Q3": "S",
      "RV1": "S", "RV2": "R", "RV3": "C", "RV4": "C", "RV5": "S", "RV6": "C", "RV7": "S"}

LEGEND = {"G": "Directly supported by the APTA Neck Pain CPG (Blanpied 2017)",
          "R": "Named trial, systematic review or clinical prediction study",
          "T": "Standard textbook teaching (Maitland, Kisner & Colby, Kendall, etc.)",
          "C": "Clinical reasoning or consensus; needs expert-panel validation",
          "S": "System, safety or data-quality rule"}

def meaning(lvl):
    return "; ".join(f"{k}: {LEGEND[k]}" for k in re.findall(r"\b[GRTCS]\b", lvl))

# key: (technique, dose, duration/frequency, level and source)   † = needs validation
DOSE = {
 "AROM": ("Pain-free AROM", "Within comfort; 5-10 reps, several times a day †", "Acute phase; progress when NPRS 3 or less", "G/T. CPG; Maitland; Cameron"),
 "ISO": ("Neck isometrics", "About 30-50% effort; 5-10 s holds x 5-10 reps †", "1-2 times a day until NPRS 3 or less †", "T. Kisner & Colby; Maitland"),
 "STR": ("Static stretching", "30 s hold x 3 per muscle", "Daily †; re-measure ROM every 2 weeks", "G/T. Kisner & Colby; Kendall; Kaltenborn"),
 "DNF": ("Deep neck flexor training", "Pressure feedback: baseline, +2 mmHg steps, 10 s holds x 10, then endurance holds", "6 weeks; 8-12 supervised treatments of 30 min or less; home twice daily", "R. Jull 2002; Jull & Falla"),
 "STG": ("Progressive strengthening (neck and scapular)", "2-3 sets x 8-12 reps", "Chronic: 2-3 times a week, home allowed; Ylinen 2003: home 3 times a week over 12 months", "T/G. Kisner & Colby; CPG; Ylinen 2003"),
 "END": ("Endurance training", "Low load, long holds or high reps †; dynamic head lifts supine and prone", "2-3 times a week; up to 12 months in trial", "G. CPG; Ylinen 2003"),
 "SCP": ("Scapular strengthening", "2-3 sets x 10-15", "2-3 times a week", "T/G. Kendall; Page (Janda); CPG"),
 "THO": ("Thoracic extension mobility", "10 reps x 1-2 sets †", "Daily †", "T. Dutton; Page (Janda)"),
 "NEU": ("Neural sliders / tensioners", "5-10 reps x 2-3 sets, symptoms mild or less", "Daily; re-test the Wainner cluster each review", "R/T. Butler; Basson 2017; CPG"),
 "BAL": ("Balance training (age 66 or more)", "Short, supervised, progressive †", "2-3 times a week †", "T. Kisner & Colby"),
 "AER": ("Aerobic activity", "About 150 min a week, graded", "Ongoing", "T. ACSM; Kisner & Colby"),
 "ERG": ("Ergonomics and micro-breaks", "Break every 30-60 min †", "Ongoing", "C. Chen 2018"),
 "MOB": ("Cervical mobilization (Maitland)", "", "Per session", "T. Maitland; Kaltenborn"),
 "TRC": ("Traction (optional)", "About 15 min, about 15 degrees flexion, intermittent; start about 10% body weight or comfort-adjusted", "2-3 times a week for about 4 weeks", "R (mixed). Fritz 2014; Young 2009"),
 "COL": ("Semi-hard collar", "Semi-hard, worn in the day with rest", "About 3 weeks, then wean (up to 6)", "G. Kuijper 2009"),
}
LOWEND = {"AROM", "ISO", "STR", "DNF", "STG"}   # Q2: high irritability -> lower end, once daily

WAINNER_ITEMS = ["ULTT-A", "Spurling-A", "Distraction", "Ipsilateral rotation <60°"]
COOK_ITEMS = ["Gait deviation", "+Hoffmann", "Inverted supinator", "+Babinski"]

# ------------------------------------------------------------------ RULE ENGINE
def run(v):
    o = {"err": [], "warn": [], "audit": [], "stop": False, "d": [], "ref": [], "res": [], "T": [], "rv": [],
         "decision": ""}
    log = lambda r, t: o["audit"].append((r, t))

    if v["age"] < 18: o["err"].append(("V1", "Age must be a number of 18 or more."))
    if not 0 <= v["nprs"] <= 10: o["err"].append(("V2", "NPRS must be 0-10."))
    if not 0 <= v["ndi"] <= 50: o["err"].append(("V3", "NDI must be 0-50."))
    pc = sum([v["pN"], v["pF"], v["pR"], v["pK"]])
    if pc == 0: o["err"].append(("V5", "Tick at least one posture option."))
    elif v["pN"] and pc > 1: o["err"].append(("V6", "Normal cannot be combined with another posture."))
    # V10 (new system rule): several tension tests may be positive, but Negative cannot be combined with a positive one
    if "Negative" in v["ultt"] and len(v["ultt"]) > 1:
        o["err"].append(("V10", "Upper-limb tension test: Negative cannot be combined with a positive test."))
    if v["nprs"] == 0 and v["ndi"] >= 25: o["warn"].append(("V7", "Severe disability with no pain; check the data entry."))
    if v["dist"] == "Radiating" and v["rad"] <= 1: o["warn"].append(("V8", "Radiating pain with an unlikely Wainner cluster; recheck the tests."))
    if "Not Identified" in v["root"] and len(v["root"]) > 1:
        o["warn"].append(("V10", "Root level: 'Not Identified' selected together with specific roots; check the entry."))
    if o["err"]:
        for r, t in o["err"]: log(r, "REJECT: " + t)
        log("V9", "Run ended at layer 0.")
        return o

    # ---- Layer 1: derived values
    age, nprs, ndi, bmi, rad, myel = v["age"], v["nprs"], v["ndi"], v["bmi"], v["rad"], v["myel"]
    ultt_pos = [x for x in v["ultt"] if x != "Negative"]
    ap = v["ap"] == "Yes"
    d = {}
    d["Age band"] = ("18-35" if age <= 35 else "36-50" if age <= 50 else "51-65" if age <= 65 else "66+", "D1")
    d["NPRS category"] = ("None" if nprs == 0 else "Mild" if nprs <= 3 else "Moderate" if nprs <= 6 else "Severe", "D2")
    d["NDI category"] = ("None" if ndi <= 4 else "Mild" if ndi <= 14 else "Moderate" if ndi <= 24 else "Severe" if ndi <= 34 else "Complete", "D3")
    if bmi < 18.5: bc = "Underweight"
    elif ap: bc = "Normal" if bmi < 23 else "Overweight" if bmi < 25 else "Obese"
    else: bc = "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
    d["BMI category"] = (bc, "D4b" if ap else "D4a")
    d["Wainner positives"] = (f"{rad}/4: " + (", ".join(v["wainner"]) or "none"), "D5")
    d["Radiculopathy (Wainner)"] = (["Unlikely", "Unlikely", "Indeterminate", "Likely", "Highly likely"][rad], "D5")
    mt = myel + (1 if age > 45 else 0)
    d["Cook items positive"] = (", ".join(v["cook"] + (["Age > 45"] if age > 45 else [])) or "none", "D6")
    d["Cook total (0-5)"] = (str(mt), "D6")
    d["Myelopathy category"] = ("Unlikely" if mt == 0 else "Indeterminate" if mt <= 2 else "Likely", "D7")
    ra = v["romAll"]
    d["Overall ROM category"] = ("≥90% (normal)" if ra >= 90 else "75-89%" if ra >= 75 else "50-74%" if ra >= 50 else "<50%", "D8")
    uc = v["pF"] and v["pR"]
    erg = v["occ"] == "Sedentary" or v["sit"] == ">8 h" or v["neckflex"] == "Present"
    fo = v["prov"] in ("Extension", "Rotation")
    d["Upper crossed posture"] = ("Yes" if uc else "No", "D9")
    d["Ergonomic exposure"] = ("Yes" if erg else "No", "D10")
    d["Foraminal closure flag"] = ("Yes" if fo else "No", "D11")
    o["d"] = [(k, a, r) for k, (a, r) in d.items()]
    for k, (a, r) in d.items(): log(r, f"{k} = {a}")

    # ---- Layer 2: referral and safety
    stop = noman = notr = False
    def fire(r, t): o["ref"].append((r, t)); log(r, t)
    if v["red"] == "Present": fire("R1", "STOP: refer urgently (IFOMPT 2020). No treatment plan."); stop = True
    if v["neuro"] == "Progressive": fire("R2", "STOP: urgent medical or spinal referral. No treatment plan."); stop = True
    if mt >= 3: fire("R3", "STOP: refer for spinal specialist review and imaging. No treatment plan."); stop = True
    if 1 <= mt <= 2 and myel >= 1:
        fire("R4", "Complete the myelopathy screen before any manual therapy or traction."); noman = notr = True
    if v["neuro"] in ("Motor", "Reflex"):
        fire("R5", "Arrange medical or spinal review; monitor neurology each visit; traction withheld."); notr = True
    if v["cdi"] == 3:
        fire("R6", "Correlate imaging with clinical findings; traction and end-range techniques withheld."); notr = True
    if d["NDI category"][0] == "Complete": fire("R7", "Consider medical review and psychosocial screening.")
    caut = [r for r, _ in o["ref"] if r in ("R4", "R5", "R6", "R7")]
    if stop:
        o["decision"] = "STOP: REFER, NO TREATMENT PLAN (" + ", ".join(r for r, _ in o["ref"] if r in ("R1", "R2", "R3")) + ")"
    elif caut:
        o["decision"] = "CONTINUE WITH REFERRAL CAUTIONS (" + ", ".join(caut) + ")"
    else:
        o["decision"] = "CONTINUE: no referral rule fired"
    o["stop"] = stop
    if stop: return o

    # ---- Layer 3: restrictions (cumulative, lowest cap wins)
    caps = []
    def add(r, t, c=None):
        o["res"].append((r, t)); log(r, t)
        if c is not None: caps.append(c)
    high = v["irr"] == "High"
    sev = d["NPRS category"][0] == "Severe"
    icap = 2 if high else 3 if v["irr"] == "Moderate" else 4
    add("X1", f"Irritability {v['irr']}: grade cap {['', 'I', 'II', 'III', 'IV'][icap]}", icap)
    if v["dur"] == "Acute": add("X2", "Acute phase: grade cap III", 3)
    if age >= 66 or sev: add("X3", "Age 66+ or severe NPRS: grade cap II", 2)
    notrust = False
    if v["comorb"] == "Osteoporosis": add("X4", "Osteoporosis: cap II; no thrust; no traction", 2); notrust = notr = True
    if v["comorb"] == "Anticoagulant": add("X5", "Anticoagulant / bleeding disorder: cap II; no thrust; no traction", 2); notrust = notr = True
    if v["comorb"] == "Inflammatory Arthropathy": add("X6", "Inflammatory arthropathy: cap II; no traction; no end-range in any direction", 2); notr = True
    if noman: add("X7", "No manual therapy pending myelopathy screen: cap 0", 0)
    if notrust: add("X8", "Exclude all thrust techniques")
    if fo: add("X9", "Avoid end-range extension, ipsilateral rotation and quadrant positions")
    if v["prov"] == "Lateral Flexion": add("X10", "Avoid end-range lateral flexion toward the painful side")
    if high: add("X11", "High irritability: no neural tensioners, no end-range stretching, low-load isometrics only")
    if v["psy"] == "High": add("X12", "High psychosocial risk: emphasise education and graded activity; avoid passive-only care")
    if notr: add("X13", "Traction is not permitted")
    cap = min(caps)
    roman = ["", "I", "II", "III", "IV"]
    if cap >= 1:
        lo = max(1, min(1 if high else 2 if v["irr"] == "Moderate" else 3, cap - 1))
        grade = roman[cap] if lo == cap else f"{roman[lo]}-{roman[cap]}"
        log("M1", f"Mobilization grades {grade}")
    else:
        grade = "None"; log("M2", "Final cap 0: no mobilization listed")
    o["cap"], o["grade"] = cap, grade

    # ---- Layer 4: technique selection
    acute = v["dur"] == "Acute"
    T = []
    def t(k, r, y, why): T.append({"k": k, "r": r, "y": y, "why": why})
    t("AROM", "T1", True, "Always")
    t("ISO", "T2", acute or high, "Acute phase or high irritability")
    t("MOB", "T3", cap >= 1, "Manual therapy allowed after layer 3")
    t("COL", "T4", acute and rad >= 3, "Acute radiculopathy (Wainner 3+)")
    t("STR", "T5", (not acute) and (not high), "Not acute and not high irritability")
    a6 = v["dnf"] == "Impaired" or v["head"] == "Present" or ((not acute) and (not high))
    dnf_on = a6 and ((not acute) or nprs <= 3)
    t("DNF", "T6b" if dnf_on else "T6c", True if dnf_on else ("D" if a6 else False), "DNF impaired, headache, or non-acute")
    t("SCP", "T7", (not acute) or v["pF"] or v["pR"], "Non-acute or forward-head / rounded shoulders")
    t8 = v["dur"] == "Chronic" and not high and not sev
    t("STG", "T8", t8, "Chronic, not high irritability, not severe NPRS")
    t("END", "T8", t8, "Chronic, not high irritability, not severe NPRS")
    t("THO", "T9", v["pK"] or v["pF"] or not acute, "Kyphosis, forward-head or non-acute")
    t("NEU", "T10a", bool(ultt_pos) or rad >= 2, "Any ULTT positive or Wainner 2+")
    t("BAL", "T11", age >= 66, "Age 66+")
    t("AER", "T12", bc in ("Overweight", "Obese"), "BMI overweight or obese")
    t("ERG", "T13", erg or not v["pN"], "Ergonomic exposure or abnormal posture")
    trc = rad >= 3 and not notr and not high and myel == 0 and not sev
    t("TRC", "T14a" if trc else "T14b", trc, "Wainner 3+, no contraindication")

    # ---- Layer 5: dosage
    for x in T:
        x["on"] = x["y"] is True
        name, dose, freq, source = DOSE[x["k"]]
        x["name"] = name
        if x["on"]:
            if x["k"] == "MOB":
                dose = f"Grades {grade}" + ("; avoid end-range in provoking directions" if fo or v["prov"] == "Lateral Flexion" else "")
            if x["k"] == "STR" and uc: dose += "; target: suboccipital, pectorals, upper trapezius, levator"
            if x["k"] == "NEU":
                dose += "; tensioners may be added once sliders are tolerated" if (v["irr"] == "Low" and nprs <= 3) else "; sliders only"
                if ultt_pos: dose += f" (positive test: {', '.join(ultt_pos)})"
            if high and x["k"] in LOWEND:
                dose += " [High irritability: use lower end of the range - Q2]"
                freq = "Once a day (Q2, high irritability). Reference: " + freq
            lvl, _, cite = source.partition(". ")
            x["dose"], x["freq"], x["lvl"], x["cite"] = dose, freq, lvl, cite
            log(x["r"], "Selected: " + name)
        elif x["y"] == "D":
            log("T6c", "Deferred: Deep neck flexor training until NPRS ≤ 3")
        elif x["k"] == "TRC" and rad >= 3:
            log("T14b", "Traction not selected (restriction, irritability, NPRS or myelopathy status)")
    o["T"] = T

    # ---- Layer 6: review (wording uses this patient's values; thresholds unchanged)
    neu = any(x["k"] == "NEU" and x["on"] for x in T)
    rv = [("RV1", f"Re-measure ROM every 2 weeks (CROM device or inclinometer). Baseline overall ROM {ra}% ({d['Overall ROM category'][0]})."),
          ("RV2", f"Re-test the Wainner cluster at each review (baseline {rad}/4, {d['Radiculopathy (Wainner)'][0]})"
                  + ("; re-test before progressing neural work." if neu else ".")),
          ("RV3", f"Current NPRS {nprs:g} is already 3 or less: progress to the next phase or add load at the first review. †" if nprs <= 3
                  else f"Current NPRS {nprs:g}. Progress to the next phase or add load once NPRS is 3 or less at review. †"),
          ("RV4", f"Step back one level if symptoms exceed mild or NPRS rises by 2 or more points (from {nprs:g} to {min(nprs + 2, 10):g} or more). †"),
          ("RV5", f"Repeat the Cook screen (baseline total {mt}/5, {d['Myelopathy category'][0]}) and the neurological check (baseline: {v['neuro']}) at every visit; any new motor, reflex or gait change means refer (R2, R3)."),
          ("RV6", f"If there is no meaningful change in NDI (baseline {ndi}) or NPRS (baseline {nprs:g}) by 4-6 weeks, reassess the diagnosis and consider referral. †")]
    if any(x["y"] == "D" for x in T):
        rv.append(("T6c", "Deep neck flexor training is deferred: check NPRS at each review and start it when NPRS is 3 or less."))
    if noman:
        rv.append(("R4", "Mobilization stays withheld until the myelopathy screen is complete."))
    if v["neuro"] in ("Motor", "Reflex"):
        rv.append(("R5", "Monitor neurology at every visit while the medical or spinal review is arranged."))
    o["rv"] = rv
    log("RV7", "Run completed")
    return o

# ------------------------------------------------------------------ INPUTS (sidebar)
sb = st.sidebar
sb.title("Patient inputs")
v = {}
sb.subheader("Patient")
v["age"] = sb.number_input("Age (years)", 1, 120, 58)
v["sex"] = sb.selectbox("Sex", ["Male", "Female", "Others"])
v["bmi"] = sb.number_input("BMI (kg/m²)", 10.0, 60.0, 27.5, 0.1)
v["ap"] = sb.selectbox("Asia-Pacific BMI bands?", ["No", "Yes"])
v["occ"] = sb.selectbox("Occupation", ["Sedentary", "Manual", "Mixed", "Other"])
v["sit"] = sb.selectbox("Sitting / screen time", ["<4 h", "4-8 h", ">8 h"], index=2)
v["neckflex"] = sb.selectbox("Sustained neck-flexed work", ["Absent", "Present"], index=1)
v["comorb"] = sb.selectbox("Comorbidity", ["None", "Osteoporosis", "Anticoagulant", "Inflammatory Arthropathy", "Other"])

sb.subheader("Symptoms")
v["dur"] = sb.selectbox("Symptom duration", ["Acute", "Subacute", "Chronic"], index=1)
v["nprs"] = sb.number_input("NPRS, 24 h average (0-10)", 0.0, 10.0, 5.0, 0.5)
v["irr"] = sb.selectbox("Irritability", ["Low", "Moderate", "High"], index=1)
v["dist"] = sb.selectbox("Pain distribution", ["Axial", "Referred", "Radiating"], index=2)
v["ndi"] = sb.number_input("NDI (0-50)", 0, 50, 20)
v["head"] = sb.selectbox("Cervicogenic headache", ["Absent", "Present"], index=1)
v["psy"] = sb.selectbox("Psychosocial risk", ["Low", "Moderate", "High"], index=1)

sb.subheader("Neurological")
sb.markdown("**Wainner cluster: tick each positive test**")
v["wainner"] = [n for n, d0 in zip(WAINNER_ITEMS, [True, True, True, False]) if sb.checkbox(n, d0, key="w_" + n)]
v["rad"] = len(v["wainner"])
sb.caption(f"Wainner positives: {v['rad']} of 4")
v["neuro"] = sb.selectbox("Neurological deficit", ["None", "Sensory", "Motor", "Reflex", "Progressive"], index=1)
v["root"] = sb.multiselect("Root level (select one or more)", ["C5", "C6", "C7", "C8", "Not Identified"], default=["C6"]) or ["Not Identified"]
v["ultt"] = sb.multiselect("Upper-limb tension test (select one or more)", ["Negative", "Median", "Radial", "Ulnar"], default=["Median"]) or ["Negative"]
sb.markdown("**Myelopathy screen (Cook cluster): tick each positive clinical sign**")
v["cook"] = [n for n in COOK_ITEMS if sb.checkbox(n, False, key="c_" + n)]
v["myel"] = len(v["cook"])
age_item = v["age"] > 45
sb.caption(f"Age > 45: {'Yes (+1, added automatically)' if age_item else 'No'}. "
           f"Cook total: {v['myel'] + (1 if age_item else 0)} of 5")
v["red"] = sb.selectbox("Red flags / CAD screen", ["Absent", "Present"])

sb.subheader("Movement")
rom = ["Normal", "Painful", "Restricted", "Painful-Restricted"]
v["romF"] = sb.selectbox("ROM flexion", rom, index=1)
v["romE"] = sb.selectbox("ROM extension", rom, index=3)
v["romL"] = sb.selectbox("ROM lateral flexion", rom, index=2)
v["romR"] = sb.selectbox("ROM rotation", rom, index=3)
v["romAll"] = sb.number_input("Overall ROM (% of age-adjusted normal)", 0, 150, 68)
v["prov"] = sb.selectbox("Pain-provoking direction", ["None", "Flexion", "Extension", "Lateral Flexion", "Rotation"], index=2)
v["dnf"] = sb.selectbox("Deep neck flexor performance", ["Adequate", "Impaired"], index=1)
v["cdi"] = sb.selectbox("CDI (0-3)", [0, 1, 2, 3], index=2)

sb.subheader("Posture (Normal cannot combine)")
v["pN"] = sb.checkbox("Normal posture", False)
v["pF"] = sb.checkbox("Forward-head posture", True)
v["pR"] = sb.checkbox("Rounded shoulders", True)
v["pK"] = sb.checkbox("Thoracic hyper-kyphosis", False)

# ------------------------------------------------------------------ OUTPUT HELPERS
def bd(rule):
    lv = LV.get(rule, "-")
    cs = " cs" if lv in ("C", "S") else ""
    return f'<span class="bd{cs}" title="G APTA CPG | R trial/review | T textbook | C consensus | S system">{rule} · {lv}</span>'

def card(num, title, body):
    head = f"{num}. {title}" if num != "" else title
    st.markdown(f'<div class="card"><h3>{head}</h3>{body}</div>', unsafe_allow_html=True)

def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else '<div class="mu">None fired.</div>'

def table(head, rows):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{h}</tr>{b}</table>"

e = html.escape
o = run(v)

# ------------------------------------------------------------------ DASHBOARD
valid = not o["err"]
ran = valid and not o["stop"]
if not valid:
    st.markdown('<div class="er">FIX INPUT ERRORS (Layer 0)</div>', unsafe_allow_html=True)
elif o["stop"]:
    st.markdown('<div class="er">REFER: no treatment plan generated</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="ok">Plan generated</div>', unsafe_allow_html=True)
for r, t in o["err"]: st.error(f"{r}: {t}")
for r, t in o["warn"]: st.warning(f"{r} WARN: {t}")

if valid:
    kv = "".join(f'<div class="kv"><small>{e(k)}</small><b>{e(a)}</b>{bd(r)}</div>' for k, a, r in o["d"])
    summary = (f'<div class="mu">Root level(s): {e(", ".join(v["root"]))} (recorded; no rule uses it). '
               f'Upper-limb tension test: {e(", ".join(v["ultt"]))}.</div>')
    card("", "Derived values (Layer 1)", kv + summary)

def notrun():
    if not valid: return '<div class="mu">Not generated: fix the Layer 0 input errors first.</div>'
    stoppers = ", ".join(r for r, _ in o["ref"] if r in ("R1", "R2", "R3"))
    return f'<div class="mu">Not generated: referral STOP rule fired ({stoppers}).</div>'

# 1. Referral and Safety Decision
if valid:
    cls = "er" if o["stop"] else "ok"
    card(1, "Referral and Safety Decision",
         f'<div class="{cls}">{e(o["decision"])}</div>' + ul([f"<b>{r}</b> {e(t)} {bd(r)}" for r, t in o["ref"]]))
else:
    card(1, "Referral and Safety Decision", notrun())

if ran:
    on = [x for x in o["T"] if x["on"]]
    off = [x for x in o["T"] if not x["on"]]
    # 2. Treatment Restrictions
    card(2, "Treatment Restrictions (cumulative)", ul([f"<b>{r}</b> {e(t)} {bd(r)}" for r, t in o["res"]]))
    # 3. Mobilization Grade Classification
    card(3, "Mobilization Grade Classification",
         f'<div class="kv"><small>Final cap {o["cap"]} (lowest cap wins)</small><b>{o["grade"]}</b>{bd("M1" if o["cap"] >= 1 else "M2")}</div>')
    # 4. Selected Treatment Techniques
    deferred = [x["name"] for x in off if x["y"] == "D"]
    card(4, "Selected Treatment Techniques",
         table(["Technique", "Rule", "Why selected"], [[e(x["name"]), bd(x["r"]), e(x["why"])] for x in on])
         + f'<div class="mu">Not selected: {e(", ".join(x["name"] for x in off if x["y"] != "D")) or "none"}.'
           + (f' Deferred until NPRS ≤ 3: {e(", ".join(deferred))}.' if deferred else "") + "</div>")
    # 5. Treatment Dosage
    card(5, "Treatment Dosage",
         table(["Technique", "Dose"], [[e(x["name"]), e(x["dose"])] for x in on])
         + '<div class="mu">† = suggested starting range; needs validation (Q3).</div>')
    # 6. Duration and Frequency
    card(6, "Duration and Frequency",
         table(["Technique", "Duration / frequency"], [[e(x["name"]), e(x["freq"])] for x in on]))
    # 7. Evidence Level
    card(7, "Evidence Level",
         table(["Technique", "Level", "Meaning", "Source"],
               [[e(x["name"]), f'<b>{e(x["lvl"])}</b>', e(meaning(x["lvl"])), e(x["cite"])] for x in on]))
    # 8. Review and Progression Schedule
    card(8, "Review and Progression Schedule", ul([f"<b>{r}</b> {e(t)} {bd(r)}" for r, t in o["rv"]]))
else:
    for n, title in [(2, "Treatment Restrictions"), (3, "Mobilization Grade Classification"),
                     (4, "Selected Treatment Techniques"), (5, "Treatment Dosage"),
                     (6, "Duration and Frequency"), (7, "Evidence Level"),
                     (8, "Review and Progression Schedule")]:
        card(n, title, notrun())

# 9. Rule Execution Audit Trail
card(9, "Rule Execution Audit Trail (every rule that fired)", ul([f"<b>{r}</b> {e(t)} {bd(r)}" for r, t in o["audit"]]))

st.caption("Badges show rule ID and evidence level: G = APTA CPG, R = trial/review, T = textbook, "
           "C = consensus, S = system (C and S need expert-panel validation). "
           "This tool supports clinical decision-making and does not replace the judgement of the treating clinician.")