with open("earthquakes.csv", "rb") as f:
    raw = f.read()

texto = raw.decode("cp1252", errors="replace")

with open("earthquakes_clean.csv", "w", encoding="utf-8") as f:
    f.write(texto)

print("listo")