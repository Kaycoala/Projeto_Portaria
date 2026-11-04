"""Acesso ao banco de dados SQLite."""
import sqlite3
from pathlib import Path

from flask import current_app, g

PASTA_BANCO = Path(__file__).resolve().parent.parent / "banco"


def conectar(caminho):
    """Abre uma conexão com o banco (com chaves estrangeiras ligadas)."""
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_banco(caminho, recriar=False):
    """Cria as tabelas e os dados iniciais.

    Se recriar=True, apaga o arquivo do banco antes (perde todos os dados).
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if recriar and caminho.exists():
        caminho.unlink()

    conexao = conectar(caminho)
    try:
        conexao.executescript((PASTA_BANCO / "schema.sql").read_text(encoding="utf-8"))
        conexao.executescript((PASTA_BANCO / "dados_iniciais.sql").read_text(encoding="utf-8"))
        conexao.commit()
    finally:
        conexao.close()


def get_db():
    """Devolve a conexão da requisição atual."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def fechar_db(erro=None):
    conexao = g.pop("db", None)
    if conexao is not None:
        conexao.close()


def init_app(app):
    app.teardown_appcontext(fechar_db)
