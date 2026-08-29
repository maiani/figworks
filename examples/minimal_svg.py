from figforge import Figure


fig = Figure(width="100mm", height="60mm", theme="paper")
fig.rect(x="10mm", y="10mm", width="35mm", height="25mm", id="box", fill="none", stroke="black")
fig.text("Native SVG", x="15mm", y="25mm", id="title")
fig.arrow(id="arrow", start=("50mm", "30mm"), end=("80mm", "20mm"))

fig.save("minimal_svg.svg")
fig.save("minimal_svg.pdf")
fig.save("minimal_svg.png")
