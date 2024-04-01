#!/bin/bash

# Paste your Tinybird API Token here
get_token_from_file() {
    local token_file=".tinyb"
    local token

    if [ -f "$token_file" ]; then
        token=$(jq -r '.token' "$token_file")
        echo "$token"
    else
        echo "Token file not found."
    fi
}

AUTH_TOKEN=$(get_token_from_file)

# Base URL for the AIS data files
BASE_URL="https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2020/"

# Starting from January 1st, 2020 to the end of the year
START_DATE="2020-01-01"
END_DATE="2020-12-31"

current=$(date -d "$START_DATE" "+%Y-%m-%d")
while [ "$(date -d "$current" +%Y%m%d)" -le "$(date -d "$END_DATE" +%Y%m%d)" ]; do
    # Formatting the date for the file name
    FILE_DATE=$(date -d "$current" "+%Y_%m_%d")
    FILENAME="AIS_${FILE_DATE}.zip"
    URL="${BASE_URL}${FILENAME}"

    # Download the zip file
    echo "Downloading ${URL}"
    curl -O "${URL}"

    # Unzip the file
    echo "Unzipping ${FILENAME}"
    unzip "${FILENAME}"

    # Assuming the CSV has the same base name as the ZIP file
    CSV_FILENAME="${FILENAME%.*}.csv"

    # Append the data to the Tinybird datasource
    echo "Appending ${CSV_FILENAME} to Tinybird datasource"
    curl -H "Authorization: Bearer ${AUTH_TOKEN}" \
         -X POST "https://api.tinybird.co/v0/datasources?format=csv&name=ais_2020&mode=append" \
         -F "csv=@${CSV_FILENAME}"

    # Clean up: remove the zip and unzipped CSV file
    echo "Cleaning up files"
    rm "${FILENAME}" "${CSV_FILENAME}"

    # Increment the day
    current=$(date -d "$current + 1 day" "+%Y-%m-%d")
done

echo "All files processed."