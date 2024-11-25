#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sqlalchemy import create_engine, Column, String, Integer, func, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry 
from tqdm import tqdm
from shapely.wkt import dumps
import orjson


# In[2]:


get_ipython().run_cell_magic('time', '', "with open('13_266069_040_003 L02 PAS.json', 'r') as file:\n    data = orjson.loads(file.read())\n\nimport shapely\nfrom shapely.geometry import shape\n")


# In[3]:


data[0]


# In[4]:


# Create a base class for our declarative mapping
Base = declarative_base()

# Define your SQLAlchemy model
class GeometryModel(Base):
    __tablename__ = 'geometries'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    centroid = Column(Geometry('POINT'))
    geom = Column(Geometry('POLYGON'))


# In[5]:


from sqlalchemy_utils import database_exists, create_database
engine = create_engine('postgresql://postgres@localhost:5333/test22')#,echo=True)
print(engine.url)
try:
    create_database(engine.url)
    print("created")
except:
    print("errored")
    pass


# In[6]:


# Initialize Spatialite extension
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    with dbapi_connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS postgis;')


# In[7]:


# Create the table
Base.metadata.create_all(engine)


# In[8]:


from tqdm import tqdm


# In[9]:


get_ipython().run_cell_magic('time', '', 'for _ in range(12):\n    batch_size=5_000\n    polygons=[]\n    with  engine.connect() as conn:\n        tran = conn.begin()\n    \n        for geojson in tqdm(data):\n            name = geojson["properties"]["classification"]["name"]\n            geometry = orjson.dumps(geojson["geometry"]).decode(\'ascii\')\n        \n            polygons.append({\'name\':name,\'geom\':geometry})\n    \n            if len(polygons) == batch_size:\n                # res=conn.execute(\n                #     text("INSERT INTO geometries (name,geom,centroid) VALUES (:name,ST_GeomFromGeoJSON(:geom),ST_Centroid(ST_GeomFromGeoJSON(:geom)));"),polygons)\n\n                #optimized query\n                res=conn.execute(\n                    text("INSERT INTO geometries (name, geom, centroid) SELECT :name, geom, ST_Centroid(geom)  FROM (SELECT ST_GeomFromGeoJSON(:geom) AS geom) AS subquery;"),polygons)\n\n                polygons = []\n                tran.commit()\n                tran = conn.begin()\n    \n        if polygons:\n            # res=conn.execute(\n            #     text("INSERT INTO geometries (name,geom,centroid) VALUES (:name,ST_GeomFromGeoJSON(:geom),ST_Centroid(ST_GeomFromGeoJSON(:geom)));"),polygons)\n\n            #optimized query\n            res=conn.execute(\n                    text("INSERT INTO geometries (name, geom, centroid) SELECT :name, geom, ST_Centroid(geom)  FROM (SELECT ST_GeomFromGeoJSON(:geom) AS geom) AS subquery;"),polygons)\n\n            \n            polygons = []\n            tran.commit()\n')


# In[10]:


get_ipython().run_cell_magic('time', '', '#lets make sure insert worked as expected\nwith  engine.connect() as conn:\n    res=conn.execute(text("select count(geom) from geometries"))\n    nresults=res.fetchall()\n    print(nresults)\n')


# In[11]:


get_ipython().run_cell_magic('time', '', 'with  engine.connect() as conn:\n    res=conn.execute(text("select ST_AsGeoJSON(centroid) as centroid from geometries limit 1000"))\n    centroids=res.fetchall()\n')


# In[12]:


centroids[0:100]


# In[ ]:




