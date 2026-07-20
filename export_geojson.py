import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(
            json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(geom)::json,
                'properties', json_build_object(
                    'mag', mag,
                    'place', place,
                    'time', time,
                    'year', EXTRACT(YEAR FROM time)::int,
                    'en_tierra', en_tierra,
                    'continente', continente
                )
            )
        )
    )
    FROM earthquakes e
    -- Excluidos: caen cerca de las Islas Kerguelen, donde el polígono de
    -- "Fr. S. Antarctic Lands" a 50m de resolución está generalizado y los
    -- clasifica como tierra pese a estar en el mar. Dos casos aislados, no
    -- vale la pena migrar todo el dataset a 10m por esto.
    WHERE e.usgs_id NOT IN ('us2000b26p', 'us1000aupt');
""")

resultado = cur.fetchone()[0]

with open("earthquakes.geojson", "w", encoding="utf-8") as f:
    json.dump(resultado, f)

print("archivo escrito")