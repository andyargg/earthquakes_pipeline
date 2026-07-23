import os
import json
import gzip
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psycopg2

QUERY = """
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(
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
        ), '[]'::json)
    )
    FROM earthquakes
    WHERE usgs_id NOT IN ('us2000b26p', 'us1000aupt')
      AND time >= %(date_min)s
      AND time < %(date_max)s::date + INTERVAL '1 day'
      AND mag BETWEEN %(mag_min)s AND %(mag_max)s;
"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)

        filtros = {
            "date_min": params.get("date_min", ["2015-01-01"])[0],
            "date_max": params.get("date_max", ["2026-12-31"])[0],
            "mag_min": float(params.get("mag_min", [4.0])[0]),
            "mag_max": float(params.get("mag_max", [10.0])[0]),
        }

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(QUERY, filtros)
        resultado = cur.fetchone()[0]
        cur.close()
        conn.close()

        cuerpo = gzip.compress(json.dumps(resultado).encode("utf-8"))

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(cuerpo)
        return
