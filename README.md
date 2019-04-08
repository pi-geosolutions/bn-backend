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

