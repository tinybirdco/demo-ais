# AIS Explorer template for Tinybird

The AIS Explorer template provides a graphical exploratory interface for automatic identification system (AIS) data.

![Splash Image](assets/readme_splash.png)

For any given [MMSI](https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity), the AIS Explorer shows the vessel's location over selected dates. You can represent location using latitude and longitude, or through [H3](https://h3geo.org/). You can adjust the H3 resolution to show more or less detail.

## Deploy on Tinybird

To deploy this template on Tinybird, open https://app.tinybird.co/?starter_kit=https%3A%2F%2Fgithub.com%2Ftinybirdco%2Fdemo-ais in your browser.

## Local deployment

To work on this project in your local environment, follow these steps:

1. Clone this repository.
2. Create a Python virtual env using `python -m venv .venv && source ./.venv/bin/activate`.
3. Install the Python dependencies by running `pip install -r requirements.txt`.
4. Open or create a [Tinybird](https://www.tinybird.co/) Workspace.
5. Open the [Tinybird Auth Token](https://www.tinybird.co/docs/get-started/administration/auth-tokens) page and copy the User Admin Token.
6. Run `tb auth` in the repo directory and paste the token.
7. Run `tb push` to establish the backend processing structure and serve the data APIs.
8. Use `noaa_uploader.sh` to append as many of the zipped CSV files as you need to Tinybird for sample data. Jan-May is about 1b rows. You might need `jq` installed: `sudo apt-get update && sudo apt-get install jq -y --no-install-recommends` or `brew install jq` for macOS.
9. Run `app.py` to have a local app to explore some of the shipping data. The default values should work.

You can also stream in live AIS data following the same format.

## Components

AIS Explorer uses [Dash and Plotly](https://dash.plotly.com/) for the map, [Pandas](https://pandas.pydata.org/) for the frontend data processing, and [Tinybird](https://ui.tinybird.co/signup) for the backend.

## Dataset

The dataset comes from [NOAA](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2020/index.html). It contains a few billion vessel observation samples from 2020.

## Credits

Created by [@Chaffelson](https://github.com/Chaffelson), [@juliavallina](https://github.com/juliavallina), [@sdairs](https://github.com/sdairs), and  [@rbarbadillo](https://github.com/rbarbadillo).
