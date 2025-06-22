import json

site_1 = json.dumps({
    "SITE": "Pumphouse Name",
    "API_KEY": "secret key", 
    "DATABASE_FULLPATH": "/opt/pumphouse/DB/dbname.db",
    "SERVER": 'https://server.com/api',
})

default = json.dumps({
    "SITE": "Pumphouse Development",
    "API_KEY": "secret key", 
    "DATABASE_FULLPATH": "/opt/pumphouse/DB/pumphouse1.db",
    "SERVER": 'https://server.com/api',
})

location = {
    "location_1_wifi": site_1,
    "location_2_wifi": site_1,
    "default": default,
    }

    

    
