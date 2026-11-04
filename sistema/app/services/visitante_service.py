"""Regras de negócio do cadastro de visitantes (RF-05).

Cada visitante nasce junto com uma solicitação de autorização "pendente" (RN-09).
"""
from app.services.erros import ErroNegocio
from app.services.pessoa_service import somente_digitos

SQL_VISITANTES = (
    "SELECT v.id, v.nome, v.cpf, v.telefone, v.motivo, v.criado_em, v.pessoa_visitada_id, "
    "       p.nome AS visitado_nome, "
    "       a.id AS autorizacao_id, a.status, a.data_inicio, a.data_fim, "
    "       a.observacao, a.decidido_em "
    "FROM visitante v JOIN pessoa p ON p.id = v.pessoa_visitada_id "
    "LEFT JOIN autorizacao a ON a.id = "
    "     (SELECT MAX(id) FROM autorizacao WHERE visitante_id = v.id) "
)


def listar_visitantes(db, busca=""):
    """Lista visitantes (mais recentes primeiro) com a situação da última autorização."""
    sql = SQL_VISITANTES + "WHERE 1 = 1"
    parametros = []
    busca = (busca or "").strip()
    if busca:
        condicao = "v.nome LIKE ?"
        parametros.append(f"%{busca}%")
        digitos = somente_digitos(busca)
        if digitos:
            condicao += " OR v.cpf LIKE ?"
            parametros.append(f"%{digitos}%")
        sql += f" AND ({condicao})"
    sql += " ORDER BY v.id DESC"
    return db.execute(sql, parametros).fetchall()


def buscar_visitante(db, visitante_id):
    return db.execute(SQL_VISITANTES + "WHERE v.id = ?", (visitante_id,)).fetchone()


def listar_pessoas_visitaveis(db, incluir_id=None):
    """Pessoas ativas que podem ser visitadas (mais a atual, se ela estiver inativa)."""
    return db.execute(
        "SELECT id, nome FROM pessoa WHERE ativo = 1 OR id = ? ORDER BY nome COLLATE NOCASE",
        (incluir_id,)).fetchall()


def _validar(db, nome, cpf, telefone, pessoa_visitada_id, motivo, visitada_atual_id=None):
    """Confere os dados e devolve um dicionário já limpo."""
    nome = " ".join((nome or "").split())
    if len(nome) < 3:
        raise ErroNegocio("Informe o nome completo do visitante (mínimo de 3 letras).")

    cpf = somente_digitos(cpf)
    if len(cpf) != 11:
        raise ErroNegocio("O CPF deve ter 11 números.")

    telefone = somente_digitos(telefone)
    if telefone and not 10 <= len(telefone) <= 11:
        raise ErroNegocio("O telefone deve ter DDD + número (10 ou 11 números).")

    try:
        pessoa_visitada_id = int(pessoa_visitada_id)
    except (TypeError, ValueError):
        raise ErroNegocio("Escolha a pessoa que será visitada.")
    pessoa = db.execute("SELECT ativo FROM pessoa WHERE id = ?", (pessoa_visitada_id,)).fetchone()
    if pessoa is None:
        raise ErroNegocio("Pessoa visitada não encontrada.")
    if not pessoa["ativo"] and pessoa_visitada_id != visitada_atual_id:
        raise ErroNegocio("A pessoa visitada está inativa.")

    motivo = " ".join((motivo or "").split())
    if not motivo:
        raise ErroNegocio("Informe o motivo da visita.")

    return {"nome": nome, "cpf": cpf, "telefone": telefone or None,
            "pessoa_visitada_id": pessoa_visitada_id, "motivo": motivo}


def criar_visitante(db, nome, cpf, telefone, pessoa_visitada_id, motivo):
    """Cadastra o visitante e já abre a solicitação de autorização (pendente).

    Devolve (visitante_id, autorizacao_id). Os dois são gravados juntos ou nenhum.
    """
    d = _validar(db, nome, cpf, telefone, pessoa_visitada_id, motivo)
    try:
        cursor = db.execute(
            "INSERT INTO visitante (nome, cpf, telefone, pessoa_visitada_id, motivo) "
            "VALUES (?, ?, ?, ?, ?)",
            (d["nome"], d["cpf"], d["telefone"], d["pessoa_visitada_id"], d["motivo"]))
        visitante_id = cursor.lastrowid
        autorizacao_id = db.execute(
            "INSERT INTO autorizacao (visitante_id) VALUES (?)", (visitante_id,)).lastrowid
        db.commit()
    except Exception:
        db.rollback()
        raise
    return visitante_id, autorizacao_id


def atualizar_visitante(db, visitante_id, nome, cpf, telefone, pessoa_visitada_id, motivo):
    atual = buscar_visitante(db, visitante_id)
    if atual is None:
        raise ErroNegocio("Visitante não encontrado.")
    d = _validar(db, nome, cpf, telefone, pessoa_visitada_id, motivo, atual["pessoa_visitada_id"])
    db.execute(
        "UPDATE visitante SET nome = ?, cpf = ?, telefone = ?, pessoa_visitada_id = ?, motivo = ? "
        "WHERE id = ?",
        (d["nome"], d["cpf"], d["telefone"], d["pessoa_visitada_id"], d["motivo"], visitante_id))
    db.commit()
