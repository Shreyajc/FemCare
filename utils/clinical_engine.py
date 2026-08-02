import re


# -----------------------------
# Extraction Functions
# -----------------------------

def extract_number(text, keywords):

    text = text.lower()

    for keyword in keywords:

        patterns = [

            rf"{keyword}\s*(?:level)?\s*(?:is|=|:)?\s*(\d+)",

            rf"{keyword}\s*(\d+)/10",

            rf"{keyword}\D*(\d+)",

            rf"(\d+)/10\s*{keyword}",

        ]

        for pattern in patterns:

            match = re.search(pattern, text)

            if match:
                value = int(match.group(1))

                if 0 <= value <= 10:
                    return value

    return None


def extract_sleep(text):

    patterns = [

        r"slept\s*(\d+)",

        r"sleep(?:ing)?(?:\s*hours?)?\s*(?:is|=|:)?\s*(\d+)",

        r"(\d+)\s*hours?\s*of\s*sleep",

        r"sleep\s*(\d+)"

    ]

    for pattern in patterns:

        match = re.search(pattern, text.lower())

        if match:

            return int(match.group(1))

    return None


def extract_flow(text):

    t = text.lower()

    if "heavy" in t:
        return "Heavy"

    if "moderate" in t:
        return "Moderate"

    if "light" in t:
        return "Light"

    return None


def extract_pcos(text):

    t = text.lower()

    phrases = [

        "i have pcos",

        "diagnosed with pcos",

        "pcos yes",

        "pcos: yes",

        "pcos = yes"

    ]

    return any(p in t for p in phrases)


# -----------------------------
# Clinical Engine
# -----------------------------

def analyze(text):

    pain = extract_number(text, ["pain"])

    stress = extract_number(text, ["stress"])

    sleep = extract_sleep(text)

    flow = extract_flow(text)

    has_pcos = extract_pcos(text)

    findings = []

    recommendations = []

    score = 0

    pain_status = None
    stress_status = None
    sleep_status = None

    # ---------------- Pain ----------------

    if pain is not None:

        if pain <= 3:
            pain_status = "🟢 Mild"

        elif pain <= 6:
            pain_status = "🟡 Moderate"
            score += 1

        else:
            pain_status = "🔴 Severe"
            score += 2
            findings.append("Severe menstrual pain reported.")
            recommendations.append("Persistent severe pain should be evaluated by a gynecologist.")

    # ---------------- Stress ----------------

    if stress is not None:

        if stress <= 3:
            stress_status = "🟢 Low"

        elif stress <= 6:
            stress_status = "🟡 Moderate"
            score += 1

        else:
            stress_status = "🔴 High"
            score += 2
            findings.append("High stress may worsen menstrual symptoms.")
            recommendations.append("Stress management techniques may help reduce symptom severity.")

    # ---------------- Sleep ----------------

    if sleep is not None:

        if sleep < 6:
            sleep_status = "🔴 Inadequate"
            score += 1
            findings.append("Insufficient sleep may increase pain perception.")
            recommendations.append("Aim for 7–9 hours of sleep.")

        else:
            sleep_status = "🟢 Adequate"

    # ---------------- Flow ----------------

    if flow == "Heavy":

        score += 2

        findings.append("Heavy menstrual flow reported.")

        recommendations.append("Monitor heavy bleeding and seek medical advice if persistent.")

    # ---------------- PCOS ----------------

    if has_pcos:

        score += 2

        findings.append("History of PCOS reported.")

        recommendations.append("Continue regular follow-up for PCOS management.")

    # ---------------- Risk ----------------

    if score <= 2:

        risk = "🟢 Low"

    elif score <= 5:

        risk = "🟡 Moderate"

    else:

        risk = "🔴 High"

    # ---------------- Clinical Report ----------------

    report = f"""
Clinical Assessment

Pain: {pain_status or "Not Provided"}

Stress: {stress_status or "Not Provided"}

Sleep: {sleep_status or "Not Provided"}

Flow: {flow or "Not Provided"}

PCOS: {"Present" if has_pcos else "Not Reported"}

Overall Risk: {risk}

Key Findings:
{chr(10).join("- " + x for x in findings) if findings else "- No significant clinical concerns detected."}

Recommendations:
{chr(10).join("- " + x for x in recommendations) if recommendations else "- Continue maintaining a healthy lifestyle."}
"""

    return {

        "report": report,

        "pain": pain_status,

        "stress": stress_status,

        "sleep": sleep_status,

        "flow": flow,

        "pcos": has_pcos,

        "risk": risk,

        "findings": findings,

        "recommendations": recommendations

    }