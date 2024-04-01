# AIS Demo

## To use

1. Install the requirements.txt in a local pyenv
2. `tb auth` with your Workspace Admin Token into this directory so the scripts can use the token.
3. Either `tb push` the data project, or use the AIS_sample.csv file to create a Datasource named ais_2020 in a Tinybird workspace and build your own from there.
4. Use noaa_uploader.sh to append as many of the zipped CSV files as you need for sample data. Jan-May is about 1b rows.
5. Run app.py to have a local Dash app to explore some of the shipping data. The default values should work.