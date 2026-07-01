World Cities Dataset
====================
Place a `world_cities.csv` file in this directory with the following columns:

  city, region, country, country_code, latitude, longitude

Recommended free source:
  https://simplemaps.com/data/world-cities  (Basic edition — free for commercial use)
  Download `worldcities.csv`, rename to `world_cities.csv`, place here.

Alternatively, the API endpoint `GET /api/locations/search?q=<query>` will
also search the database directly if you pre-seed locations via
`POST /api/locations`.
