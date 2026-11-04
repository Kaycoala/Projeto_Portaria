"""Cria o primeiro usuário administrador.

Uso (o script pergunta o login e a senha):
    python criar_admin.py

Ou direto:
    python criar_admin.py --login admin --senha minhasenha
"""
import argparse
import getpass
import sys
from pathlib import Path

from app.db import conectar, criar_banco
from app.services.erros import ErroNegocio
from app.services.usuario_service import criar_usuario, perfil_id_por_nome

CAMINHO = Path(__file__).resolve().parent / "instance" / "portaria.db"


def main():
    parser = argparse.ArgumentParser(description="Cria um usuário administrador.")
    parser.add_argument("--login")
    parser.add_argument("--senha")
    args = parser.parse_args()

    login = args.login or input("Login do administrador: ")
    senha = args.senha
    if senha is None:
        senha = getpass.getpass("Senha (mínimo 6 caracteres): ")
        if senha != getpass.getpass("Repita a senha: "):
            print("As senhas não conferem.")
            sys.exit(1)

    criar_banco(CAMINHO)  # garante que o banco existe (não apaga dados)
    db = conectar(CAMINHO)
    try:
        criar_usuario(db, login, senha, perfil_id_por_nome(db, "administrador"))
        print(f"Administrador '{login.strip().lower()}' criado com sucesso.")
    except ErroNegocio as erro:
        print(f"Erro: {erro}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
