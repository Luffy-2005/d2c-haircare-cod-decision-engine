"""
Convert BUSINESS_MEMO.md into an executive styled HTML suitable for 1-click PDF printing.
"""

import os
import sys

def convert_memo_to_html(md_path="docs/BUSINESS_MEMO.md", html_path="docs/BUSINESS_MEMO.html"):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Simple clean converter for markdown headings, bold, tables, lists
    lines = md_text.split("\n")
    html_lines = []
    in_table = False

    for line in lines:
        l = line.strip()
        if not l:
            if in_table:
                html_lines.append("</table>")
                in_table = False
            html_lines.append("<br>")
            continue

        if l.startswith("# "):
            html_lines.append(f"<h1 class='memo-title'>{l[2:]}</h1>")
        elif l.startswith("### "):
            html_lines.append(f"<h3 class='section-title'>{l[4:]}</h3>")
        elif l.startswith("#### "):
            html_lines.append(f"<h4 class='sub-title'>{l[5:]}</h4>")
        elif l.startswith("**TO:**") or l.startswith("**FROM:**") or l.startswith("**DATE:**") or l.startswith("**SUBJECT:**"):
            html_lines.append(f"<div class='memo-meta'>{l.replace('**', '<strong>', 1).replace('**', '</strong>', 1)}</div>")
        elif l.startswith("---"):
            html_lines.append("<hr class='divider'>")
        elif l.startswith("|") and "|" in l[1:]:
            if "---" in l:
                continue
            cols = [c.strip() for c in l.split("|")[1:-1]]
            if not in_table:
                in_table = True
                html_lines.append("<table class='memo-table'><thead><tr>")
                for c in cols:
                    html_lines.append(f"<th>{c}</th>")
                html_lines.append("</tr></thead><tbody>")
            else:
                html_lines.append("<tr>")
                for c in cols:
                    html_lines.append(f"<td>{c}</td>")
                html_lines.append("</tr>")
        elif l.startswith("* ") or l.startswith("- "):
            html_lines.append(f"<li class='memo-li'>{l[2:]}</li>")
        elif l.startswith("1. ") or l.startswith("2. ") or l.startswith("3. "):
            html_lines.append(f"<div class='memo-numbered'><strong>{l[:3]}</strong> {l[3:]}</div>")
        elif l.startswith("```"):
            html_lines.append("<pre class='memo-code'>") if not in_table else None
        else:
            formatted = l.replace("**", "<strong>").replace("**", "</strong>")
            html_lines.append(f"<p class='memo-p'>{formatted}</p>")

    if in_table:
        html_lines.append("</tbody></table>")

    body_content = "\n".join(html_lines)

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Executive Business Memo - COD Optimization</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm 18mm 18mm 18mm;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #1e293b;
      line-height: 1.5;
      max-width: 840px;
      margin: 0 auto;
      padding: 30px;
      font-size: 13.5px;
    }}
    .memo-title {{
      font-size: 22px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.5px;
      margin-bottom: 14px;
      text-transform: uppercase;
      border-bottom: 3px solid #10b981;
      padding-bottom: 8px;
    }}
    .memo-meta {{
      font-size: 13px;
      color: #334155;
      margin-bottom: 4px;
    }}
    .divider {{
      border: none;
      border-top: 1px solid #cbd5e1;
      margin: 16px 0;
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 700;
      color: #0f172a;
      margin-top: 20px;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      border-left: 4px solid #10b981;
      padding-left: 8px;
    }}
    .sub-title {{
      font-size: 14px;
      font-weight: 700;
      color: #334155;
      margin-top: 12px;
      margin-bottom: 6px;
    }}
    .memo-p {{
      margin-bottom: 10px;
      text-align: justify;
    }}
    .memo-li {{
      margin-left: 20px;
      margin-bottom: 6px;
    }}
    .memo-numbered {{
      margin-top: 10px;
      margin-bottom: 6px;
    }}
    .memo-table {{
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0;
      font-size: 12.5px;
    }}
    .memo-table th {{
      background: #f1f5f9;
      color: #0f172a;
      padding: 8px 10px;
      border: 1px solid #cbd5e1;
      font-weight: 700;
      text-align: left;
    }}
    .memo-table td {{
      padding: 8px 10px;
      border: 1px solid #cbd5e1;
      vertical-align: top;
    }}
    .memo-code {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 10px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 12px;
      margin: 10px 0;
    }}
    @media print {{
      body {{ padding: 0; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="no-print" style="background:#ecfdf5; border:1px solid #a7f3d0; padding:12px; border-radius:8px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
    <span style="color:#065f46; font-size:13px; font-weight:600;">📄 Executive Memo Print View (A4 Formatted)</span>
    <button onclick="window.print()" style="background:#10b981; color:#fff; border:none; padding:8px 16px; border-radius:6px; font-weight:700; cursor:pointer;">Print to PDF (Ctrl+P)</button>
  </div>
  {body_content}
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"Executive HTML memo generated at: {html_path}")

if __name__ == "__main__":
    convert_memo_to_html()
