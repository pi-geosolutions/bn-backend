# bn-backend
Simple backend intended to serve the stations data for bassin-niger frontend app (https://github.com/fgravin/bassin-niger)

## API

Data is returned as JSON data

**/api/v1/sources**: get the list of available sources

**/api/v1/sources/<source_id>**: get definition of the source matching the given id

**/api/v1/sources/<source_id>/stations**: get the list of stations for given data source id (geojson)

**/api/v1/sources/<source_id>/stations/<station_id>**: get station definition for given data source id and station id. 
station_id is given by the `productIdentifier` field in the station definition (geojson)

**/api/v1/sources/<source_id>/stations/<station_id>?scope=data**: get the station's altimetric data (historical data)

**/api/v1/stations**: get the merged list of stations from all sources (geojson)

## Configure data sources
Data sources are, by default, configured in the sources.ini file. You will have to adjust the user and password 
definitions in the theia-hydroweb details_uri

### Providing credentials as environment variables
The http://hydroweb.theia-land.fr/hydroweb service, for instance, requires you to provide user credentials. You *should 
not provide them in the source.ini file* , as this will be shown on the /api/v1/sources endpoint. Instead, you are 
advised to use environment variables. When the service meets a {{ MY_VAR }} token, it tries to replace it by the 
corresponding environment variable. For instance, 
`details_uri= http://hydroweb.theia-land.fr/hydroweb/authdownload?products={id}&user={{HYDROWEB_USER}}&pwd={{HYDROWEB_PASSWORD}}&format=txt` will look for 
HYDROWEB_USER and HYDROWEB_PASSWORD environment variables and replace them if they are defined.

The /api/v1/sources endpoint will still show the raw uri, keeping prying eyes from your super secure password.

### Specify the sources.ini file location 
You can use your own sources definition file by providing the path with the SOURCES_CONFIG_FILE environment variable. 
For example, using docker, you can mount the file as a volume and provide the corresponding path using the environment 
variable : 
`docker run -p 5000:5000 -it  -v /tmp/sources.ini:/sources.ini -e SOURCES_CONFIG_FILE="/sources.ini" pigeosolutions/bn-backend`
This even allows you to use secrets for your data sources file (best way to protect the authentication params)

## Override configuration
You can override the app's configuration by pointing the env. var FLASK_CONFIG_FILE_PATH to your own configuration file.

## Override configuration using Environment Variables
The following other environment variables are supported:
* SOURCES_CONFIG_FILE: path to the sources definition file
* FLASK_CONFIG_FILE_PATH: path to the global config file for the app
* STORAGE_PATH: path on the filesystem where the files will be written. The user running the app needs write access on 
this path

## Dev setup

### Set-up python environment
Create a virtualenv in the root folder, then activate it
```
virtualenv .venv && \
. .venv/bin/activate
```
and install the python packages
```
pip install -r requirements.txt
```

### Run
`python app/main.py`
Then open http://localhost:5000/api/v1/sources

Or using docker:
```
docker run -p 5000:5000 -it  -v [PATH TO YOUR SOURCES FILE]/datasources.ini:/sources.ini -e SOURCES_CONFIG_FILE="/sources.ini" -v [PATH TO YOUR DATA FOLDER]/data:/mnt/data   pigeosolutions/bn-backend
```

### Build docker image
`docker build . -t pigeosolutions/bn-backend`

Then you can test it running 
`docker run -p 5000:5000 -it pigeosolutions/bn-backend`
and testing the URLs given above

