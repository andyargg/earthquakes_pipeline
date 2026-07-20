# Earthquakes Pipeline

A geospatial data pipeline that ingests 10 years of global earthquake history into PostGIS, classifies each event spatially (on land vs. ocean, continent), and serves it to an interactive WebGL map.

**Live demo:** https://proyectoespacial1.vercel.app/map.html

## What it does

- Pulls the last 10 years of M4.0+ earthquakes from the [USGS FDSN Event Web Service](https://earthquake.usgs.gov/fdsnws/event/1/).
- Loads them into PostGIS alongside [Natural Earth](https://www.naturalearthdata.com/) land, coastline and country boundary layers.
- Classifies each earthquake against those layers with spatial joins (`ST_Intersects`) — on land or in the ocean, and which continent — computed once at ingestion time, not on every read.
- Serves a filtered subset (by year and magnitude) through a serverless API, gzip-compressed to fit within response size limits.
- Renders the result with [MapLibre GL JS](https://maplibre.org/) (base map) and [deck.gl](https://deck.gl/) (WebGL point layer, radius/color scaled by magnitude), with year, magnitude and continent filters.

## Stack

- **Database:** PostgreSQL + PostGIS ([Neon](https://neon.tech), serverless Postgres)
- **Ingestion:** Python (`psycopg2`, `requests`)
- **API:** Python serverless function (Vercel)
- **Frontend:** Static HTML + MapLibre GL JS + deck.gl (no build step)
- **Hosting:** Vercel

## Project structure

```
ingest_earthquakes.py   # Pulls USGS data, loads it into Postgres, classifies land/continent
export_geojson.py       # One-off local export to a static GeoJSON file (for offline testing)
api/earthquakes.py      # Serverless endpoint: filtered, gzip-compressed GeoJSON
map.html                # Frontend: MapLibre + deck.gl
```

## Running it locally

1. Clone the repo and install dependencies (a `pyproject.toml` is included):
   ```
   pip install -r <(python -c "import tomllib;print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))")
   ```
   or simply install `requests`, `psycopg2-binary` and `python-dotenv`.

2. Copy `.env.example` to `.env` and set `DATABASE_URL` to a Postgres instance with the PostGIS extension enabled.

3. Load the reference geometry (Natural Earth land, coastline and country shapefiles) into `land`, `coastline` and `countries` tables — see `ingest_earthquakes.py` for the expected schema of `earthquakes`; the other tables are loaded via `shp2pgsql`.

4. Run the ingestion:
   ```
   python ingest_earthquakes.py
   ```

5. Install the [Vercel CLI](https://vercel.com/docs/cli) and run the app (serves both the static frontend and the API function):
   ```
   vercel dev
   ```

## Notes

- Earthquake locations are biased toward regions with dense seismic monitoring networks (California, Alaska, Japan); the dataset reflects reporting density, not just tectonic activity.
- Two earthquakes near the Kerguelen Islands are excluded from the API response — Natural Earth's 50m-resolution boundary for that territory is generalized enough to misclassify them as on land.
