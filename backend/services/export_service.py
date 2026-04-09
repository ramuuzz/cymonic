import io
from typing import List, Dict
import pandas as pd
from fpdf import FPDF


def export_csv(items: List[Dict]) -> bytes:
    df = pd.DataFrame(items)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def _safe_text(text: str) -> str:
    if not text:
        return ""
    replacements = {
        '—': '-', '–': '-',
        '“': '"', '”': '"', 
        '‘': "'", '’': "'",
        '…': '...',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')


def export_pdf(items: List[Dict], meeting_name: str = "Meeting") -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe_text(f"{meeting_name} - Extracted Items"), ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Total items: {len(items)}", ln=True)
    pdf.ln(5)

    decisions = [i for i in items if i.get("type") == "decision"]
    actions = [i for i in items if i.get("type") == "action_item"]

    if decisions:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Decisions", ln=True)
        pdf.ln(2)
        for idx, d in enumerate(decisions, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, f"{idx}. Decision", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _safe_text(f"   {d.get('description', '')}"))
            pdf.ln(3)

    if actions:
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Action Items", ln=True)
        pdf.ln(2)
        for idx, a in enumerate(actions, 1):
            owner = a.get("owner", "Unassigned")
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, _safe_text(f"{idx}. [{owner}]"), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, _safe_text(f"   {a.get('description', '')}"))
            due = a.get("due_date", "")
            if due:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 6, _safe_text(f"   Due: {due}"), ln=True)
            pdf.ln(3)

    return pdf.output()
