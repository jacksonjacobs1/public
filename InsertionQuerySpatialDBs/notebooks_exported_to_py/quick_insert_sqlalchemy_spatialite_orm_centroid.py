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


# Connect to the Spatialite database
db_path = 'sqlite:////tmp/blog/spatialite_core_orm.db'
engine = create_engine(db_path, echo=False)  # Set echo=True to see SQL commands being executed


# In[6]:


# Initialize Spatialite extension
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    dbapi_connection.enable_load_extension(True)
    dbapi_connection.execute('SELECT load_extension("mod_spatialite")')
    dbapi_connection.execute('SELECT InitSpatialMetaData(1);')


# In[7]:


# Create the table
Base.metadata.create_all(engine)

# Start a session
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()


# In[8]:


from tqdm import tqdm


# In[9]:


get_ipython().run_cell_magic('time', '', 'for _ in range(12):\n    batch_size=5_000\n    polygons=[]\n    with  engine.connect() as conn:\n        for geojson in tqdm(data):\n            name = geojson["properties"]["classification"]["name"]\n            shapely_geom = shape(geojson["geometry"])\n            \n            polygons.append(GeometryModel(name=name, geom=shapely_geom.wkt,centroid=shapely_geom.centroid.wkt))\n        \n            if len(polygons) == batch_size:\n                session.bulk_save_objects(polygons)\n                session.commit()\n                polygons.clear()  # Clear the list for the next batch\n        \n        # Insert any remaining records that didn\'t fit into the final batch\n        if polygons:\n            session.bulk_save_objects(polygons)\n            session.commit()\nsession.close()\n')


# In[10]:


get_ipython().run_cell_magic('time', '', '#lets make sure insert worked as expected\nwith  engine.connect() as conn:\n    res=conn.execute(text("select count(geom) from geometries"))\n    nresults=res.fetchall()\n    print(nresults)\n')


# In[11]:


get_ipython().run_cell_magic('time', '', 'with  engine.connect() as conn:\n    res=conn.execute(text("select AsGeoJSON(centroid) as centroid from geometries limit 1000"))\n    centroids=res.fetchall()\n')


# In[12]:


centroids[0:100]


# In[ ]:



