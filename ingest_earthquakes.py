import os
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import date
from dotenv import load_dotenv

load_dotenv()

MIN_MAGNITUDE = 4.0
ANIOS = range(date.today().year - 10, date.today().year + 1)

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS earthquakes (
        usgs_id TEXT PRIMARY KEY,
        time TIMESTAMPTZ,
        mag FLOAT8,
        depth FLOAT8,
        place TEXT,
        geom GEOMETRY(Point, 4326),
        en_tierra BOOLEAN,
        continente TEXT
    );
""")
cur.execute("""
    CREATE INDEX IF NOT EXISTS earthquakes_geom_idx
    ON earthquakes USING GIST (geom);
""")
conn.commit()

total = 0

for anio in ANIOS:
    inicio = f"{anio}-01-01"
    fin = f"{anio + 1}-01-01"

    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query"
        f"?format=geojson&starttime={inicio}&endtime={fin}"
        f"&minmagnitude={MIN_MAGNITUDE}"
    )

    respuesta = requests.get(url)
    datos = respuesta.json()

    registros = []
    for feature in datos["features"]:
        props = feature["properties"]
        lon, lat, profundidad = feature["geometry"]["coordinates"]
        registros.append((
            feature["id"],
            props["time"],
            props["mag"],
            profundidad,
            props["place"],
            lon,
            lat,
        ))

    if registros:
        execute_values(
            cur,
            """
            INSERT INTO earthquakes (usgs_id, time, mag, depth, place, geom)
            VALUES %s
            ON CONFLICT (usgs_id) DO NOTHING
            """,
            registros,
            template=(
                "(%s, to_timestamp(%s / 1000.0), %s, %s, %s, "
                "ST_SetSRID(ST_MakePoint(%s, %s), 4326))"
            ),
        )
        conn.commit()

        # Clasificación espacial (tierra/mar, continente) calculada acá, una
        # sola vez por sismo nuevo, en vez de recalcularla cada vez que se
        # exporta el GeoJSON. Solo toca las filas recién insertadas.
        cur.execute("""
            UPDATE earthquakes AS e SET
                en_tierra = EXISTS (
                    SELECT 1 FROM land l WHERE ST_Intersects(e.geom, l.geom)
                ),
                continente = (
                    SELECT c.continent FROM countries c
                    WHERE ST_Intersects(e.geom, c.geom)
                    LIMIT 1
                )
            WHERE e.en_tierra IS NULL;
        """)
        conn.commit()

    print(anio, "->", len(registros), "sismos")
    total += len(registros)

print("total procesado:", total)
