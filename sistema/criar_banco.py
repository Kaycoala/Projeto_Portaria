"""Cria o banco de dados do sistema.

Uso:
    python criar_banco.py             cria o banco (não apaga dados existentes)
    python criar_banco.py --recriar   APAGA o banco e cria de novo
"""
import sys
from pathlib import Path

from app.db import criar_banco

CAMINHO = Path(__file__).resolve().parent / "instance" / "portaria.db"

if __name__ == "__main__":
    recriar = "--recriar" in sys.argv
    criar_banco(CAMINHO, recriar=recriar)
    print(f"Banco {'recriado' if recriar else 'pronto'} em: {CAMINHO}")
