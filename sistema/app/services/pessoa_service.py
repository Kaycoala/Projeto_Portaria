"""Regras de negócio do cadastro de pessoas (RF-01, RN-06)."""
import re
import sqlite3

from app.services.erros import ErroNegocio

TIPOS = {"morador": "Morador", "funcionario": "Funcionário", "prestador": "Prestador"}

PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def nome_tipo(tipo):
    return TIPOS.get(tipo, tipo)


def somente_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def formatar_cpf(cpf):
    """123.456.789-09 (só para exibir; no banco o CPF fica só com números)."""
    digitos = somente_digitos(cpf)
    if len(digitos) != 11:
        return cpf or ""          # incompleto: devolve como foi digitado
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def listar_pessoas(db, busca="", incluir_inativos=True):
    """Lista pessoas. A busca procura no nome ou no CPF (aceita CPF com pontos e traço)."""
    sql = "SELECT * FROM pessoa WHERE 1 = 1"
    parametros = []
    if not incluir_inativos:
        sql += " AND ativo = 1"
    busca = (busca or "").strip()
    if busca:
        digitos = somente_digitos(busca)
        condicao = "nome LIKE ?"
        parametros.append(f"%{busca}%")
        if digitos:
            condicao += " OR cpf LIKE ?"
            parametros.append(f"%{digitos}%")
        sql += f" AND ({condicao})"
    sql += " ORDER BY nome COLLATE NOCASE"
    return db.execute(sql, parametros).fetchall()


def buscar_pessoa(db, pessoa_id):
    return db.execute("SELECT * FROM pessoa WHERE id = ?", (pessoa_id,)).fetchone()


def _validar(db, nome, cpf, telefone, email, endereco_setor, tipo, pessoa_id=None):
    """Confere os dados e devolve um dicionário já limpo."""
    nome = " ".join((nome or "").split())
    if len(nome) < 3:
        raise ErroNegocio("Informe o nome completo (mínimo de 3 letras).")

    cpf = somente_digitos(cpf)
    if len(cpf) != 11:
        raise ErroNegocio("O CPF deve ter 11 números.")

    telefone = somente_digitos(telefone)
    if telefone and not 10 <= len(telefone) <= 11:
        raise ErroNegocio("O telefone deve ter DDD + número (10 ou 11 números).")

    email = (email or "").strip().lower()
    if email and not PADRAO_EMAIL.match(email):
        raise ErroNegocio("O e-mail informado não é válido.")

    if tipo not in TIPOS:
        raise ErroNegocio("Escolha o tipo da pessoa (morador, funcionário ou prestador).")

    existente = db.execute("SELECT id FROM pessoa WHERE cpf = ?", (cpf,)).fetchone()
    if existente is not None and existente["id"] != pessoa_id:
        raise ErroNegocio("Já existe uma pessoa com este CPF.")  # RN-06

    return {"nome": nome, "cpf": cpf, "telefone": telefone or None, "email": email or None,
            "endereco_setor": (endereco_setor or "").strip() or None, "tipo": tipo}


def criar_pessoa(db, nome, cpf, telefone, email, endereco_setor, tipo):
    d = _validar(db, nome, cpf, telefone, email, endereco_setor, tipo)
    try:
        cursor = db.execute(
            "INSERT INTO pessoa (nome, cpf, telefone, email, endereco_setor, tipo) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (d["nome"], d["cpf"], d["telefone"], d["email"], d["endereco_setor"], d["tipo"]))
        db.commit()
    except sqlite3.IntegrityError:    # garantia extra: o banco também não aceita CPF repetido
        raise ErroNegocio("Já existe uma pessoa com este CPF.")
    return cursor.lastrowid


def atualizar_pessoa(db, pessoa_id, nome, cpf, telefone, email, endereco_setor, tipo):
    if buscar_pessoa(db, pessoa_id) is None:
        raise ErroNegocio("Pessoa não encontrada.")
    d = _validar(db, nome, cpf, telefone, email, endereco_setor, tipo, pessoa_id)
    try:
        db.execute(
            "UPDATE pessoa SET nome = ?, cpf = ?, telefone = ?, email = ?, "
            "endereco_setor = ?, tipo = ? WHERE id = ?",
            (d["nome"], d["cpf"], d["telefone"], d["email"], d["endereco_setor"], d["tipo"],
             pessoa_id))
        db.commit()
    except sqlite3.IntegrityError:
        raise ErroNegocio("Já existe uma pessoa com este CPF.")


def alternar_ativo(db, pessoa_id):
    """Ativa ou desativa a pessoa (não apaga, pois ela pode ter histórico). Devolve True se ficou ativa."""
    atual = buscar_pessoa(db, pessoa_id)
    if atual is None:
        raise ErroNegocio("Pessoa não encontrada.")
    novo = 0 if atual["ativo"] else 1
    db.execute("UPDATE pessoa SET ativo = ? WHERE id = ?", (novo, pessoa_id))
    db.commit()
    return bool(novo)
