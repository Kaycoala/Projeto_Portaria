"""Relatório de acessos de um período (RF-10).

Reúne entradas, saídas, visitantes, veículos e ocorrências. Só lê os dados.
Registros excluídos (exclusão lógica) não entram no relatório.
"""
import csv
import io
from datetime import date, timedelta

from app.services.erros import ErroNegocio
from app.services.historico_service import SQL_HISTORICO, TIPOS, intervalo_de_datas
from app.services.ocorrencia_service import listar_ocorrencias

DIAS_MAXIMOS = 366   # período máximo de um relatório (mantém a consulta rápida, RNF-01)


def periodo_padrao(hoje=None):
    """Do primeiro dia do mês até hoje, no formato AAAA-MM-DD."""
    hoje = hoje or date.today()
    return hoje.replace(day=1).isoformat(), hoje.isoformat()


def _validar_periodo(data_de, data_ate):
    data_de = (data_de or "").strip()
    data_ate = (data_ate or "").strip()
    if not data_de or not data_ate:
        raise ErroNegocio("Informe a data inicial e a data final do relatório.")
    inicio, fim = intervalo_de_datas(data_de, data_ate)    # valida formato e ordem
    de, ate = date.fromisoformat(data_de), date.fromisoformat(data_ate)
    dias = (ate - de).days + 1
    if dias > DIAS_MAXIMOS:
        raise ErroNegocio(f"O período do relatório pode ter no máximo {DIAS_MAXIMOS} dias.")
    return de.isoformat(), ate.isoformat(), inicio, fim, dias


def _contar(db, sql, parametros):
    return db.execute(sql, parametros).fetchone()[0]


def gerar_relatorio(db, data_de, data_ate):
    """Monta o relatório do período (datas inclusivas). Levanta ErroNegocio se o período for inválido."""
    data_de, data_ate, inicio, fim, dias = _validar_periodo(data_de, data_ate)
    periodo = (inicio, fim)

    acessos = db.execute(
        SQL_HISTORICO + "WHERE r.ativo = 1 AND r.entrada_em >= ? AND r.entrada_em < ? "
                        "ORDER BY r.entrada_em, r.id", periodo).fetchall()

    entradas_por_tipo = {tipo: 0 for tipo in TIPOS}
    for registro in acessos:
        entradas_por_tipo[registro["tipo"]] += 1

    saidas = _contar(db, "SELECT COUNT(*) FROM registro_acesso "
                         "WHERE ativo = 1 AND saida_em >= ? AND saida_em < ?", periodo)
    sem_saida = sum(1 for registro in acessos if registro["saida_em"] is None)
    visitantes_distintos = _contar(
        db, "SELECT COUNT(DISTINCT v.cpf) FROM registro_acesso r JOIN visitante v ON v.id = r.visitante_id "
            "WHERE r.ativo = 1 AND r.entrada_em >= ? AND r.entrada_em < ?", periodo)
    veiculos_distintos = _contar(
        db, "SELECT COUNT(DISTINCT veiculo_id) FROM registro_acesso "
            "WHERE ativo = 1 AND tipo = 'veiculo' AND entrada_em >= ? AND entrada_em < ?", periodo)

    autorizacoes = {"pendente": 0, "aprovada": 0, "negada": 0}
    for linha in db.execute("SELECT status, COUNT(*) AS n FROM autorizacao "
                            "WHERE solicitado_em >= ? AND solicitado_em < ? GROUP BY status", periodo):
        autorizacoes[linha["status"]] = linha["n"]

    ocorrencias = listar_ocorrencias(db, data_de, data_ate)

    return {
        "data_de": data_de,
        "data_ate": data_ate,
        "dias": dias,
        "resumo": {
            "entradas": len(acessos),
            "entradas_por_tipo": entradas_por_tipo,
            "saidas": saidas,
            "sem_saida": sem_saida,
            "visitantes_distintos": visitantes_distintos,
            "veiculos_distintos": veiculos_distintos,
            "autorizacoes": autorizacoes,
            "ocorrencias": len(ocorrencias),
        },
        "acessos": acessos,
        "ocorrencias": ocorrencias,
    }


# ---------- exportação ----------

def _quem(registro):
    if registro["tipo"] == "pessoa":
        return registro["pessoa_nome"], registro["pessoa_cpf"]
    if registro["tipo"] == "visitante":
        return f"{registro['visitante_nome']} (visita {registro['visitado_nome']})", registro["visitante_cpf"]
    return f"{registro['placa']} - {registro['modelo']} ({registro['proprietario_nome']})", \
        registro["proprietario_cpf"]


def _seguro(valor):
    """Evita que um texto digitado vire fórmula ao abrir o CSV no Excel (ex.: "=SOMA(...)")."""
    texto = "" if valor is None else str(valor)
    return "'" + texto if texto[:1] in ("=", "+", "-", "@") else texto


def gerar_csv(relatorio):
    """Texto CSV (separado por ponto e vírgula, abre direto no Excel em português)."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(["Relatório de acessos", relatorio["data_de"], relatorio["data_ate"]])
    escritor.writerow([])
    escritor.writerow(["Tipo", "Quem", "CPF", "Entrada", "Saída", "Porteiro", "Observação"])
    for registro in relatorio["acessos"]:
        nome, cpf = _quem(registro)
        escritor.writerow([TIPOS[registro["tipo"]], _seguro(nome), cpf, registro["entrada_em"],
                           registro["saida_em"] or "", registro["porteiro_login"],
                           _seguro(registro["observacao"])])
    escritor.writerow([])
    escritor.writerow(["Ocorrências"])
    escritor.writerow(["Data e hora", "Descrição", "Pessoas envolvidas", "Registrada por"])
    for ocorrencia in relatorio["ocorrencias"]:
        escritor.writerow([ocorrencia["data_hora"], _seguro(ocorrencia["descricao"]),
                           _seguro(ocorrencia["envolvidos"]), ocorrencia["registrador"]])
    return saida.getvalue()


def nome_arquivo_csv(relatorio):
    return f"relatorio_acessos_{relatorio['data_de']}_a_{relatorio['data_ate']}.csv"


def ultimos_dias(dias, hoje=None):
    """Atalho para os botões de período: (data_de, data_ate) dos últimos `dias` dias."""
    hoje = hoje or date.today()
    return (hoje - timedelta(days=dias - 1)).isoformat(), hoje.isoformat()
