# bn-backend
Simple backend intended to serve the stations data for bassin-niger frontend app (https://github.com/fgravin/bassin-niger)

##Services 

Retrieve list of stations and their position:
```
http://localhost:5000/services/stations
```

Retrieve water elevation values for station L_kainji2 (experimental source)
```
http://localhost:5000/services/station/experimental/L_kainji2
```

Retrieve water elevation values for station R_nig_tin_s3a_0515_00 (theia-hydroweb source)
```
http://localhost:5000/services/station/theia-hydroweb/R_nig_tin_s3a_0515_00
```

Configuration of the sources is, for now, done in app/app.py in the sources object. 
Data is returned as JSON data

## Configure data sources
Data sources are, by default, configured in the sources.ini file. You will have to adjust the user and password 
definitions int the theia-hydroweb details_uri

You can use your own sources definition file by providing the path with the SOURCES_CONFIG_FILE environment variable. 
For example, using docker, you can mount the file as a volume and provide the corresponding path using the environment 
variable : 
`docker run -p 5000:5000 -it  -v /tmp/sources.ini:/sources.ini -e SOURCES_CONFIG_FILE="/sources.ini" pigeosolutions/bn-backend`
This even allows you to use secrets for your data sources file (best way to protect the authentication params)

## Override configuration
You can override the app's configuration by pointing the env. var FLASK_CONFIG_FILE_PATH to your own configuration file.

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

### Build docker image
`docker build . -t pigeosolutions/bn-backend`

Then you can test it running 
`docker run -p 5000:5000 -it pigeosolutions/bn-backend`
and testing the URLs given above

