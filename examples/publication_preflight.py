"""A readable preflight report for a figure with deliberately small labels."""

from figworks import Figure

figure = Figure("85mm", "45mm")
figure.text("Too small after placement", "10mm", "15mm", id="caption", font_size="4pt")
figure.line(
    x1="10mm", y1="20mm", x2="65mm", y2="20mm", stroke="black", stroke_width="0.1pt", id="curve"
)
figure.rect(x="80mm", y="25mm", width="15mm", height="10mm", id="outside")

report = figure.check()
for issue in report.issues:
    print(f"{issue.severity}: {issue.code} [{issue.element_id or issue.path}] {issue.message}")
for limitation in report.unchecked:
    print(f"Not checked: {limitation}")
# Warnings are review decisions; structural/font errors can block a build.
report.raise_for_errors()
