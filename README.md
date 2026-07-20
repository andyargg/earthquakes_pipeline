# Earthquakes Pipeline

Pipeline geoespacial que carga 10 años de sismos globales (USGS, M4+) en PostGIS, los clasifica por tierra/mar y continente con un cruce espacial, y los muestra en un mapa con deck.gl.

Demo: https://proyectoespacial1.vercel.app/map.html

## Qué hace

- `ingest_earthquakes.py` trae los sismos desde el FDSN Event Web Service de USGS y los carga en Postgres junto con las capas de tierra, costa y países de Natural Earth.
- Cada sismo se clasifica (en tierra o mar, continente) al momento de cargarlo, no cada vez que se consulta — así la API que lo sirve es liviana.
- `api/earthquakes.py` es una función serverless que devuelve los sismos filtrados por año y magnitud, comprimidos con gzip.
- `map.html` los dibuja con MapLibre (mapa base) y deck.gl (los puntos, con radio y color según magnitud), con filtros de año, magnitud y continente.

Stack: PostgreSQL/PostGIS en Neon, Python para la ingesta, Vercel para la API y el hosting. Sin build, sin frameworks de frontend.

## Setup local

```
pip install requests psycopg2-binary python-dotenv
cp .env.example .env   # completar con tu DATABASE_URL (Postgres + PostGIS)
```

Cargar `land`, `coastline` y `countries` con `shp2pgsql` (shapefiles de Natural Earth), después:

```
python ingest_earthquakes.py
```

Y para levantar el sitio completo (frontend + API):

```
npm i -g vercel
vercel dev
```

## Nota

Los sismos están sesgados hacia zonas con más estaciones sísmicas (California, Japón, Alaska) — el dataset refleja dónde se detecta mejor, no necesariamente dónde tiembla más.
