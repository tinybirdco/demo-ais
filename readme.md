# AIS Demo

This Demo offers a simple exploratory interface over AIS Data.

![Splash Image](assets/readme_splash.png)

## Components

The Dashboard is created using [Dash & Plotly](https://dash.plotly.com/) for the map, [Pandas](https://pandas.pydata.org/) for the frontend data processing, and [Tinybird](https://ui.tinybird.co/signup) for the backend.

## Dataset

The dataset comes from [NOAA](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2020/index.html), and is a few billion vessel observation samples from 2020.


## To Use

1. Checkout this repository
2. Install the requirements.txt in a local pyenv
2. Open your Tinybird Workspace, and grab your User Admin Token, then run `tb auth` into this directory so the scripts can use the token.
3. `tb push` the data project to establish the backend processing structure and serve the data APIs.
4. Use noaa_uploader.sh to append as many of the zipped CSV files as you need to Tinybird for sample data. Jan-May is about 1b rows. 
> ⚠️ **NOTE:** NOAA provide this data for free, so don't abuse their download server
5. Run app.py to have a local Dash app to explore some of the shipping data. The default values should work.

You could also stream in live AIS data following the same format.

## Credits
Created by @Chaffelson and @juliavallina