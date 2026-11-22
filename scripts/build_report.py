"""Build the black-only, bordered assignment report from versioned sources."""

from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import statistics

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, LongTable, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, TableStyle, KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/technical-report.pdf"
WIDTH = A4[0] - 44 * mm
STYLES = getSampleStyleSheet()
for style in STYLES.byName.values():
    style.textColor = colors.black
STYLES.add(ParagraphStyle("ReportBody", fontName="Times-Roman", fontSize=10.5,
    leading=14.5, alignment=TA_JUSTIFY, spaceAfter=7, allowWidows=0, allowOrphans=0,
    splitLongWords=True))
STYLES.add(ParagraphStyle("Major", fontName="Helvetica-Bold", fontSize=16,
    leading=21, spaceAfter=16, keepWithNext=True))
STYLES.add(ParagraphStyle("Minor", fontName="Helvetica-Bold", fontSize=11.5,
    leading=16, spaceBefore=12, spaceAfter=7, keepWithNext=True))
STYLES.add(ParagraphStyle("Cell", fontName="Times-Roman", fontSize=8,
    leading=10.5, spaceAfter=0, splitLongWords=True))
STYLES.add(ParagraphStyle("CellHead", parent=STYLES["Cell"], fontName="Times-Bold"))
STYLES.add(ParagraphStyle("CodeBlock", fontName="Courier", fontSize=7.6,
    leading=10.4, spaceBefore=4, spaceAfter=10, borderColor=colors.black,
    borderWidth=.4, borderPadding=7, keepWithNext=True))
STYLES.add(ParagraphStyle("Cover", fontName="Helvetica-Bold", fontSize=26,
    leading=34, alignment=TA_CENTER, spaceAfter=18))
STYLES.add(ParagraphStyle("CoverSub", fontName="Helvetica", fontSize=12,
    leading=18, alignment=TA_CENTER, spaceAfter=12))


def clean(text):
    for a, b in (("?", "^2"), ("?", "-"), ("?", "-"), ("?", ">="),
                 ("?", "<="), ("?", "x"), ("?", "->"), ("?", "'")):
        text = text.replace(a, b)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = escape(text.replace("`", ""))
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)


def table(rows):
    count = len(rows[0])
    widths = [WIDTH / count] * count
    if count == 2:
        widths = [WIDTH * .28, WIDTH * .72]
    elif count == 3:
        widths = [WIDTH * .20, WIDTH * .37, WIDTH * .43]
    cells = [[Paragraph(clean(c), STYLES["CellHead" if i == 0 else "Cell"])
              for c in row] for i, row in enumerate(rows)]
    result = LongTable(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), .35, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def markdown_flowables(text):
    lines = text.splitlines()
    flow = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            flow.append(Preformatted("\n".join(code), STYLES["CodeBlock"]))
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", c) for c in cells):
                    rows.append(cells)
                index += 1
            flow.extend([KeepTogether([table(rows)]) if len(rows) <= 13 else table(rows), Spacer(1, 4 * mm)])
            continue
        elif line.startswith("## "):
            flow.extend([PageBreak(), Paragraph(clean(line[3:]), STYLES["Major"])])
        elif line.startswith("### "):
            flow.append(Paragraph(clean(line[4:]), STYLES["Minor"]))
        elif line.startswith("# "):
            flow.append(Paragraph(clean(line[2:]), STYLES["Major"]))
        else:
            paragraph = [line]
            while index + 1 < len(lines):
                nxt = lines[index + 1].strip()
                if not nxt or nxt.startswith(("#", "|", "```")):
                    break
                index += 1
                paragraph.append(nxt)
            flow.append(Paragraph(clean(" ".join(paragraph)), STYLES["ReportBody"]))
        index += 1
    # Keep the small dispersion summary with its heading and explanation.
    for position, item in enumerate(flow):
        if (isinstance(item, Paragraph)
                and item.getPlainText().startswith("7.7 Timing dispersion")):
            end = position + 1
            while end < len(flow) and not isinstance(flow[end], PageBreak):
                end += 1
            flow[position:end] = [KeepTogether(flow[position:end])]
            break
    return flow


def experiment_report():
    raw = json.loads((ROOT / "experiments/results/studies.json").read_text())
    analysis = (ROOT / "experiments/results/analysis.md").read_text(encoding="utf-8")
    env = raw["environment"]
    parts = re.split(r"^## ", analysis, flags=re.M)[1:]
    methods = [
        ("Use vertex counts 20, 60 and 120 at sparse and denser edge probabilities. "
         "A chain guarantees connectivity; extra edges use probability 2/V or 0.12. "
         "Coordinates are uniform in [0,100); road length is uniform in [1,25], "
         "time=length/5 and fuel=length/10. Traverse from vertex 0. Each pair uses the same graph.",
         "Visited vertices, examined adjacency entries and elapsed milliseconds. "
         "Verify minimum hops with independent repeated relaxation, and verify connected/cycle results before timing.",
         "On these connected inputs both traversals examine the adjacency structure; "
         "the counters support the O(V+E) model. Small timings are noisy, so no timing row proves that bound.",
         "Only connected undirected generated graphs are timed; directed/disconnected edge cases belong to the test suite."),
        ("Use the same sparse generator at V=20,60,120 and seeds SEED+V. "
         "Coordinates are independent uniform [0,100); edge length is uniform [1,25], "
         "time=length/5 and fuel=length/10. Route 0 to V-1 with the shared balanced cost. "
         "Run Dijkstra and A* on exactly the same instance at each size.",
         "Expanded vertices, attempted edge relaxations, heap operations, optimal scalar cost and milliseconds. "
         "Check cost equality outside timing. A* heuristic setup is included.",
         "A* expands fewer vertices in two stored cases and the same number in one; no case here expands more. "
         "Equal expansion is possible with a weak/zero bound. Tie order, termination and heuristic behavior "
         "affect comparisons generally; the experiment does not establish a universal expansion advantage. "
         "Both return equal optimal costs on these inputs, and fewer expansions do not ensure shorter runtime.",
         "Only three synthetic sparse graphs are measured, not named authored-circuit workloads. "
         "This limits generalization to gameplay circuits. No more-expansion case was observed."),
        ("Use three explicit small counterexamples and generated item/budget pairs (10,30), (30,60), (60,100). "
         "Generated costs are integers 1..12, benefits 1..30, using Random(SEED). "
         "Time both algorithms on each identical item list. Exhaustively enumerate small-case subsets before timing.",
         "Selected IDs, total benefit, runtime and DP state count. Selected IDs and full input items are retained in raw JSON.",
         "DP is optimal for the discrete scalar-budget model and defeats greedy on all three counterexamples. "
         "Its O(mB) bound is pseudo-polynomial; greedy takes O(m log m) for ordering and need not maximize benefit.",
         "Budgets are small and integer; this is not a measurement of the joint multi-resource routing problem."),
        ("Use 50,250,1000 scheduled events, timestamps from 0..11 and priorities from 1..6 with seed SEED+n. "
         "Measure queue creation/insertion separately from extraction. Cancel every eleventh event before extraction; "
         "prepare that queue outside extraction timing. Compare surviving events with (time,priority,sequence). "
         "A separate two-closure race check verifies independent expiry at times 3 and 6.",
         "Insertion milliseconds, extraction milliseconds, cancellation count and heap operations. "
         "The operation total counts insertion/extraction, including lazily cancelled entries; it is not a comparison count.",
         "Heap ordering gives deterministic scheduling even with equal timestamps and priorities. "
         "Insert/extract take O(log n) each, with O(n log n) total queue work; lazy cancellation defers removal work.",
         "The distribution has a small timestamp/priority range and does not represent every event burst or cancellation ratio."),
        ("Use n=50,200,500 championship records in random, sorted, reverse and duplicate-heavy forms. "
         "Generate points/wins/positions/laps with Random(SEED); duplicate-heavy rows repeat primary fields, "
         "while racer ID remains the final tie-break. Compare three full sorts and k=5 versus k=n-1 on the same inputs.",
         "Mean/median elapsed time; verify all rankings and top-k prefixes with Python reference sorting "
         "under ranking_key. Sorting comparison counters are not implemented and are not reported.",
         "Merge/Heap Sort are O(n log n); Quick Sort averages O(n log n) with O(n^2) worst case. "
         "The bounded heap uses O(n log(k+1)) time and O(k) storage. Its storage advantage declines as k approaches n; "
         "observed runtimes vary with ordering and comparator/setup overhead.",
         "Duplicate-heavy primary fields are not identical total keys because IDs differ. "
         "Small samples and visible outliers limit reliable speedup claims."),
    ]
    output = ["### 7.1 Shared environment and timing protocol", "",
        f"Recorded environment: {env['platform']}; {env['processor']}; Python {env['python']}. "
        f"Dependency versions: {env['dependencies']}. Master seed: {env['seed']}. "
        "The audit dates this stored run to 19 November 2026. Each measurement uses one warm-up and five timed repetitions "
        "with perf_counter on the same machine and interpreter. Algorithms in a pair use identical inputs. "
        "Input generation, correctness checks, rendering, file I/O and artificial delays are outside timing. "
        "Algorithm initialization and trace construction are included, except queue preparation for extraction. "
        "No compiler/build-mode comparison is made: these are interpreted Python calls. "
        "CPU model family is recorded, but RAM, exact marketing model and power/background-load settings were not captured; "
        "those missing fields must not be inferred. Results describe the recorded runtime conditions.", "",
        "Tables present means; the raw file retains all five samples and medians. The supplementary summary below "
        "shows median and sample standard deviation on representative paired workloads. "
        "Measurements are empirical and do not determine theoretical complexity from a single timing.", ""]
    for i, (part, method) in enumerate(zip(parts, methods), 1):
        title, body = part.split("\n", 1)
        procedure, metrics, conclusion, limits = method
        output += [f"### 7.{i+1} Experiment {i}: {title.split('. ',1)[-1]}", "",
            "**Objective and recorded results.** " + body.strip().split("\n\n",1)[0], "",
            "**Environment.** Windows 11, Intel64 Family 6 Model 142 Stepping 10, Python 3.12.16; "
            "same dependency set, seed policy and timing controls as Section 7.1. "
            "One warm-up followed by five measurements per operation.", "",
            "**Inputs and procedure.** " + procedure, "", "**Metrics and correctness.** " + metrics, ""]
        rest = body.strip().split("\n\n",1)[1]
        output += [rest, "", "**Limitations.** " + limits, "", "**Conclusion.** " + conclusion, ""]
        if i == 3:
            output += ["**Selected-item evidence for the small counterexamples.** Costs/benefits are listed as (cost, benefit) in ID order.", "",
                "| Budget | Input items | DP IDs / benefit | Greedy IDs / benefit |",
                "| --- | --- | --- | --- |"]
            for case in raw["resources"]["cases"]:
                b = case["budget"]
                rr = [r for r in raw["resources"]["rows"] if r["budget"] == b and r["items"] == 3]
                dp, gr = rr
                inputs = "; ".join(f"({x['cost']},{x['benefit']})" for x in case["items"])
                output.append(f"| {b} | {inputs} | {dp['selected']} / {dp['benefit']} | {gr['selected']} / {gr['benefit']} |")
            output.append("")
    output += ["### 7.7 Timing dispersion on representative workloads", "",
        "Sample standard deviation uses the five stored observations (denominator r-1). "
        "These selected rows illustrate variability; the complete raw dataset remains the reproducible record.", "",
        "| Workload | Algorithm | Mean ms | Median ms | Sample SD ms |",
        "| --- | --- | --- | --- | --- |"]
    selected = []
    for group, size_key, size in (("traversal","vertices",120),("routing","vertices",120),("sorting","size",500)):
        for row in raw[group]:
            if row[size_key] != size or (group == "traversal" and not row["dense"]):
                continue
            if group == "sorting" and row["input"] != "random":
                continue
            label = row["algorithm"]
            if label == "top_k":
                label += f" (k={row['k']})"
            selected.append((f"{group}, n={size}", label, row["timing"]))
    for label, alg, timing in selected:
        output.append(f"| {label} | {alg} | {timing['mean_ms']:.4f} | {timing['median_ms']:.4f} | "
                      f"{statistics.stdev(timing['samples_ms']):.4f} |")
    return "\n".join(output)


class Report(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if (isinstance(flowable, Paragraph) and flowable.style.name in ("Major", "Minor")
                and flowable.getPlainText() != "Contents"):
            title = flowable.getPlainText()
            level = 0 if flowable.style.name == "Major" else 1
            key = "section-" + re.sub(r"[^a-zA-Z0-9]+", "-", title)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level)
            self.notify("TOCEntry", (level, title, self.page, key))


def page_frame(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setFillColor(colors.black)
    canvas.setLineWidth(.65)
    canvas.rect(12 * mm, 12 * mm, A4[0] - 24 * mm, A4[1] - 24 * mm)
    if document.page > 1:
        canvas.setFont("Helvetica", 8)
        canvas.drawString(22 * mm, A4[1] - 20 * mm, "SMART RACING CHAMPIONSHIP")
        canvas.drawRightString(A4[0] - 22 * mm, A4[1] - 20 * mm, "TECHNICAL REPORT")
        canvas.line(22 * mm, A4[1] - 23 * mm, A4[0] - 22 * mm, A4[1] - 23 * mm)
        canvas.line(22 * mm, 23 * mm, A4[0] - 22 * mm, 23 * mm)
        canvas.drawString(22 * mm, 18 * mm, "Design and Analysis of Algorithms | FAST-NUCES")
        canvas.drawRightString(A4[0] - 22 * mm, 18 * mm, f"Page {document.page}")
    canvas.restoreState()


def cover(details):
    flow = [Spacer(1, 12 * mm)]
    source = PILImage.open(ROOT / "docs/report/assets/FAST.png").convert("RGBA")
    background = PILImage.new("RGBA", source.size, "white")
    background.alpha_composite(source)
    # Single-ink publication rendition; preserve the downloaded original asset.
    mono = background.convert("L").point(lambda x: 0 if x < 225 else 255, mode="1")
    buffer = BytesIO()
    mono.save(buffer, format="PNG")
    buffer.seek(0)
    image = Image(buffer, width=145 * mm, height=145 * mm * mono.height / mono.width)
    image.hAlign = "CENTER"
    flow += [image, Spacer(1, 16 * mm), Paragraph("SMART RACING<br/>CHAMPIONSHIP", STYLES["Cover"]),
        Paragraph("TECHNICAL REPORT", STYLES["CoverSub"]), Spacer(1, 8 * mm),
        Paragraph("National University of Computer and Emerging Sciences", STYLES["CoverSub"]),
        Paragraph(clean(details["course"]), STYLES["CoverSub"]),
        Paragraph(clean(details["semester"]), STYLES["CoverSub"]), Spacer(1, 9 * mm)]
    blank = "____________________________"
    rows = [["Academic details", ""], ["Campus", details.get("campus") or blank],
            ["Section", details.get("section") or blank], ["Report date", details["report_date"]]]
    flow += [table(rows), Spacer(1, 8 * mm)]
    rows = [["Group member", "Registration number"]]
    for member in details.get("members") or [{"name": blank,"registration":blank}] * 3:
        rows.append([member["name"], member["registration"]])
    flow += [table(rows), Spacer(1, 10 * mm),
        Paragraph("A deterministic racing simulation using graph search, resource optimization,<br/>"
                  "event scheduling and championship ranking algorithms.", STYLES["CoverSub"])]
    return flow


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    details = json.loads((ROOT / "docs/report/report-details.json").read_text())
    document = Report(str(OUTPUT), pagesize=A4, leftMargin=22*mm, rightMargin=22*mm,
        topMargin=29*mm, bottomMargin=29*mm,
        title="Smart Racing Championship - Technical Report",
        author="Smart Racing Championship project group")
    frame = Frame(22*mm, 29*mm, WIDTH, A4[1]-58*mm, leftPadding=0,
                  rightPadding=0, topPadding=0, bottomPadding=0)
    document.addPageTemplates(PageTemplate(id="Report", frames=[frame], onPage=page_frame))
    flow = cover(details)
    flow += [PageBreak(), Paragraph("Contents", STYLES["Major"])]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOCMajor", fontName="Helvetica-Bold", fontSize=9.5, leading=14, spaceBefore=7),
        ParagraphStyle("TOCMinor", fontName="Helvetica", fontSize=8.5, leading=12, leftIndent=12),
    ]
    flow.append(toc)
    text = (ROOT / "docs/report/technical-report.md").read_text(encoding="utf-8")
    text = text[text.index("## 1."):].replace("{{EXPERIMENTS}}", experiment_report())
    flow.extend(markdown_flowables(text))
    document.multiBuild(flow)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
