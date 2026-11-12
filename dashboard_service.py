"""Números do painel inicial (dashboard). Tudo vem do banco; nada é fixo na tela.

Só lê os dados. Registros com exclusão lógica (ativo = 0) não entram nas contagens.
"""
from datetime import date, timedelta

from app.services.historico_service import SQL_HISTORICO

ULTIMAS = 5   # quantas movimentações recentes mostrar


def _contar(db, sql, parametros=()):
    return db.execute(sql, parametros).fetchone()[0]


def _hoje(hoje=None):
    """(início do dia, início do dia seguinte), no formato gravado no banco."""
    hoje = hoje or date.today()
    return f"{hoje.isoformat()} 00:00:00", f"{(hoje + timedelta(days=1)).isoformat()} 00:00:00"


def resumo(db, hoje=None):
    dia = _hoje(hoje)

    pessoas_por_tipo = {"morador": 0, "funcionario": 0, "prestador": 0}
    for linha in db.execute("SELECT tipo, COUNT(*) AS n FROM pessoa WHERE ativo = 1 GROUP BY tipo"):
        pessoas_por_tipo[linha["tipo"]] = linha["n"]

    dentro = {"pessoa": 0, "visitante": 0, "veiculo": 0}
    for linha in db.execute("SELECT tipo, COUNT(*) AS n FROM registro_acesso "
                            "WHERE saida_em IS NULL AND ativo = 1 GROUP BY tipo"):
        dentro[linha["tipo"]] = linha["n"]

    return {
        "pessoas": sum(pessoas_por_tipo.values()),
        "pessoas_por_tipo": pessoas_por_tipo,
        "veiculos": _contar(db, "SELECT COUNT(*) FROM veiculo WHERE ativo = 1"),
        # O mesmo visitante pode ter várias visitas; conta cada CPF uma vez.
        "visitantes": _contar(db, "SELECT COUNT(DISTINCT cpf) FROM visitante"),
        "autorizacoes_pendentes": _contar(db, "SELECT COUNT(*) FROM autorizacao WHERE status = 'pendente'"),
        "entradas_hoje": _contar(db, "SELECT COUNT(*) FROM registro_acesso "
                                     "WHERE ativo = 1 AND entrada_em >= ? AND entrada_em < ?", dia),
        "saidas_hoje": _contar(db, "SELECT COUNT(*) FROM registro_acesso "
                                   "WHERE ativo = 1 AND saida_em >= ? AND saida_em < ?", dia),
        "dentro": dentro,
        "dentro_total": sum(dentro.values()),
        "ocorrencias_hoje": _contar(db, "SELECT COUNT(*) FROM ocorrencia "
                                        "WHERE ativo = 1 AND data_hora >= ? AND data_hora < ?", dia),
    }


def ultimas_movimentacoes(db, limite=ULTIMAS):
    """Entradas mais recentes (com a saída, se já houve)."""
    return db.execute(SQL_HISTORICO + "WHERE r.ativo = 1 ORDER BY r.entrada_em DESC, r.id DESC LIMIT ?",
                      (limite,)).fetchall()
