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

def createTables():
    session.execute("""
        CREATE TABLE IF NOT EXISTS comprador (
            email       TEXT PRIMARY KEY,
            nome        TEXT,
            favoritos   LIST<TEXT>
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS vendedor (
            email   TEXT PRIMARY KEY,
            nome    TEXT
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id              UUID PRIMARY KEY,
            nome            TEXT,
            preco           DECIMAL,
            vendedor_email  TEXT
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id               UUID PRIMARY KEY,
            comprador_email  TEXT,
            produto_id       UUID,
            pagamento        TEXT
        )
    """)

    print("Tabelas criadas com sucesso.")