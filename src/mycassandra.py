#python3 -m pip install cassandra-driver==3.30.1     (Python 3.10 a 3.14, NAO use o 3.15)
#------------------------------------------------------------------
# Credenciais por variavel de ambiente, NUNCA no codigo:
#   Mac/Linux:  export ASTRA_SCB_PATH="/caminho/secure-connect-mercadolivre.zip"
#               export ASTRA_DB_TOKEN="AstraCS:..."
#   Windows:    $env:ASTRA_SCB_PATH="C:\caminho\secure-connect-mercadolivre.zip"
#               $env:ASTRA_DB_TOKEN="AstraCS:..."
# O keyspace "mercadolivre" deve ser criado antes, pelo painel do Astra.
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra import InvalidRequest
from dotenv import load_dotenv

load_dotenv() 

cloud = {"secure_connect_bundle": os.getenv("secure_connect_bundle")}
auth = PlainTextAuthProvider("token", os.getenv("token"))
cluster = Cluster(cloud=cloud, auth_provider=auth)
session = cluster.connect("mercado_livre")
    

def criarTabelas():
    print("\n####CREATE TABLE####")
    # Busca de usuario pelo CPF: o CPF eh a partition key
    session.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            cpf   text PRIMARY KEY,
            nome  text,
            email text
        )
    """)
    # Uma tabela por consulta: "pedidos de um usuario, do mais novo pro mais antigo"
    #   partition key  (cpf)                   -> todos os pedidos do usuario ficam juntos no mesmo no
    #   clustering key (data_pedido, id_pedido) -> ja gravados em ordem, sem ORDER BY na consulta
    session.execute("""
        CREATE TABLE IF NOT EXISTS pedido_por_usuario (
            cpf         text,
            data_pedido timestamp,
            id_pedido   uuid,
            produto     text,
            valor       decimal,
            PRIMARY KEY ((cpf), data_pedido, id_pedido)
        ) WITH CLUSTERING ORDER BY (data_pedido DESC, id_pedido ASC)
    """)
    print("Tabelas criadas")


def insertUsuario(cpf, nome, email):
    #Insert com prepared statement (evita injection, igual ao SQL)
    print("\n####INSERT USUARIO####")
    stmt = session.prepare("INSERT INTO usuario (cpf, nome, email) VALUES (?, ?, ?)")
    session.execute(stmt, (cpf, nome, email))
    print("Inserido", nome)


def insertPedido(cpf, produto, valor):
    print("\n####INSERT PEDIDO####")
    stmt = session.prepare("""
        INSERT INTO pedido_por_usuario (cpf, data_pedido, id_pedido, produto, valor)
        VALUES (?, ?, ?, ?, ?)
    """)
    session.execute(stmt, (cpf, datetime.now(timezone.utc), uuid.uuid4(), produto, valor))
    print("Pedido inserido:", produto)


def findUsuario(cpf):
    print("\n####QUERY USUARIO####")
    stmt = session.prepare("SELECT cpf, nome, email FROM usuario WHERE cpf = ?")
    for row in session.execute(stmt, (cpf,)):
        print(row.cpf, row.nome, row.email)


def findPedidos(cpf):
    #Vem ordenado pela clustering key, do mais novo pro mais antigo
    print("\n####QUERY PEDIDOS####")
    stmt = session.prepare("SELECT data_pedido, produto, valor FROM pedido_por_usuario WHERE cpf = ?")
    for row in session.execute(stmt, (cpf,)):
        print(row.data_pedido, row.produto, row.valor)


def findPorNome(nome):
    #nome NAO eh chave: o Cassandra recusa, pq teria que varrer o cluster inteiro.
    #No Mongo isso funciona; aqui a modelagem nasce da consulta.
    print("\n####QUERY POR NOME (sem chave)####")
    try:
        stmt = session.prepare("SELECT * FROM usuario WHERE nome = ?")
        session.execute(stmt, (nome,))
    except InvalidRequest as e:
        print("Recusado pelo Cassandra:", e)


############# main

criarTabelas()
insertUsuario("111.111.111-11", "Fulano de Tal", "fulano@exemplo.com")
insertPedido("111.111.111-11", "Teclado", Decimal("150.00"))
insertPedido("111.111.111-11", "Mouse", Decimal("80.00"))
findUsuario("111.111.111-11")
findPedidos("111.111.111-11")
findPorNome("Fulano de Tal")

cluster.shutdown()
