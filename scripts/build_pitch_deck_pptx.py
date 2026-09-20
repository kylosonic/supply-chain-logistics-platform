"""Generate the EAII pitch deck as a native, editable PowerPoint file.

7 slides covering the 10 required EAII sections. All text is native PowerPoint
text (no images of text), so reviewers can edit or reuse it.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).resolve().parent.parent / 'docs' / 'eaii' / 'FreightPilot-EAII-Pitch-Deck.pptx'

INK = RGBColor(0x0B, 0x12, 0x20)
TEXT = RGBColor(0xE8, 0xEE, 0xF9)
MUTED = RGBColor(0x9F, 0xB0, 0xCC)
ACCENT = RGBColor(0x38, 0xBD, 0xF8)
GOOD = RGBColor(0x34, 0xD3, 0x99)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide():
    slide = prs.slides.add_slide(BLANK)
    bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = INK
    bg.line.fill.background()
    bg.shadow.inherit = False
    return slide


def textbox(slide, left, top, width, height, *, text='', size=12, bold=False,
            color=TEXT, align=PP_ALIGN.LEFT, spacing=1.0, font='Segoe UI'):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    para = frame.paragraphs[0]
    para.text = text
    para.alignment = align
    para.line_spacing = spacing
    run = para.runs[0] if para.runs else para.add_run()
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    return frame


def bullets(slide, left, top, width, height, items, *, size=11, color=MUTED,
            bullet_color=ACCENT, spacing=1.18):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    for index, item in enumerate(items):
        para = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        para.text = f'■  {item}'
        para.line_spacing = spacing
        para.space_after = Pt(5)
        for run in para.runs:
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.name = 'Segoe UI'
    return frame


def eyebrow(slide, text):
    textbox(slide, 0.62, 0.34, 12.0, 0.32, text=text.upper(), size=10.5, bold=True, color=ACCENT)


def title(slide, text, *, top=0.72, size=25, width=12.1):
    textbox(slide, 0.62, top, width, 1.15, text=text, size=size, bold=True, color=WHITE, spacing=1.03)


def footer(slide, number, label):
    line = slide.shapes.add_shape(1, Inches(0.62), Inches(6.94), Inches(12.1), Emu(9525))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(0x2A, 0x3A, 0x58)
    line.line.fill.background()
    line.shadow.inherit = False
    textbox(slide, 0.62, 7.02, 6.0, 0.3, text='FREIGHTPILOT', size=9, bold=True, color=MUTED)
    textbox(slide, 7.0, 7.02, 5.72, 0.3, text=f'Slide {number} of 7 · {label}',
            size=9, color=RGBColor(0x64, 0x74, 0x8B), align=PP_ALIGN.RIGHT)


def card(slide, left, top, width, height, heading, lines, *, size=10.5):
    box = slide.shapes.add_shape(5, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x13, 0x1D, 0x30)
    box.line.color.rgb = RGBColor(0x2A, 0x3A, 0x58)
    box.line.width = Pt(0.75)
    box.shadow.inherit = False
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = Inches(0.14)
    frame.margin_right = Inches(0.14)
    frame.margin_top = Inches(0.1)
    para = frame.paragraphs[0]
    para.text = heading
    for run in para.runs:
        run.font.size = Pt(size + 1.5)
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = 'Segoe UI'
    for line in lines:
        sub = frame.add_paragraph()
        sub.text = line
        sub.line_spacing = 1.16
        sub.space_before = Pt(4)
        for run in sub.runs:
            run.font.size = Pt(size)
            run.font.color.rgb = MUTED
            run.font.name = 'Segoe UI'
    return box


# ---------------------------------------------------------------------------
# Slide 1 — 1 Problem, 2 Solution
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, 'FreightPilot · EAII Second-Round Submission')
title(s, 'Ethiopian logistics teams run on spreadsheets,\nphone calls and guesswork.')
card(s, 0.62, 2.02, 6.0, 4.4, '1 · The problem', [
    'An Ethiopian freight and distribution operator plans routes in Excel, learns about a delayed truck by phone, and discovers a stock-out only when a customer complains.',
    '■  Routes are planned by habit — no repeatable way to weigh distance, time, cost and capacity.',
    '■  Exceptions arrive too late — delays and low stock surface after the money is lost.',
    '■  Cash is reconciled by hand — bank-transfer receipts matched to invoices manually, with no audit trail.',
    '■  Data lives in files — warehouses, items, fleet and orders sit in disconnected CSVs nobody trusts.',
])
card(s, 6.86, 2.02, 5.86, 4.4, '2 · The solution', [
    'FreightPilot is one operator surface that takes a logistics team from signup to a planned, monitored, reconciled day of operations.',
    '',
    '01 Onboard — company workspace in one form.',
    '02 Import — warehouses, items, fleet, inventory, orders by CSV.',
    '03 Optimize — weighted route plans on real geography.',
    '04 Monitor — live feed, alerts, exception queue.',
    '05 Reconcile — receipts, wallet and audit trail.',
    '',
    'Built and verified: 81 live API endpoints · 4 deployable surfaces · 19 schema migrations · 604 automated tests.',
])
footer(s, 1, 'Problem & Solution')

# ---------------------------------------------------------------------------
# Slide 2 — 3 Market Opportunity
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '3 · Market Opportunity')
title(s, 'A large, underserved operator base that is already digitising —\njust not with software built for it.')
card(s, 0.62, 2.1, 6.0, 4.3, 'Who we sell to', [
    'Primary: Ethiopian freight forwarders, distributors and 3PL operators running 5–50 vehicles and 1–10 warehouses.',
    'Buyer: the owner or operations manager — one person who feels route cost, stock-outs and cash reconciliation every week.',
    'Users per account: 3–25 (dispatchers, warehouse operators, finance, owners).',
])
card(s, 6.86, 2.1, 5.86, 4.3, 'Why now', [
    'Digital payments reached operational scale, so receipt-to-invoice reconciliation is now a real software problem.',
    'Smartphone and 3G coverage is good enough for a browser console — no desktop install required to start.',
    'Incumbents are priced and shaped for other markets: global TMS products assume carrier-settlement breadth and English-first workflows a 20-truck operator cannot absorb.',
    '',
    'Entry market is countable: low thousands of serviceable operators. This is a wedge into a regional logistics-software market, not a bet on one country.',
])
footer(s, 2, 'Market Opportunity')

# ---------------------------------------------------------------------------
# Slide 3 — 4 Traction, 5 Business Model
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '4 · Traction   ·   5 · Business Model')
title(s, 'A production platform, verified end to end —\nand a business model wired into the product.')
metrics = [
    ('399', 'backend tests passing on the\nlocked dependency set'),
    ('205', 'console (143) + website (62)\ntests passing'),
    ('22/22', 'launch-funnel steps verified\nend to end'),
    ('0', 'known vulnerabilities in the\ndeployed dependency set'),
]
for index, (value, label) in enumerate(metrics):
    left = 0.62 + index * 3.06
    box = s.shapes.add_shape(5, Inches(left), Inches(2.02), Inches(2.9), Inches(1.34))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x13, 0x1D, 0x30)
    box.line.color.rgb = RGBColor(0x2A, 0x3A, 0x58)
    box.line.width = Pt(0.75)
    box.shadow.inherit = False
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = Inches(0.12)
    para = frame.paragraphs[0]
    para.text = value
    for run in para.runs:
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = 'Segoe UI'
    sub = frame.add_paragraph()
    sub.text = label
    sub.line_spacing = 1.1
    for run in sub.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = MUTED
        run.font.name = 'Segoe UI'
card(s, 0.62, 3.52, 6.0, 3.2 if False else 2.9, 'Traction — what is actually built and proven', [
    'Signup to first route plan works: workspace created, sample data seeded, first optimisation returned a real plan — 21.07 km, 31.61 ETB — and persisted to route history.',
    'Multi-tenant isolation is enforced and regression-tested: a second organisation cannot list, read or mutate the first organisation\'s rows; cross-tenant reads answer 404, never 403.',
    'Cashflow operations ship: receipt ingestion, wallet credits, reversible audit trail, dispute threads, admin verification queue.',
    'Commercial controls ship: subscription tiers, metered usage with 80%/100%/overage events, BYOK provider-key management.',
])
card(s, 6.86, 3.52, 5.86, 2.9, 'Business model — B2B SaaS per workspace', [
    'Subscription: tiered plans with a free entry tier that onboards a real workspace on sample data.',
    'Usage metering: delivery tasks and route optimisations are metered, with threshold events at 80%, 100% and overage.',
    'Expansion: tier upgrade when a workspace outgrows its included units.',
    'Bring-your-own-key: customers attach their own AI provider key, so inference cost scales with the customer, not with us.',
])
footer(s, 3, 'Traction & Business Model')

# ---------------------------------------------------------------------------
# Slide 4 — 6 Go-to-Market, 7 Competition
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '6 · Go-to-Market   ·   7 · Competition')
title(s, 'Land with a free working workspace.\nExpand on the operator\'s own numbers.')
card(s, 0.62, 2.02, 6.0, 4.4, 'Go-to-market: product-led land, operator-led expand', [
    'Land — a prospect signs up with a business email and lands in a workspace already seeded with sample operational data. Route value is visible in the first session, before procurement.',
    'Activate — the product tracks a five-step activation path and shows exactly what is still sample data versus the operator\'s own uploads.',
    'Prove — the first route optimisation is the "aha": distance, cost and stops the operator can act on today.',
    'Expand — metered usage crossing 80% and 100% is the natural upgrade moment, surfaced in-product.',
    'Channel — logistics associations, freight-forwarding communities, founder-led onboarding of design partners.',
])
card(s, 6.86, 2.02, 5.86, 4.4, 'Competition', [
    'Spreadsheets — universal and free, but no route optimisation, no exception detection, no audit trail, no shared state across roles.',
    'Global TMS / routing suites — deep at enterprise breadth, but shaped for carrier settlement and large fleets, priced and configured beyond a 20-vehicle operator.',
    'Local point tools — single-purpose (GPS tracking, accounting); the operator still stitches tools together.',
    'Generic ERP add-ons — broad back office; we are the operational layer an ERP does not cover.',
    '',
    'Defensible position: tenant-safe operational software (scoping enforced on every surface and pinned by regression tests) and receipt-to-cashflow reconciliation tuned to Ethiopian bank-transfer reality.',
])
footer(s, 4, 'Go-to-Market & Competition')

# ---------------------------------------------------------------------------
# Slide 5 — 8 Core Team and Advisor
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '8 · Core Team and Advisor')
title(s, 'A small team with an engineered product —\nand named gaps we intend to fill with this program.')
card(s, 0.62, 2.1, 6.0, 4.3, 'Core team', [
    'Founder / CEO — product direction, customer discovery with Ethiopian operators, commercial model and pricing, fundraising.',
    'Engineering — four deployable surfaces (FastAPI platform API, React operations console, Next.js product site, Electron desktop shell), the data model, and release engineering, delivered with QA and security gates on every change.',
    '',
    'Concretely: 11,236 lines of Python across 23 API modules, 8,666 lines of TypeScript across the console, a 19-migration schema, 81 live endpoints and 604 automated tests — with an audit trail recording each security finding and its remediation evidence.',
])
card(s, 6.86, 2.1, 5.86, 4.3, 'Advisors — declared honestly', [
    'We are not padding this slide. What we have today:',
    '',
    '■  Design-partner operators — working relationships with logistics operators who review workflows and validate whether the product matches how they actually run a day.',
    '',
    '■  Domain validation on cashflow — receipt verification is built against published CBE and Dashen transfer practice, with one human verification gate still open before paid launch.',
    '',
    'What we seek from EAII: an advisor or mentor with logistics-operations depth in Ethiopia or comparable East African markets, and a go-to-market advisor for B2B SaaS sold into owner-operated firms.',
])
footer(s, 5, 'Core Team and Advisor')

# ---------------------------------------------------------------------------
# Slide 6 — 9 Financial Projection
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '9 · Financial Projection')
title(s, 'Plan built from cost we control and customers we can name —\nnot from a growth curve.')
card(s, 0.62, 2.1, 6.0, 4.3, 'Where the money goes (next 12 months)', [
    'Cloud & database — three Vercel projects plus managed Postgres. Low and variable; scales with usage, not headcount.',
    'AI inference — receipt extraction only. Customer-funded via bring-your-own-key, so it is not a fixed cost.',
    'Team — founder plus engineering. The largest line; program support extends runway rather than expanding headcount.',
    'Customer acquisition — founder-led plus community. Deliberately near-zero paid spend at this stage.',
    '',
    'Cost-structure advantage: because inference and heavy compute are customer-funded or usage-metered, cost to serve a new workspace is close to flat, and gross margin improves with tier rather than volume alone.',
])
card(s, 6.86, 2.1, 5.86, 4.3, 'Revenue projection logic (named-account capacity)', [
    'Months 1–3 — design partners. Onboard a small cohort of Ethiopian operators on the free tier; convert on validated value. Target: first paid workspaces.',
    'Months 4–8 — repeatable onboarding. The activation path becomes self-serve: fewer founder hours per workspace, more workspaces per month.',
    'Months 9–12 — metered expansion. Existing workspaces cross their included unit threshold and upgrade; net revenue retention becomes the primary growth lever.',
    '',
    'Three metrics we manage the business on: time to first route plan (activation) · workspaces crossing 80% of included units (expansion) · net revenue retention (health).',
    '',
    'Honesty rule: the projection states explicit assumptions and named levers; month-by-month figures with underlying assumptions are provided in the data room.',
])
footer(s, 6, 'Financial Projection')

# ---------------------------------------------------------------------------
# Slide 7 — 10 The Ask
# ---------------------------------------------------------------------------
s = add_slide()
eyebrow(s, '10 · The Ask')
title(s, 'We are asking for the support that turns a working platform\ninto a repeatable business.')
card(s, 0.62, 2.02, 6.0, 4.4, 'What we are asking EAII for', [
    'Domain mentorship — a logistics-operations advisor who has run freight or distribution in Ethiopia or a comparable market, to pressure-test our workflows against how operators really work.',
    'Go-to-market support — converting founder-led onboarding into a repeatable sales motion for owner-operated firms, plus introductions to a first cohort of paying customers.',
    'Cashflow-gate resolution — support closing the one remaining human verification: confirming CBE and Dashen transfer fee schedules in the 5,000–50,000 ETB band against our ±1,000 ETB tolerance. This blocks paid launch, not the product.',
    'Fundraising readiness — structured preparation for a seed conversation: metrics narrative, data room, investor introductions.',
])
card(s, 6.86, 2.02, 5.86, 2.2, 'What we bring', [
    'A shipped product, not a prototype: live website, operations console and API, plus a desktop shell.',
    'Engineering discipline the program can audit: 604 automated tests, hash-verified dependency lockfiles, CI gates on every push, and a written security audit with findings remediated.',
    'Full-time founder commitment — available five days per week for the duration of the program (requirement is a minimum of three).',
])
card(s, 6.86, 4.36, 5.86, 2.06, 'Where we are, stated plainly', [
    'Pre-revenue, post-product. The platform is built and verified; the open work is commercial validation and one human verification gate.',
    '',
    'That is exactly the stage where accelerator support changes the outcome — and every number in this deck is reproducible from the repository and the running platform.',
])
footer(s, 7, 'The Ask')

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f'wrote {OUT} ({OUT.stat().st_size} bytes, {len(prs.slides.__iter__.__self__._sldIdLst)} slides)')
