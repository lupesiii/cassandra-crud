from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import InvalidRequest
import os

load_dotenv() 

cloud = {"secure_connect_bundle": os.getenv("secure_connect_bundle")}
auth = PlainTextAuthProvider("token", os.getenv("token"))
cluster = Cluster(cloud=cloud, auth_provider=auth)
session = cluster.connect("mercado_livre")