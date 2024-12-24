This template offers a simple exploratory interface over AIS Data.

For a chosen [MMSI](https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity), it shows the vessel location over chosen dates. Location can be represented with latitude and longitude, or with [H3](https://h3geo.org/). The H3 resolution can be adjusted to show more or less detail.

## 1. Set up the project

Fork the GitHub repository and deploy the data project to Tinybird.

Use `noaa_uploader.sh` to append as many of the zipped CSV files as you need to Tinybird for sample data

**NOTE:** NOAA provide this data for free, so don't abuse their download server

Run `app.py` to have a local Dash app to explore some of the shipping data. The default values should work

You could also stream in live AIS data following the same format.

## 2. Components

The Dashboard is created using [Dash & Plotly](https://dash.plotly.com/) for the map, [Pandas](https://pandas.pydata.org/) for the frontend data processing, and [Tinybird](https://ui.tinybird.co/signup) for the backend.

## 3. Dataset

The dataset comes from [NOAA](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2020/index.html), and is a few billion vessel observation samples from 2020.

## 4. Learn more

To learn more about this template check out the [README](https://github.com/tinybirdco/demo-ais/blob/main/readme.md).

## 5. Support

If you have any questions or need help, please reach out to us on [Slack](https://www.tinybird.co/join-our-slack-community) or [email](mailto:support@tinybird.co).
