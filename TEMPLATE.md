The AIS Explorer template provides a graphical exploratory interface for automatic identification system (AIS) data.

For any given MMSI, the AIS Explorer shows the vessel's location over selected dates. You can represent location using latitude and longitude, or through H3. You can adjust the H3 resolution to show more or less detail.

## Set up the project

Fork the GitHub repository and deploy the data project to Tinybird.

- Use `noaa_uploader.sh` to append as many of the zipped CSV files as you need to Tinybird for sample data
- Run `app.py` to have a local Dash app to explore some of the shipping data. The default values should work

You could also stream in live AIS data following the same format.
