"""Cópia de segurança do banco de dados (RNF-05: pelo menos a cada 24 horas).

O backup usa o recurso próprio do SQLite, que gera uma cópia consistente mesmo com o
sistema em uso. Cada cópia vira um arquivo `portaria_AAAA-MM-DD_HH-MM-SS.db`; a data
do backup é lida do nome do arquivo (copiar o arquivo para outro lugar não a muda).
"""
import os
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.services.erros import ErroNegocio

MANTER_PADRAO = 30                 # quantos backups guardar (os mais antigos são apagados)
INTERVALO = timedelta(hours=24)    # RNF-05
FORMATO_NOME = "portaria_%Y-%m-%d_%H-%M-%S"
PADRAO_NOME = re.compile(r"^portaria_(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})(?:_(\d+))?\.db$")


def tamanho_legivel(bytes_):
    if bytes_ < 1024:
        return f"{bytes_} bytes"
    if bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.0f} KB"
    return f"{bytes_ / (1024 * 1024):.1f} MB".replace(".", ",")


def _ler_nome(nome):
    """Devolve (momento, número) a partir do nome do arquivo, ou None se não for um backup."""
    achado = PADRAO_NOME.match(nome)
    if achado is None:
        return None
    try:
        momento = datetime.strptime(f"{achado[1]} {achado[2]}:{achado[3]}:{achado[4]}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return momento, int(achado[5] or 1)


def listar_backups(pasta):
    """Backups da pasta, do mais recente para o mais antigo. Outros arquivos são ignorados."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        return []
    encontrados = []
    for arquivo in pasta.iterdir():
        lido = _ler_nome(arquivo.name)
        if lido is None or not arquivo.is_file():
            continue
        momento, numero = lido
        tamanho = arquivo.stat().st_size
        encontrados.append({"nome": arquivo.name, "caminho": arquivo, "momento": momento,
                            "criado_em": momento.strftime("%Y-%m-%d %H:%M:%S"),
                            "tamanho": tamanho, "tamanho_texto": tamanho_legivel(tamanho),
                            "_ordem": (momento, numero)})
    encontrados.sort(key=lambda item: item["_ordem"], reverse=True)
    return encontrados


def situacao(pasta, agora=None):
    """Diz se existe backup feito nas últimas 24 horas."""
    agora = agora or datetime.now()
    lista = listar_backups(pasta)
    ultimo = lista[0] if lista else None
    em_dia = ultimo is not None and agora - ultimo["momento"] < INTERVALO
    return {"ultimo": ultimo["criado_em"] if ultimo else None, "em_dia": em_dia, "total": len(lista)}


def _nome_livre(pasta, agora):
    base = agora.strftime(FORMATO_NOME)
    nome, numero = f"{base}.db", 1
    while (pasta / nome).exists():
        numero += 1
        nome = f"{base}_{numero}.db"
    return nome


def fazer_backup(caminho_banco, pasta, manter=MANTER_PADRAO, agora=None):
    """Cria um backup do banco e apaga os mais antigos além do limite `manter`."""
    caminho_banco, pasta = Path(caminho_banco), Path(pasta)
    if manter < 1:
        raise ErroNegocio("É preciso manter pelo menos 1 backup.")
    if not caminho_banco.is_file():
        raise ErroNegocio("O banco de dados não foi encontrado; não há o que copiar.")

    agora = agora or datetime.now()
    try:
        pasta.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise ErroNegocio("Não foi possível criar a pasta de backups.")
    nome = _nome_livre(pasta, agora)
    destino = pasta / nome
    temporario = pasta / (nome + ".tmp")   # só vira backup depois de conferido

    origem = copia = None
    try:
        origem = sqlite3.connect(caminho_banco)
        copia = sqlite3.connect(temporario)
        origem.backup(copia)
        resultado = copia.execute("PRAGMA integrity_check").fetchone()[0]
        if resultado != "ok":
            raise ErroNegocio("A cópia gerada não passou na verificação e foi descartada.")
        copia.close()
        copia = None
        os.replace(temporario, destino)
    except ErroNegocio:
        raise
    except (sqlite3.Error, OSError):
        raise ErroNegocio("Não foi possível criar o backup. Confira se o banco e a pasta de backups estão acessíveis.")
    finally:
        for conexao in (origem, copia):
            if conexao is not None:
                conexao.close()
        if temporario.exists():
            try:
                temporario.unlink()
            except OSError:
                pass

    removidos = 0
    for antigo in listar_backups(pasta)[manter:]:
        try:
            antigo["caminho"].unlink()
            removidos += 1
        except OSError:
            pass
    return {"nome": nome, "caminho": destino, "tamanho_texto": tamanho_legivel(destino.stat().st_size),
            "removidos": removidos}
