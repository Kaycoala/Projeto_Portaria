"""Regras de negócio das autorizações de visitantes (RF-06, RN-03, RN-09, UC02)."""
from datetime import date

from app.services.erros import ErroNegocio

STATUS = {"pendente": "Pendente", "aprovada": "Autorizada", "negada": "Negada"}

SQL_AUTORIZACOES = (
    "SELECT a.id, a.visitante_id, a.status, a.data_inicio, a.data_fim, a.observacao, "
    "       a.solicitado_em, a.decidido_em, a.aprovador_id, u.login AS aprovador_login, "
    "       v.nome AS visitante_nome, v.cpf AS visitante_cpf, v.telefone AS visitante_telefone, "
    "       v.motivo, p.nome AS visitado_nome "
    "FROM autorizacao a "
    "JOIN visitante v ON v.id = a.visitante_id "
    "JOIN pessoa p ON p.id = v.pessoa_visitada_id "
    "LEFT JOIN usuario u ON u.id = a.aprovador_id "
)


def nome_status(status):
    return STATUS.get(status, status)


def formatar_data(texto):
    """'2026-11-04' -> '04/11/2026' e '2026-11-04 20:30:00' -> '04/11/2026 20:30' (só para exibir)."""
    if not texto:
        return "—"
    dia, _, hora = texto.partition(" ")
    try:
        saida = date.fromisoformat(dia).strftime("%d/%m/%Y")
    except ValueError:
        return texto
    return f"{saida} {hora[:5]}" if hora else saida


def listar_autorizacoes(db, status="pendente"):
    """Lista autorizações. status: pendente, aprovada, negada ou todas.

    Pendentes: as mais antigas primeiro (ordem de chegada). Demais: as mais recentes primeiro.
    """
    if status in STATUS:
        ordem = "a.id" if status == "pendente" else "a.id DESC"
        return db.execute(SQL_AUTORIZACOES + f"WHERE a.status = ? ORDER BY {ordem}",
                          (status,)).fetchall()
    return db.execute(SQL_AUTORIZACOES + "ORDER BY a.id DESC").fetchall()


def contar_por_status(db):
    """Devolve {'pendente': n, 'aprovada': n, 'negada': n}."""
    contagem = {s: 0 for s in STATUS}
    for linha in db.execute("SELECT status, COUNT(*) AS n FROM autorizacao GROUP BY status"):
        contagem[linha["status"]] = linha["n"]
    return contagem


def buscar_autorizacao(db, autorizacao_id):
    return db.execute(SQL_AUTORIZACOES + "WHERE a.id = ?", (autorizacao_id,)).fetchone()


def solicitar_nova(db, visitante_id):
    """Abre uma nova solicitação para um visitante que já existe (ex.: voltou outro dia)."""
    if db.execute("SELECT 1 FROM visitante WHERE id = ?", (visitante_id,)).fetchone() is None:
        raise ErroNegocio("Visitante não encontrado.")
    if db.execute("SELECT 1 FROM autorizacao WHERE visitante_id = ? AND status = 'pendente'",
                  (visitante_id,)).fetchone() is not None:
        raise ErroNegocio("Este visitante já tem uma solicitação aguardando decisão.")
    cursor = db.execute("INSERT INTO autorizacao (visitante_id) VALUES (?)", (visitante_id,))
    db.commit()
    return cursor.lastrowid


def _data(texto, nome_campo):
    try:
        return date.fromisoformat((texto or "").strip())
    except ValueError:
        raise ErroNegocio(f"Informe {nome_campo} (formato válido de data).")


def _pendente_ou_erro(db, autorizacao_id):
    autorizacao = buscar_autorizacao(db, autorizacao_id)
    if autorizacao is None:
        raise ErroNegocio("Autorização não encontrada.")
    if autorizacao["status"] != "pendente":
        raise ErroNegocio("Esta solicitação já foi decidida e não pode ser alterada.")
    return autorizacao


def _registrar_decisao(db, autorizacao_id, status, aprovador_id, data_inicio, data_fim, observacao):
    # "AND status = 'pendente'" evita que dois aprovadores decidam a mesma solicitação.
    cursor = db.execute(
        "UPDATE autorizacao SET status = ?, data_inicio = ?, data_fim = ?, aprovador_id = ?, "
        "decidido_em = datetime('now', 'localtime'), observacao = ? "
        "WHERE id = ? AND status = 'pendente'",
        (status, data_inicio, data_fim, aprovador_id, observacao or None, autorizacao_id))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio("Esta solicitação já foi decidida e não pode ser alterada.")
    db.commit()


def aprovar(db, autorizacao_id, aprovador_id, data_inicio, data_fim, observacao=""):
    """Autoriza a entrada no período informado (se data_fim ficar vazia, vale só no dia inicial)."""
    _pendente_ou_erro(db, autorizacao_id)
    inicio = _data(data_inicio, "a data de início")
    fim = _data(data_fim, "a data final") if (data_fim or "").strip() else inicio
    if fim < inicio:
        raise ErroNegocio("A data final não pode ser anterior à data de início.")
    if fim < date.today():
        raise ErroNegocio("O período autorizado já terminou. Informe uma data de hoje em diante.")
    _registrar_decisao(db, autorizacao_id, "aprovada", aprovador_id,
                       inicio.isoformat(), fim.isoformat(), (observacao or "").strip())


def negar(db, autorizacao_id, aprovador_id, observacao=""):
    """Nega a entrada. A decisão fica registrada com quem negou e quando."""
    _pendente_ou_erro(db, autorizacao_id)
    _registrar_decisao(db, autorizacao_id, "negada", aprovador_id, None, None,
                       (observacao or "").strip())
