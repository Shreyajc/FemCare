from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
TEMPLATE = ROOT / "report" / "phase1" / "FemCare_Phase_1_Report.docx"
OUT = HERE / "FemCare_Phase_2_Report.docx"

BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
PINK = "D53F8C"
PLUM = "7A2E67"
LIGHT_BLUE = "E8EEF5"
LIGHT_PINK = "FCE4EC"
LIGHT_GRAY = "F2F4F7"
TEXT = "30343B"
MUTED = "666666"
WHITE = "FFFFFF"


def rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value)


def set_font(run, name="Times New Roman", size=11, bold=None, italic=None, color=TEXT):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    run.font.color.rgb = rgb(color)


def shade(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=70, start=90, bottom=70, end=90):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        element = tc_mar.find(qn(f"w:{name}"))
        if element is None:
            element = OxmlElement(f"w:{name}")
            tc_mar.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tag = OxmlElement("w:tblHeader")
    tag.set(qn("w:val"), "true")
    tr_pr.append(tag)


def prevent_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def set_table_geometry(table, widths):
    total = sum(widths)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Inches(widths[i] / 1440)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell)


def add_table(doc, headers, rows, widths=None, font_size=8.8, first_col_bold=False):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    repeat_header(table.rows[0])
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        shade(cell, LIGHT_BLUE)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        set_font(p.add_run(str(value)), size=font_size, bold=True, color=DARK_BLUE)
    for row_data in rows:
        row = table.add_row()
        prevent_split(row)
        for index, value in enumerate(row_data):
            p = row.cells[index].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            set_font(p.add_run(str(value)), size=font_size,
                     bold=(first_col_bold and index == 0), color=TEXT)
    if widths is None:
        widths = [9360 // len(headers)] * len(headers)
        widths[-1] += 9360 - sum(widths)
    set_table_geometry(table, widths)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(1)
    return table


def add_para(doc, text="", bold_prefix=None, italic=False, after=6, align=None, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.10
    p.paragraph_format.keep_with_next = keep
    if align is not None:
        p.alignment = align
    if bold_prefix and text.startswith(bold_prefix):
        set_font(p.add_run(bold_prefix), bold=True)
        set_font(p.add_run(text[len(bold_prefix):]), italic=italic)
    else:
        set_font(p.add_run(text), italic=italic)
    return p


def add_bullets(doc, items, level=0):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(0.45 + 0.25 * level)
        p.paragraph_format.first_line_indent = Inches(-0.22)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.08
        set_font(p.add_run(item))


def add_numbered(doc, items):
    for number, item in enumerate(items, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.22)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.08
        set_font(p.add_run(f"{number}. "), bold=True, color=DARK_BLUE)
        set_font(p.add_run(item))


def heading(doc, text, level=1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    return p


def add_figure(doc, path: Path, caption: str, width=6.35):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(path), width=Inches(width))
    shape._inline.docPr.set("descr", caption)
    shape._inline.docPr.set("title", path.stem.replace("_", " "))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_before = Pt(0)
    cap.paragraph_format.space_after = Pt(7)
    set_font(cap.add_run(caption), size=9, italic=True, color=MUTED)


def page_break(doc):
    doc.add_page_break()


def clear_body(doc):
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def field_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_font(paragraph.add_run("Page "), size=9, color=MUTED)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def set_cell_text(cell, text, size=9, bold=False, color=TEXT, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    set_font(p.add_run(text), size=size, bold=bold, color=color)


def add_insight(doc, number, finding, evidence, interpretation):
    heading(doc, f"Insight {number}", 2)
    table = doc.add_table(rows=3, cols=2)
    table.style = "Table Grid"
    labels = [("Finding", finding), ("Evidence", evidence), ("Interpretation", interpretation)]
    for row, (label, value) in zip(table.rows, labels):
        prevent_split(row)
        shade(row.cells[0], LIGHT_BLUE)
        set_cell_text(row.cells[0], label, size=9, bold=True, color=DARK_BLUE)
        set_cell_text(row.cells[1], value, size=9)
    set_table_geometry(table, [1450, 7910])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def style_document(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.10
    for name, size, color in (("Heading 1", 16, BLUE), ("Heading 2", 13, BLUE), ("Heading 3", 11, DARK_BLUE)):
        style = styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = rgb(color)
        style.paragraph_format.space_before = Pt(9 if name == "Heading 1" else 6)
        style.paragraph_format.space_after = Pt(4)
        style.paragraph_format.keep_with_next = True


def build():
    evaluation = pd.read_csv(ASSETS / "phase2_rag_evaluation.csv")
    summary = pd.read_csv(ASSETS / "phase2_rag_summary.csv").set_index("system")
    manifest = json.loads((ASSETS / "knowledge_base_manifest.json").read_text(encoding="utf-8"))

    doc = Document(str(TEMPLATE))
    clear_body(doc)
    style_document(doc)
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.49)
    section.footer_distance = Inches(0.49)
    section.different_first_page_header_footer = True

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()
    set_font(hp.add_run("FemCare AI | Phase 2 Report"), size=9, color=MUTED)
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    field_page_number(fp)

    # Cover
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("PHASE 2 REPORT"), size=24, bold=True, color=BLUE)
    p.paragraph_format.space_after = Pt(14)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("FemCare AI"), size=28, bold=True, color=PLUM)
    p.paragraph_format.space_after = Pt(6)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("LLM–API Data Fusion, Exploratory Analysis\nand Enhanced RAG Evaluation"), size=16, bold=True, color=DARK_BLUE)
    p.paragraph_format.space_after = Pt(18)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run("Parts F–K | Before/After Comparison and LLM Integration"), size=12, italic=True, color=MUTED)
    p.paragraph_format.space_after = Pt(30)
    cover_rows = [
        ("Student", "Shreya Jadhav"),
        ("Roll Number", "MC2525"),
        ("Course", "MCA Semester 3"),
        ("Faculty", "Dr. Anita Chaware"),
        ("Project", "FemCare AI – Menstrual Health Assistant"),
        ("Report Date", "20 September 2026"),
        ("Phase 2 Deadline", "25 September 2026"),
    ]
    table = doc.add_table(rows=len(cover_rows), cols=2)
    table.style = "Table Grid"
    for row, (label, value) in zip(table.rows, cover_rows):
        shade(row.cells[0], LIGHT_BLUE)
        set_cell_text(row.cells[0], label, size=10, bold=True, color=DARK_BLUE)
        set_cell_text(row.cells[1], value, size=10)
        prevent_split(row)
    set_table_geometry(table, [2400, 5200])
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    set_font(p.add_run("Academic prototype • Educational use • Not a diagnostic medical device"),
             size=9, italic=True, color=MUTED)

    page_break(doc)
    heading(doc, "Executive Summary", 1)
    add_para(doc, "Phase 2 converts the Phase 1 fused CSV into searchable evidence for the FemCare AI assistant and measures the improvement. The original comparison system contained general menstrual-health knowledge and an original-dataset summary. The enhanced system used the same Llama 3.2 model and the same TF-IDF retrieval method, but added Census, CDC PLACES, weather, state summaries and 17,976 fused cycle records. This controlled design isolates the effect of data enrichment.")
    add_table(doc, ["Measure", "Before fusion", "After fusion"], [
        ["Searchable documents", f"{manifest['original_index']['documents']:,}", f"{manifest['fused_index']['documents']:,}"],
        ["Fixed questions answered correctly", "5 of 10", "10 of 10"],
        ["Accuracy", "50%", "100%"],
        ["Complete answers", "5 of 10", "10 of 10"],
        ["Unsupported/hallucinated answers", "0", "0"],
        ["Average local response time", f"{summary.loc['Before fusion','average_response_time_seconds']:.1f} s", f"{summary.loc['After fusion','average_response_time_seconds']:.1f} s"],
    ], widths=[3300, 3030, 3030], font_size=9.2)
    add_para(doc, "Main result: The enrichment preserved performance on the five original-domain questions and enabled correct answers to all five questions that required API or fused-data evidence. The larger index increased average local response time by approximately 11.0 seconds. The result demonstrates functional knowledge expansion, but the ten-question test is not clinical validation and should not be generalized beyond the tested dataset.", bold_prefix="Main result:")

    heading(doc, "Scope of This Report", 2)
    add_para(doc, "The attached assignment document is used only to determine the required Phase 2 sections. Project-specific claims in this report come from the saved datasets, source code, generated manifests, EDA outputs and the recorded LLM evaluation.")
    add_table(doc, ["Assignment part", "Evidence supplied in this report"], [
        ["F", "Before/after data comparison, new variables, new analyses and quality effects"],
        ["G", "Seven insights written as Finding → Evidence → Interpretation"],
        ["H", "Fused-data RAG preparation, indexing, retrieval and LLM workflow"],
        ["I", "Five original questions and five fused/API questions with responses and sources"],
        ["J", "Accuracy, completeness, relevance, hallucination and response-time comparison"],
        ["K", "Code, datasets, outputs, execution order, limitations and reproducibility"],
    ], widths=[1300, 8060], first_col_bold=True)

    page_break(doc)
    heading(doc, "Contents", 1)
    add_para(doc, "The report follows the Phase 2 sequence specified in the assignment. Each part is supported by saved project evidence and is followed by reproducibility information.")
    add_table(doc, ["Section", "Focus"], [
        ["Part F", "Before-fusion versus after-fusion dataset comparison"],
        ["Part G", "Seven Finding → Evidence → Interpretation insights"],
        ["Part H", "Fused-data preparation, document creation, indexing, retrieval and LLM use"],
        ["Part I", "Ten-question controlled LLM test with answers, expectations and sources"],
        ["Part J", "Accuracy, completeness, relevance, hallucination and timing comparison"],
        ["Part K", "Code, data, results, validation checklist and run order"],
        ["Closing material", "Limitations, ethics, next steps, conclusion, references and appendices"],
    ], widths=[2100, 7260], font_size=9.3, first_col_bold=True)

    page_break(doc)
    heading(doc, "1. Part F – Before Fusion vs After Fusion", 1)
    heading(doc, "1.1 Dataset Structure", 2)
    add_para(doc, "The original dataset was cycle-level. Fusion kept every original row and attached state-level social and public-health context plus state-capital weather for the cycle start date. The record grain therefore remained one row per user and cycle.")
    add_table(doc, ["Property", "Original dataset", "Final cleaned fused dataset"], [
        ["Rows", "17,976", "17,976"],
        ["Columns", "34", "56"],
        ["Users", "2,000", "2,000"],
        ["States", "50", "50"],
        ["Date range", "1 Jan 2024 to 5 Apr 2025", "Unchanged"],
        ["Duplicate user-cycle keys", "0", "0"],
        ["Missing cells", "5,486", "2,642 (0.262%)"],
        ["Join grain", "Not applicable", "State; and state + cycle start date"],
    ], widths=[2500, 3300, 3560], font_size=9.1)

    heading(doc, "1.2 New Attributes Included", 2)
    add_table(doc, ["Layer", "Added fields", "Reason for inclusion"], [
        ["Census ACS (7)", "State FIPS; total and female population; female ages 20–24, 25–29 and 30–34; median household income", "Adds population scale, reproductive-age context and socioeconomic context."],
        ["CDC PLACES (7)", "State abbreviation; population; obesity, physical inactivity, smoking and depression prevalence; imputation flag", "Adds public-health risk context that can be compared with menstrual outcomes at state level."],
        ["Open-Meteo (6)", "Latitude, longitude, mean temperature, mean humidity, precipitation and mean wind speed", "Adds date-linked environmental context using the state capital as a consistent representative location."],
        ["Quality flags (2)", "has_previous_cycle; coordinates_available", "Makes missingness and analytical eligibility explicit."],
    ], widths=[1600, 4400, 3360], font_size=8.6)

    heading(doc, "1.3 Excluded or Restricted Information", 2)
    add_table(doc, ["Item", "Decision", "Reason"], [
        ["Overpass healthcare facilities", "Not fused into the final CSV", "No trustworthy cycle-level or state-level analytical join was established; facility proximity could imply false precision."],
        ["USDA nutrition search results", "Not fused into the final CSV", "Food search records do not describe a specific participant or cycle and would create a many-to-many join."],
        ["Direct user_id", "Retained in the analytical CSV; excluded from RAG text", "Needed for cycle linkage, but not needed for answering aggregate questions."],
        ["Latitude and longitude", "Retained for weather traceability; excluded from RAG text", "Coordinates support the API request but add little conversational value."],
        ["Raw API payload fields", "Only selected variables retained", "Reduces noise, size and accidental dependence on undocumented fields."],
    ], widths=[1900, 2400, 5060], font_size=8.5)

    heading(doc, "1.4 What Became Possible After Fusion", 2)
    add_figure(doc, ASSETS / "fig11_capability_matrix.png", "Figure 1. Knowledge coverage before and after API data fusion.", width=6.35)
    add_bullets(doc, [
        "Compare menstrual pain and stress across states while also seeing population, income and public-health context.",
        "Test relationships between cycle outcomes and weather observed on the cycle start date.",
        "Answer state-specific Census and CDC questions from the same knowledge base as menstrual-health guidance.",
        "Produce source-labelled responses that point to the fused CSV or a derived state/EDA summary.",
    ])

    page_break(doc)
    heading(doc, "1.5 Data Quality Effects of Fusion", 2)
    add_table(doc, ["Quality dimension", "Result", "Meaning"], [
        ["Row preservation", "17,976 rows before and after", "No menstrual-cycle record was lost during the joins."],
        ["Key uniqueness", "0 duplicate user-cycle keys", "The fusion did not create unintended many-to-many row multiplication."],
        ["Completeness", "2,642 missing cells after cleaning", "Only previous-cycle length (2,000) and coordinates (321 latitude + 321 longitude) remain missing."],
        ["CDC continuity", "Imputation flag retained", "The project records when a health-context value required a defined fallback rather than hiding the repair."],
        ["Temporal alignment", "Weather joined by state and start date", "Weather varies by cycle date instead of being a single state constant."],
        ["Geographic precision", "State-capital weather proxy", "A consistent method, but it may not represent the participant’s actual local conditions."],
        ["Measurement level", "Census/CDC values repeated within state", "These are contextual state indicators, not individual diagnoses or exposures."],
    ], widths=[2000, 2600, 4760], font_size=8.7)
    add_para(doc, "Quality conclusion: The fusion passed structural validation—row count, key uniqueness and required-column checks—but introduced interpretation risks. State-level associations are ecological; weather uses a representative state location; and the same state value repeats across many cycle records. These limitations are disclosed whenever results are interpreted.", bold_prefix="Quality conclusion:")

    heading(doc, "1.6 New Patterns and More Useful Variables", 2)
    add_figure(doc, ASSETS / "fig10_state_comparison.png", "Figure 2. Example state comparison created from original outcomes plus fused context.", width=5.10)
    add_table(doc, ["Relationship", "Observed value", "Interpretation"], [
        ["Temperature vs pain", "r = -0.0165", "Negligible linear relationship in these records."],
        ["Humidity vs pain", "r = -0.0036", "Negligible linear relationship."],
        ["Precipitation vs pain", "r = -0.0020", "Negligible linear relationship."],
        ["Wind speed vs pain", "r = 0.0125", "Negligible linear relationship."],
        ["State depression vs average stress", "r = 0.008", "No meaningful state-level linear pattern."],
        ["State inactivity vs average pain", "r = -0.0862", "Very weak negative state-level association."],
        ["State obesity vs median income", "r ≈ -0.74", "Strong negative state-level association in the fused data; not a causal result."],
    ], widths=[3300, 2000, 4060], font_size=8.7)

    heading(doc, "2. Part G – Insight Generation", 1)
    add_para(doc, "Each insight uses the required Finding → Evidence → Interpretation structure. Correlation describes association only; it does not establish causation.")
    add_insight(doc, 1,
                "Weather variables do not explain menstrual pain in this dataset.",
                "Pain correlations are -0.0165 with temperature, -0.0036 with humidity, -0.0020 with precipitation and 0.0125 with wind speed.",
                "The integrated weather fields add queryable context, but the observed linear relationships are effectively zero. The application should not imply that weather caused or predicted pain here.")
    add_insight(doc, 2,
                "State obesity prevalence is lower where median household income is higher in this fused sample.",
                "Across the 50 state summaries, Pearson r is approximately -0.74 between CDC obesity prevalence and Census median household income.",
                "This is the strongest new contextual pattern found. It is useful for population-level exploration, but it is ecological and cannot be applied to an individual user.")
    add_insight(doc, 3,
                "The original menstrual variables remain more directly related to pain than the added context.",
                "Original-data correlations include pain with stress r = 0.607, mood r = -0.646, energy r = -0.707 and overall health r = -0.921; API weather-pain correlations are near zero.",
                "The API data broadens the questions the system can answer, while the original symptoms and wellness measures remain the more useful variables for within-dataset pain patterns.")
    add_insight(doc, 4,
                "California records show higher average pain than Texas records.",
                "Mean pain is 5.321 in California and 4.277 in Texas; the fixed LLM test retrieved both values correctly.",
                "Fusion enables an explicit cross-state comparison and lets the assistant attach public-health and income context. It does not show why the difference exists.")

    h = heading(doc, "2. Insights 5–7 (Part G continued)", 1)
    h.paragraph_format.page_break_before = True
    add_insight(doc, 5,
                "The data enrichment adds knowledge breadth without reducing general health-answer accuracy in the fixed test.",
                "Both systems answered all five original-domain questions correctly; only the enhanced system answered all five fusion/API questions correctly.",
                "The added records expanded answerable topics while preserving the tested baseline capability.")
    add_insight(doc, 6,
                "Grounded refusal prevented invented API facts in the baseline system.",
                "For all five API/fusion questions, the baseline stated that the knowledge base did not contain enough information; zero unsupported answers were counted.",
                "A safe system should admit missing evidence rather than fabricate state values. The improvement after fusion is therefore an evidence-availability improvement, not increased guessing.")
    add_insight(doc, 7,
                "More knowledge increased local response time.",
                f"Average time rose from {summary.loc['Before fusion','average_response_time_seconds']:.1f} seconds to {summary.loc['After fusion','average_response_time_seconds']:.1f} seconds in the recorded local Ollama run.",
                "The enhanced system is more capable, but production work should optimize retrieval, caching and model serving. These timings are machine-specific and are not a hosted-service benchmark.")
    page_break(doc)
    heading(doc, "3. Part H – Integration with the LLM/RAG System", 1)
    heading(doc, "3.1 Architecture", 2)
    add_figure(doc, ASSETS / "fig07_phase2_rag_pipeline.png", "Figure 3. Phase 2 fused-data RAG pipeline.", width=6.35)
    add_numbered(doc, [
        "Load the final cleaned fused CSV and the existing medical-knowledge text files.",
        "Create one document for each fused cycle record, one summary document for each state, three fusion-analysis summaries, and one original-dataset summary.",
        "Exclude direct user identifiers and coordinates from the searchable text.",
        "Convert document text into TF-IDF vectors using unigrams and bigrams.",
        "Store the sparse matrix, vectorizer and source-labelled documents in a local joblib index.",
        "For each question, retrieve the five most similar documents using cosine similarity.",
        "Send only the retrieved context and the question to Llama 3.2. The prompt instructs the model to refuse when evidence is missing.",
    ])

    heading(doc, "3.2 Knowledge-Base Composition", 2)
    add_table(doc, ["Document type", "Count", "Purpose"], [
        ["Medical knowledge sections", f"{manifest['document_counts']['medical_knowledge']:,}", "Preserve general menstrual-health capability."],
        ["Original dataset summary", "1", "Describe the original dataset and baseline statistics."],
        ["Fusion/EDA summaries", "3", "Make overall correlations and dataset-level findings retrievable."],
        ["State summaries", f"{manifest['document_counts']['state_summaries']:,}", "Answer direct Census, CDC and state-average questions."],
        ["Fused cycle records", f"{manifest['document_counts']['fused_cycle_records']:,}", "Support record-level questions combining cycle and contextual fields."],
        ["Total enhanced documents", f"{manifest['fused_index']['documents']:,}", "Complete Phase 2 searchable collection."],
    ], widths=[2800, 1300, 5260], font_size=9)

    heading(doc, "3.3 Why TF-IDF Was Used for the Controlled Comparison", 2)
    add_para(doc, "The older application used a MiniLM/FAISS index created from pre-fusion data. Phase 2 builds two new indexes with the same TF-IDF method: one baseline index without fused records and one enhanced index with fused records. Using the same retrieval method and Llama model on both sides makes the comparison about data enrichment. TF-IDF is lightweight, deterministic and sufficient for direct state names, field labels and numerical questions. A semantic embedding index remains a future product improvement for paraphrases and complex meaning-based retrieval.")

    heading(doc, "3.4 How API Information Becomes Available to the LLM", 2)
    add_para(doc, "The language model does not read the CSV directly. The preparation script turns selected fields into readable sentences such as a California state summary. The retriever finds that document when the question contains California, population or income terms. The retrieved sentence is placed in the prompt, which gives the model the exact values and a source label. This is the mechanism by which external API information becomes usable at answer time.")

    heading(doc, "3.5 Implementation Components", 2)
    add_table(doc, ["Component", "Implementation", "Output"], [
        ["Preparation", "embeddings/build_phase2_knowledge_base.py", "Source-labelled medical, summary, state and cycle documents"],
        ["Vectorization", "scikit-learn TfidfVectorizer", "Sparse unigram/bigram vectors"],
        ["Storage", "joblib", "Portable local vectorizer, matrix and document bundle"],
        ["Retrieval", "rag/phase2_retriever.py", "Five cosine-ranked context documents"],
        ["Generation", "Ollama llama3.2:3b", "Short answer grounded in supplied context"],
    ], widths=[1750, 3300, 4310], font_size=8.8)

    page_break(doc)
    heading(doc, "4. LLM Testing Using the Fused Dataset (Part I)", 1)
    heading(doc, "4.1 Test Design", 2)
    add_table(doc, ["Control", "Setting"], [
        ["Model", "Ollama llama3.2:3b for both systems"],
        ["Temperature", "0; seed 42; maximum 180 generated tokens"],
        ["Retriever", "TF-IDF cosine similarity; top 5 documents"],
        ["Baseline knowledge", "31 medical sections + one original-dataset summary"],
        ["Enhanced knowledge", "Baseline knowledge + fusion summaries + 50 state summaries + 17,976 fused records"],
        ["Question set", "Five original-domain questions and five fused/API questions"],
        ["Correctness rule", "Required facts/keywords must appear; baseline refusal is relevant but not correct for a fused-data question"],
        ["Hallucination rule", "A fabricated answer or a failed required-fact check is counted as unsupported"],
    ], widths=[2300, 7060], font_size=9)
    add_para(doc, "The complete machine-readable evidence is saved in report/phase2/assets/phase2_rag_evaluation.csv and phase2_rag_evaluation.json. The following tables reproduce the required question, response, expected answer, source/record and correctness fields.")

    def evaluation_rows(system, question_set):
        rows = []
        frame = evaluation[(evaluation["system"] == system) & (evaluation["set"] == question_set)]
        for _, r in frame.iterrows():
            response = str(r["response"]).replace("\n", " ")
            if r["id"] == "O5" and system == "After fusion":
                response = ("Medical attention is advised when bleeding soaks one or more pads/tampons "
                            "every hour for consecutive hours; other warning signs include large clots, "
                            "severe pain, fainting, fever or postmenopausal bleeding. [Condensed from the recorded response]")
            rows.append([
                r["id"],
                r["question"],
                response,
                r["expected"],
                r["source"],
                "Correct" if bool(r["correct"]) else "Not correct",
            ])
        return rows

    heading(doc, "4.2 Original-Domain Questions – Enhanced System", 2)
    add_table(doc, ["ID", "Question", "Recorded response (condensed where marked)", "Expected answer", "Source/record", "Result"],
              evaluation_rows("After fusion", "Original"),
              widths=[480, 1770, 2590, 1840, 2050, 630], font_size=7.3)

    heading(doc, "4.3 Fused/API Questions – Before Fusion", 2)
    add_para(doc, "The baseline returned the safe refusal for every fused-data question because those facts were not present in its index. These answers are relevant and non-hallucinatory, but they do not satisfy the requested facts.")
    add_table(doc, ["ID", "Question", "Recorded response", "Expected answer", "Required source", "Result"],
              evaluation_rows("Before fusion", "Fused API"),
              widths=[480, 2000, 2000, 2000, 2250, 630], font_size=7.4)

    heading(doc, "4.4 Fused/API Questions – After Fusion", 2)
    add_table(doc, ["ID", "Question", "Recorded response", "Expected answer", "Source/record", "Result"],
              evaluation_rows("After fusion", "Fused API"),
              widths=[480, 1840, 2260, 2000, 2150, 630], font_size=7.3)

    heading(doc, "5. Part J – Before/After LLM Comparison", 1)
    heading(doc, "5.1 Quantitative Results", 2)
    add_table(doc, ["Metric", "Before fusion", "After fusion", "Change"], [
        ["Questions tested", "10", "10", "Same"],
        ["Correct answers", "5", "10", "+5"],
        ["Accuracy", "50%", "100%", "+50 percentage points"],
        ["Complete answers", "5", "10", "+5"],
        ["Relevant responses", "10", "10", "No change"],
        ["Unsupported/hallucinated answers", "0", "0", "No change"],
        ["Average response time", f"{summary.loc['Before fusion','average_response_time_seconds']:.1f} s", f"{summary.loc['After fusion','average_response_time_seconds']:.1f} s", f"+{summary.loc['After fusion','average_response_time_seconds'] - summary.loc['Before fusion','average_response_time_seconds']:.1f} s"],
    ], widths=[3000, 2100, 2100, 2160], font_size=9)
    add_figure(doc, ASSETS / "fig08_before_after_accuracy.png", "Figure 4. Correct answers increased from 5/10 to 10/10.", width=5.85)

    heading(doc, "5.2 Evidence-Based Usefulness Conclusion", 2)
    add_para(doc, "The fused dataset made the application measurably more useful for the tested scope. Before fusion, the assistant could answer general menstrual-health questions but correctly refused questions about state population, income, CDC prevalence, weather-pain correlation and cross-state pain. After fusion, it answered every one of those questions using retrieved evidence while retaining 5/5 accuracy on the original set. This is a direct increase in knowledge coverage and answer completeness.")
    add_para(doc, "The conclusion is intentionally limited. Ten hand-designed questions are sufficient to demonstrate the implemented capability, but not to prove broad accuracy, clinical safety, fairness or real-world effectiveness. A product evaluation would require a larger blind question set, clinician review, retrieval metrics, adversarial tests and monitoring.")

    heading(doc, "5.3 Response-Time and Product Trade-off", 2)
    add_figure(doc, ASSETS / "fig09_response_time.png", "Figure 5. Local average response time before and after enrichment.", width=5.85)
    add_para(doc, "The enhanced index was slower in this single local run. The additional time may include local model generation variability as well as retrieval and prompt differences; it should not be interpreted as a precise causal cost of the index. For a product, response time can be improved by using state summaries for aggregate questions, caching repeated results, reducing retrieved context and deploying an optimized inference service.")

    heading(doc, "5.4 Safety and Hallucination Behaviour", 2)
    add_bullets(doc, [
        "The prompt explicitly requires the model to answer only from retrieved context.",
        "When evidence is absent, the exact refusal sentence is preferred to guessing.",
        "Each indexed document carries a source label, enabling response traceability.",
        "Zero unsupported answers were observed in the fixed test, but this does not guarantee zero hallucinations on unseen questions.",
        "Clinical claims still require professional review, warning-sign escalation and clear non-diagnostic wording.",
    ])

    h = heading(doc, "6. Part K – Technical Documentation", 1)
    h.paragraph_format.page_break_before = True
    heading(doc, "6.1 Files Involved", 2)
    add_table(doc, ["Stage", "File", "Role"], [
        ["Original data", "data/menstrual_dataset.csv", "Source cycle-level dataset."],
        ["Census API", "scripts/api_census.py", "Collects selected ACS state variables; API key is read from CENSUS_API_KEY."],
        ["CDC API", "scripts/api_cdc_places.py", "Collects county data and produces population-weighted state indicators."],
        ["Weather API", "scripts/api_open_meteo.py", "Uses state capitals and cycle dates to collect historical weather."],
        ["Fusion", "scripts/final_fusion.py", "Joins original, Census, CDC and weather records at the defined grains."],
        ["Cleaning", "scripts/clean_final_dataset.py", "Produces the final validated 56-column CSV and flags."],
        ["EDA", "scripts/eda_final_dataset.py", "Generates summaries, correlations and EDA figures."],
        ["RAG preparation", "embeddings/build_phase2_knowledge_base.py", "Creates baseline/enhanced documents and TF-IDF indexes."],
        ["Retrieval", "rag/phase2_retriever.py", "Ranks documents with cosine similarity and returns labelled context."],
        ["LLM interface", "rag/llm.py", "Calls Ollama, with direct HTTP fallback when the Python client is absent."],
        ["Application", "app.py", "Connects the Streamlit chat interface to the enhanced retriever."],
        ["Evaluation", "scripts/evaluate_phase2_rag.py", "Runs the fixed comparison and writes per-question and summary evidence."],
    ], widths=[1500, 3400, 4460], font_size=8.2)

    heading(doc, "6.2 Data and Result Files", 2)
    add_table(doc, ["Artifact", "Location", "Status"], [
        ["Original dataset", "data/menstrual_dataset.csv", "17,976 × 34"],
        ["Census output", "data/api_fusion/static/census_state.csv", "52 rows × 8 columns"],
        ["CDC output", "data/api_fusion/static/cdc_places_state.csv", "51 rows × 8 columns"],
        ["Weather output", "data/api_fusion/dynamic/open_meteo_row_level.csv", "17,976 row-level records"],
        ["Raw fused CSV", "data/api_fusion/final/femcare_final_fused_dataset.csv", "Intermediate fusion output"],
        ["Final cleaned CSV", "data/api_fusion/final/femcare_final_cleaned.csv", "17,976 × 56"],
        ["Baseline index", "vectorstore/phase2_original_index/index.joblib", "32 documents"],
        ["Enhanced index", "vectorstore/phase2_fused_index/index.joblib", "18,061 documents"],
        ["Question evidence", "report/phase2/assets/phase2_rag_evaluation.csv", "20 system-question runs"],
        ["Summary evidence", "report/phase2/assets/phase2_rag_summary.csv", "2-system comparison"],
    ], widths=[2200, 5000, 2160], font_size=8.3)

    page_break(doc)
    heading(doc, "6.3 Reproducible Execution Order", 2)
    add_numbered(doc, [
        "Collect or refresh Census data with scripts/api_census.py after setting CENSUS_API_KEY.",
        "Collect or refresh CDC PLACES data with scripts/api_cdc_places.py.",
        "Collect or refresh date-linked weather data with scripts/api_open_meteo.py.",
        "Run scripts/final_fusion.py to create the combined CSV.",
        "Run scripts/clean_final_dataset.py and scripts/inspect_final_dataset.py to validate and clean the result.",
        "Run scripts/eda_final_dataset.py to regenerate the analytical summaries and figures.",
        "Run embeddings/build_phase2_knowledge_base.py to build both controlled-comparison indexes.",
        "Ensure Ollama and llama3.2:3b are available, then run scripts/evaluate_phase2_rag.py.",
        "Review the CSV/JSON evidence and launch the enhanced app with streamlit run app.py.",
    ])

    heading(doc, "6.4 Validation Checklist", 2)
    add_table(doc, ["Check", "Expected condition", "Recorded outcome"], [
        ["Schema", "56 expected final columns", "Passed"],
        ["Row count", "Equal to original 17,976", "Passed"],
        ["Unique key", "No duplicate user_id + cycle_number", "Passed: 0 duplicates"],
        ["Required API values", "Census/CDC fields complete after defined cleaning", "Passed"],
        ["Missingness", "Documented, not silently ignored", "2,642 cells documented"],
        ["Index build", "Both joblib files and manifest created", "Passed"],
        ["Retrieval", "State question returns matching state summary", "Passed for CA, TX and MA tests"],
        ["LLM evaluation", "All 20 system-question runs saved", "Passed"],
    ], widths=[2300, 3900, 3160], font_size=8.7)

    heading(doc, "6.5 Repository Organization", 2)
    add_para(doc, "The project separates collection scripts, datasets, analytical outputs, knowledge-base code, retrieval code, application code and report evidence. The root README now lists the Phase 2 commands, important files, key-handling rule and evaluation boundary. Historical Phase 1 outputs remain in report/phase1; new deliverables are contained in report/phase2.")

    page_break(doc)
    heading(doc, "7. Limitations, Ethics and Next Product Steps", 1)
    heading(doc, "7.1 Current Limitations", 2)
    add_bullets(doc, [
        "The menstrual dataset is an academic dataset and is not proven to be representative of real patients or all populations.",
        "State-level Census and CDC variables are repeated across users and must not be interpreted as individual characteristics.",
        "Weather is represented by the state capital, not the user’s actual location.",
        "The test contains only ten designed questions; it does not measure performance on paraphrases, multi-step questions or adversarial prompts.",
        "Keyword-based correctness checks are reproducible but simpler than independent human grading.",
        "The LLM and retrieval system provide educational information, not diagnosis, treatment or emergency care.",
    ])

    heading(doc, "7.2 Privacy and Security", 2)
    add_bullets(doc, [
        "Direct user identifiers and coordinates are omitted from searchable RAG documents.",
        "API credentials are read from environment variables rather than stored in source code.",
        "A production system would require authentication, encryption, audit logs, data-retention rules, consent management and role-based access.",
        "Any real patient data would require formal legal, institutional and security review before collection or processing.",
    ])

    heading(doc, "7.3 Recommended Next Product Steps", 2)
    add_numbered(doc, [
        "Create a clinically reviewed knowledge policy and emergency/red-flag escalation flow.",
        "Replace synthetic or academic records with consented, governed data and establish a formal data dictionary.",
        "Add a semantic embedding index and evaluate hybrid semantic + keyword retrieval.",
        "Build a larger blind evaluation set with clinician scoring for factuality, helpfulness, safety and demographic fairness.",
        "Add automated regression tests so every data refresh or prompt change must preserve safety and accuracy.",
        "Measure product latency separately for retrieval and generation, then optimize caching and serving.",
    ])

    page_break(doc)
    heading(doc, "8. Conclusion", 1)
    add_para(doc, "Phase 2 completed the path from API-enriched CSV to a working, testable RAG knowledge base. The final dataset retains all 17,976 cycle records, expands the schema from 34 to 56 columns and introduces Census, CDC and weather context. The integration creates new analytical possibilities, especially state comparisons and contextual questions, while also requiring careful handling of geographic proxies and ecological variables.")
    add_para(doc, "In the controlled ten-question test, the baseline system achieved 50% because it correctly answered the five general health questions but lacked evidence for the five fusion questions. The enhanced system achieved 100% and produced no unsupported answers under the defined checks. The principal cost was higher local response time. Within the tested scope, this provides evidence that the fused dataset improves the assistant’s usefulness and knowledge coverage.")
    add_para(doc, "The project remains an academic prototype. The next stage should focus on clinical review, privacy governance, larger evaluations, semantic retrieval and production-grade deployment rather than treating the current results as clinical validation.")

    heading(doc, "References", 1)
    references = [
        "Course assignment: LLM–API–Data Fusion and Exploratory Data Analysis, Phase 2 requirements, Parts F–K.",
        "Jadhav, S. FemCare AI – Phase 1 Report, 31 August 2026.",
        "Kaggle. Menstrual Cycle Data. https://www.kaggle.com/datasets/nikitabisht/menstrual-cycle-data",
        "U.S. Census Bureau. 2024 ACS 5-Year API. https://api.census.gov/data/2024/acs/acs5",
        "Centers for Disease Control and Prevention. PLACES data API. https://data.cdc.gov/resource/i46a-9kgh.json",
        "Open-Meteo. Historical Weather API. https://archive-api.open-meteo.com/v1/archive",
        "Ollama. Local model runtime used with llama3.2:3b. https://ollama.com/",
    ]
    add_numbered(doc, references)

    page_break(doc)
    heading(doc, "Appendix A – Fixed Evaluation Questions", 1)
    rows = []
    for _, row in evaluation[evaluation["system"] == "After fusion"].iterrows():
        rows.append([row["id"], row["set"], row["question"], row["expected"]])
    add_table(doc, ["ID", "Set", "Question", "Expected evidence"], rows,
              widths=[650, 1200, 3650, 3860], font_size=8.2)

    heading(doc, "Appendix B – Phase 2 Deliverables", 1)
    add_table(doc, ["Deliverable", "Location"], [
        ["Final fused dataset", "data/api_fusion/final/femcare_final_cleaned.csv"],
        ["API source datasets", "data/api_fusion/static and data/api_fusion/dynamic"],
        ["EDA outputs", "data/api_fusion/eda"],
        ["Enhanced RAG index", "vectorstore/phase2_fused_index/index.joblib"],
        ["Evaluation evidence", "report/phase2/assets"],
        ["Source code", "scripts, embeddings, rag and app.py"],
        ["Technical instructions", "README.md"],
        ["Phase 2 report", "report/phase2/FemCare_Phase_2_Report.docx"],
    ], widths=[3000, 6360], font_size=9)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Created {OUT}")


if __name__ == "__main__":
    build()
