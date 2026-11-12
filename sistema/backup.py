r"""Cria uma cópia de segurança do banco de dados (RNF-05).

Uso (dentro da pasta sistema):
    venv\Scripts\python.exe backup.py                 cria um backup em backups/
    venv\Scripts\python.exe backup.py --manter 60     guarda os 60 mais recentes (padrão: 30)

Para fazer todo dia automaticamente, veja a seção "Backup" do README.
"""
import argparse
import sys
from pathlib import Path

from app.services import backup_service
from app.services.erros import ErroNegocio

BASE = Path(__file__).resolve().parent


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Cria um backup do banco de dados da portaria.")
    parser.add_argument("--banco", default=str(BASE / "instance" / "portaria.db"), help="arquivo do banco")
    parser.add_argument("--pasta", default=str(BASE / "backups"), help="pasta onde os backups ficam")
    parser.add_argument("--manter", type=int, default=backup_service.MANTER_PADRAO,
                        help="quantos backups guardar")
    opcoes = parser.parse_args(argumentos)
    try:
        resultado = backup_service.fazer_backup(opcoes.banco, opcoes.pasta, opcoes.manter)
    except ErroNegocio as erro:
        print(f"Erro: {erro}")
        return 1
    print(f"Backup criado: {resultado['caminho']} ({resultado['tamanho_texto']})")
    if resultado["removidos"]:
        print(f"Backups antigos apagados: {resultado['removidos']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
