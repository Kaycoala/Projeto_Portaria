"""Gera o PDF final do projeto: documentacao/Projeto_Portaria.pdf

Só roda quando os 10 prints reais estiverem em documentacao/prints/ (veja o README dessa pasta)
e quando os dados da capa abaixo estiverem preenchidos. Assim não existe PDF com imagem faltando.

Uso (na raiz do repositório, no PowerShell):
    sistema\\venv\\Scripts\\python.exe -m pip install -r documentacao\\requirements-pdf.txt
    sistema\\venv\\Scripts\\python.exe documentacao\\gerar_pdf.py
"""
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ====================== PREENCHA ANTES DE GERAR ======================
INTEGRANTES = ["PREENCHER: nome do integrante 1", "PREENCHER: nome do integrante 2"]
INSTITUICAO = "PREENCHER: nome da instituição"
CURSO = "Ciência da Computação"
PROFESSOR = "PREENCHER: nome do professor"
# =====================================================================

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PRINTS = RAIZ / "documentacao" / "prints"
SAIDA = RAIZ / "documentacao" / "Projeto_Portaria.pdf"
VERSAO = "1.0.0"
REPOSITORIO = "https://github.com/Kaycoala/Projeto_Portaria"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]

PRINTS = [  # (nome do arquivo sem extensão, título, perfil, legenda)
    ("01_login", "Login", "sem login", "Tela de entrada. Todas as demais telas exigem login (RNF-02)."),
    ("02_dashboard", "Dashboard", "administrador",
     "Painel inicial com os números lidos do banco de dados e as últimas movimentações."),
    ("03_cadastro_pessoas", "Cadastro de pessoas", "porteiro",
     "Lista de moradores, funcionários e prestadores, com busca (RF-01)."),
    ("04_cadastro_veiculos", "Cadastro de veículos", "porteiro",
     "Veículos com placa, modelo, cor e proprietário (RF-02)."),
    ("05_cadastro_visitantes", "Cadastro de visitantes", "porteiro",
     "Visitantes com a situação da autorização: aguardando, autorizado ou negado (RF-05)."),
    ("06_autorizacao_visitantes", "Autorização de visitantes", "aprovador (gerente)",
     "Tela de decisão: o aprovador autoriza (com período) ou nega a entrada (RF-06, UC02)."),
    ("07_entrada_saida", "Registro de entrada e saída", "porteiro",
     "Registro de entradas e saídas de pessoas, visitantes e veículos, com a lista de quem está dentro agora "
     "(RF-03, RF-04, RF-07, UC01)."),
    ("08_historico_acessos", "Histórico de acessos", "porteiro",
     "Consulta com filtros por nome, CPF, placa, data e tipo de acesso (RF-08, UC03)."),
    ("09_ocorrencias", "Ocorrências", "porteiro",
     "Ocorrências com data, horário, descrição e pessoas envolvidas (RF-09)."),
    ("10_relatorios", "Relatórios", "administrador",
     "Relatório de acessos por período, com resumo, entradas e saídas e ocorrências (RF-10)."),
]

REQ_FUNCIONAIS = [
    ("RF-01", "Cadastrar moradores e funcionários (nome, CPF, telefone, e-mail e endereço ou setor).", "Menu Pessoas"),
    ("RF-02", "Cadastrar veículos (placa, modelo, cor e proprietário).", "Menu Veículos"),
    ("RF-03", "Registrar a entrada de moradores, funcionários, visitantes e prestadores, com data e horário.", "Menu Entrada e saída"),
    ("RF-04", "Registrar a saída de pessoas que já possuem entrada registrada.", "Menu Entrada e saída"),
    ("RF-05", "Cadastrar visitantes (nome, CPF, telefone, pessoa visitada e motivo).", "Menu Visitantes"),
    ("RF-06", "Autorizar ou negar a entrada de um visitante, informando a data ou o período permitido.", "Menu Autorizações"),
    ("RF-07", "Registrar a entrada e a saída de veículos, com placa, horário e responsável.", "Menu Entrada e saída"),
    ("RF-08", "Consultar o histórico de acessos com filtros (nome, CPF, placa, data e tipo de acesso).", "Menu Histórico"),
    ("RF-09", "Registrar ocorrências (data e horário, descrição e pessoas envolvidas).", "Menu Ocorrências"),
    ("RF-10", "Gerar relatórios de movimentações por período (acessos, visitantes, veículos e ocorrências).", "Menu Relatórios"),
]
REQ_NAO_FUNCIONAIS = [
    ("RNF-01", "Desempenho: consultas e registros em até 2 segundos.",
     "Consultas com índices no banco, limite de 200 linhas no histórico e relatórios de no máximo 366 dias."),
    ("RNF-02", "Segurança: login e senha antes de acessar os dados.",
     "Todas as telas exigem login; senhas guardadas com hash; formulários protegidos contra envio falso."),
    ("RNF-03", "Disponibilidade durante o horário de operação da portaria.",
     "Sistema leve (Flask e SQLite) que roda em um único computador, sem depender de internet."),
    ("RNF-04", "Permissões: acesso de acordo com o perfil do usuário.",
     "Permissões centralizadas em um arquivo; páginas proibidas respondem com erro 403 e o menu mostra só o permitido."),
    ("RNF-05", "Backup: cópia de segurança pelo menos a cada 24 horas.",
     "Script de backup e tela Backup (administrador); o painel avisa quando o último backup passa de 24 horas."),
]
REGRAS = [
    ("RN-01", "Pessoas com acesso permanente devem estar cadastradas.", "Só pessoas cadastradas e ativas têm a entrada registrada."),
    ("RN-02", "Toda entrada tem registro de data e horário antes da liberação.", "Data e hora gravadas automaticamente pelo sistema."),
    ("RN-03", "Visitantes entram mediante autorização.", "A entrada do visitante só é liberada com autorização válida para o dia."),
    ("RN-04", "Toda saída deve ser registrada.", "Quem está dentro aparece em \"Dentro agora\" até a saída ser registrada."),
    ("RN-05", "Só usuários autorizados alteram ou excluem registros.", "Somente o administrador edita ou exclui acessos, visitantes e ocorrências."),
    ("RN-06", "O CPF é único no cadastro de pessoas.", "Verificado na validação e garantido no banco (UNIQUE)."),
    ("RN-07", "A placa é única no cadastro de veículos.", "Verificado na validação e garantido no banco (UNIQUE)."),
    ("RN-08", "Registros de acesso não são excluídos por usuários comuns.", "Exclusão lógica: o registro continua guardado e visível ao administrador."),
    ("RN-09", "Visitante sem autorização aguarda a liberação.", "Toda solicitação começa aguardando autorização e a portaria não libera a entrada até a decisão."),
    ("RN-10", "Ocorrências têm data, horário e descrição.", "Campos obrigatórios na tela e no banco de dados."),
]
CASOS_DE_USO = [
    ("UC01 - Registrar entrada", "Porteiro",
     "Registrar a entrada de uma pessoa no local.",
     ["O porteiro está autenticado.", "A pessoa deve ser identificada."],
     ["O porteiro acessa a opção de registrar entrada.", "O sistema solicita a identificação da pessoa.",
      "O porteiro informa os dados necessários.", "O sistema verifica o cadastro e a autorização.",
      "O porteiro confirma a entrada.", "O sistema registra a data e o horário.",
      "O sistema confirma que a entrada foi registrada."],
     "Se a pessoa não estiver cadastrada ou não tiver autorização, o sistema informa que é necessário regularizar o "
     "cadastro ou obter autorização antes da entrada.",
     "A entrada fica registrada no histórico de acessos."),
    ("UC02 - Autorizar visitante", "Aprovador (Gerente)",
     "Autorizar ou negar a entrada de um visitante.",
     ["O visitante está identificado.", "O aprovador está autenticado."],
     ["O aprovador acessa a opção de autorização de visitantes.", "O sistema apresenta os dados da solicitação.",
      "O aprovador verifica o visitante, o responsável e o período solicitado.", "O aprovador aprova a solicitação.",
      "O sistema registra a decisão.", "O sistema confirma que o visitante está autorizado."],
     "Se o aprovador negar a solicitação, o sistema registra a decisão e informa que a entrada não está autorizada.",
     "A decisão fica registrada e pode ser consultada."),
    ("UC03 - Consultar histórico de acessos", "Porteiro",
     "Consultar entradas e saídas de pessoas e veículos.",
     ["O usuário está autenticado.", "O usuário tem permissão para consultar o histórico."],
     ["O porteiro acessa o histórico.", "O sistema apresenta os filtros disponíveis.",
      "O porteiro informa os critérios de pesquisa.", "O sistema pesquisa os registros correspondentes.",
      "O sistema apresenta os resultados."],
     "Se nenhum registro for encontrado, o sistema informa que não existem resultados para os filtros utilizados.",
     "O histórico é apresentado sem alterar os registros."),
]
CLASSES = [
    ("Pessoa", "pessoa", "Acrescenta endereço/setor, tipo (morador, funcionário ou prestador) e situação. CPF único."),
    ("Veiculo", "veiculo", "Ligado ao proprietário (1 pessoa para 0..* veículos). Placa única."),
    ("Visitante (especialização de Pessoa)", "visitante", "Tabela própria com nome, CPF e telefone; a pessoa visitada é uma chave estrangeira."),
    ("Acesso", "registro_acesso", "O tipo indica pessoa, visitante ou veículo; guarda o porteiro e a exclusão lógica."),
    ("Ocorrencia", "ocorrencia e ocorrencia_pessoa", "A tabela de ligação guarda as pessoas envolvidas."),
    ("Usuario", "usuario e perfil", "Senha com hash; o perfil virou uma tabela, com as permissões em um arquivo de configuração."),
]


def estilos():
    base = getSampleStyleSheet()
    azul = colors.HexColor("#1f3a5f")
    return {
        "corpo": ParagraphStyle("corpo", parent=base["BodyText"], fontName="Helvetica", fontSize=10.5,
                                leading=15, alignment=TA_JUSTIFY, spaceAfter=6),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=16,
                             textColor=azul, spaceBefore=4, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12,
                             textColor=azul, spaceBefore=8, spaceAfter=4),
        "celula": ParagraphStyle("celula", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=12),
        "celula_b": ParagraphStyle("celula_b", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=12,
                                   textColor=colors.white),
        "legenda": ParagraphStyle("legenda", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=9,
                                  leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#444444"), spaceAfter=10),
        "capa_titulo": ParagraphStyle("capa_titulo", parent=base["Title"], fontName="Helvetica-Bold", fontSize=28,
                                      leading=34, textColor=azul, alignment=TA_CENTER),
        "capa": ParagraphStyle("capa", parent=base["BodyText"], fontName="Helvetica", fontSize=12, leading=18,
                               alignment=TA_CENTER),
        "item": ParagraphStyle("item", parent=base["BodyText"], fontName="Helvetica", fontSize=10.5, leading=14,
                               leftIndent=14, bulletIndent=2, spaceAfter=2),
    }


def p(texto, estilo):
    return Paragraph(escape(texto), estilo)


def tabela(cabecalho, linhas, larguras, e):
    dados = [[Paragraph(escape(c), e["celula_b"]) for c in cabecalho]]
    dados += [[Paragraph(escape(c), e["celula"]) for c in linha] for linha in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6f9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def imagem(caminho, largura_max, altura_max):
    largura, altura = ImageReader(str(caminho)).getSize()
    escala = min(largura_max / largura, altura_max / altura)
    img = Image(str(caminho), width=largura * escala, height=altura * escala)
    img.hAlign = "CENTER"
    return img


def achar_print(nome):
    for extensao in (".png", ".jpg", ".jpeg"):
        caminho = PASTA_PRINTS / f"{nome}{extensao}"
        if caminho.exists():
            return caminho
    return None


def conferir_antes_de_gerar():
    """Devolve a lista de problemas; o PDF só é gerado se ela estiver vazia."""
    problemas = []
    for valor in INTEGRANTES + [INSTITUICAO, PROFESSOR]:
        if "PREENCHER" in valor:
            problemas.append("Preencha os dados da capa no começo de documentacao/gerar_pdf.py "
                             "(integrantes, instituição e professor).")
            break
    for nome, titulo, _, _ in PRINTS:
        if achar_print(nome) is None:
            problemas.append(f"Falta o print '{nome}.png' ({titulo}) em documentacao/prints/.")
    for arquivo in ("Diagrama_Casos_de_Uso_Portaria.jpg", "Diagrama_de_Classes_Portaria.jpg"):
        if not (RAIZ / "diagramas" / arquivo).exists():
            problemas.append(f"Falta o diagrama diagramas/{arquivo}.")
    return problemas


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, f"Sistema de Controle de Portaria - versão {VERSAO}")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


def montar_documento():
    e = estilos()
    hoje = date.today()
    h = []

    # 1. Capa
    h += [Spacer(1, 3 * cm), p(INSTITUICAO, e["capa"]), p(f"Curso de {CURSO}", e["capa"]), Spacer(1, 3 * cm),
          p("Sistema de Controle de Portaria", e["capa_titulo"]), Spacer(1, 0.6 * cm),
          p("Documentação do projeto - Análise e Projeto de Sistemas", e["capa"]), Spacer(1, 3.5 * cm)]
    h += [p(nome, e["capa"]) for nome in INTEGRANTES]
    h += [Spacer(1, 0.8 * cm), p(f"Professor: {PROFESSOR}", e["capa"]), Spacer(1, 2.5 * cm),
          p(f"Versão {VERSAO}", e["capa"]), p(f"{MESES[hoje.month - 1].capitalize()} de {hoje.year}", e["capa"]),
          p(REPOSITORIO, e["capa"]), PageBreak()]

    # 2. Descrição e contexto
    h += [p("1. Descrição e contexto do sistema", e["h1"]),
          p("O Sistema de Controle de Portaria organiza o registro e o acompanhamento da entrada e da saída de pessoas "
            "e veículos em um ambiente com portaria, como um condomínio ou uma empresa. Em muitos locais esse controle "
            "ainda é feito de forma manual, em cadernos ou planilhas, o que dificulta consultar o histórico, saber quem "
            "está dentro do local e comprovar quem autorizou cada visita.", e["corpo"]),
          p("O sistema substitui esses controles por uma aplicação web simples, usada pelo navegador, com banco de dados "
            "real. Ele permite cadastrar moradores, funcionários e veículos, registrar visitantes e suas autorizações, "
            "registrar entradas e saídas, consultar o histórico, registrar ocorrências e gerar relatórios. Cada usuário "
            "acessa apenas o que o seu perfil permite: administrador, porteiro, aprovador (gerente) ou funcionário.", e["corpo"]),
          p("Tecnologias utilizadas: Python com Flask, banco de dados SQLite, páginas HTML com Bootstrap e testes "
            "automatizados com unittest.", e["corpo"])]

    # 3. Objetivo
    h += [p("2. Objetivo", e["h1"]),
          p("Desenvolver um sistema funcional para controlar a entrada e a saída de pessoas e veículos, aplicando os "
            "conceitos de análise, modelagem e desenvolvimento de sistemas.", e["corpo"]), p("Objetivos específicos:", e["h2"])]
    for item in ["Melhorar o controle de acesso de pessoas e veículos.", "Registrar entradas, saídas e ocorrências.",
                 "Organizar os dados de moradores, funcionários e visitantes.", "Registrar as autorizações de visitantes.",
                 "Facilitar a consulta ao histórico de acessos.", "Apoiar a geração de relatórios de movimentação."]:
        h.append(Paragraph(escape(item), e["item"], bulletText="•"))

    # 4. Escopo
    h += [p("3. Escopo", e["h1"]),
          p("Fazem parte do escopo os dez requisitos funcionais (RF-01 a RF-10), os cinco requisitos não funcionais "
            "(RNF-01 a RNF-05) e as dez regras de negócio (RN-01 a RN-10) descritos neste documento, implementados e "
            "cobertos por testes automatizados. O sistema funciona em um computador, com acesso pelo navegador.", e["corpo"]),
          p("Não fazem parte deste trabalho a integração com equipamentos externos (catracas, câmeras ou leitores de "
            "placa), um aplicativo para celular e o envio de mensagens a moradores.", e["corpo"]), PageBreak()]

    # 5-7. Requisitos
    h += [p("4. Requisitos funcionais", e["h1"]),
          tabela(["Código", "Requisito", "Onde fica no sistema"], REQ_FUNCIONAIS, [1.6 * cm, 11.4 * cm, 4 * cm], e),
          Spacer(1, 0.6 * cm), p("5. Requisitos não funcionais", e["h1"]),
          tabela(["Código", "Requisito", "Como foi atendido"], REQ_NAO_FUNCIONAIS, [1.6 * cm, 6.4 * cm, 9 * cm], e),
          PageBreak(), p("6. Regras de negócio", e["h1"]),
          tabela(["Código", "Regra", "Como foi atendida"], REGRAS, [1.6 * cm, 6.4 * cm, 9 * cm], e),
          Spacer(1, 0.6 * cm), p("Perfis de usuário", e["h2"]),
          tabela(["Perfil", "O que pode fazer"], [
              ("Administrador", "Gerencia usuários e tem acesso administrativo a registros, ocorrências, relatórios e backup."),
              ("Porteiro", "Realiza cadastros, registra entradas e saídas, cadastra visitantes e consulta o histórico."),
              ("Aprovador (Gerente)", "Autoriza ou nega as solicitações de entrada de visitantes."),
              ("Funcionário", "Tem seus dados e veículos cadastrados; entra no sistema sem operações."),
              ("Visitante", "Solicita acesso e aguarda a autorização (é um registro, não um usuário com login)."),
          ], [4 * cm, 13 * cm], e), PageBreak()]

    # 8. Casos de uso
    h += [p("7. Diagrama de Casos de Uso", e["h1"]),
          imagem(RAIZ / "diagramas" / "Diagrama_Casos_de_Uso_Portaria.jpg", 17 * cm, 12 * cm),
          p("Figura 1 - Diagrama de Casos de Uso.", e["legenda"]), PageBreak()]

    # 9. Casos de uso textuais
    h.append(p("8. Casos de uso textuais", e["h1"]))
    for titulo, ator, objetivo, pre, fluxo, alternativo, pos in CASOS_DE_USO:
        bloco = [p(titulo, e["h2"]), p(f"Ator principal: {ator}", e["corpo"]), p(f"Objetivo: {objetivo}", e["corpo"]),
                 p("Pré-condições:", e["corpo"])]
        bloco += [Paragraph(escape(x), e["item"], bulletText="•") for x in pre]
        bloco.append(p("Fluxo principal:", e["corpo"]))
        bloco += [Paragraph(escape(x), e["item"], bulletText=f"{i}.") for i, x in enumerate(fluxo, 1)]
        bloco += [p(f"Fluxo alternativo: {alternativo}", e["corpo"]), p(f"Pós-condição: {pos}", e["corpo"]), Spacer(1, 0.3 * cm)]
        h.append(KeepTogether(bloco))
    h.append(PageBreak())

    # 10. Classes
    h += [p("9. Diagrama de Classes", e["h1"]),
          imagem(RAIZ / "diagramas" / "Diagrama_de_Classes_Portaria.jpg", 11 * cm, 16 * cm),
          p("Figura 2 - Diagrama de Classes.", e["legenda"]), PageBreak(),
          p("Correspondência com a implementação", e["h2"]),
          p("Cada classe do diagrama foi implementada em tabelas do banco de dados. O diagrama não foi alterado; "
            "a tabela abaixo mostra como cada classe foi representada.", e["corpo"]),
          tabela(["Classe", "Tabela(s)", "Observações"], CLASSES, [4.4 * cm, 3.6 * cm, 9 * cm], e),
          Spacer(1, 0.3 * cm),
          p("Foi acrescentada a tabela de autorizações (visitante, situação, período, quem decidiu e quando), necessária "
            "para registrar a decisão do aprovador (RF-06 e UC02), que o diagrama de classes não detalha. Os campos de "
            "situação (ativo) permitem desativar cadastros e excluir registros sem apagá-los, preservando o histórico (RN-08).",
            e["corpo"]), PageBreak()]

    # 11. Prints
    h.append(p("10. Telas do sistema em funcionamento", e["h1"]))
    h.append(p("As imagens abaixo são capturas reais do sistema em execução, com dados fictícios de demonstração.", e["corpo"]))
    for i, (nome, titulo, perfil, legenda) in enumerate(PRINTS, 1):
        h.append(KeepTogether([p(f"10.{i} {titulo} (perfil: {perfil})", e["h2"]),
                               imagem(achar_print(nome), 16.5 * cm, 9.6 * cm),
                               p(f"Figura {i + 2} - {legenda}", e["legenda"])]))
    return h


def main():
    problemas = conferir_antes_de_gerar()
    if problemas:
        print("O PDF NÃO foi gerado. Resolva antes de continuar:")
        for problema in problemas:
            print(f"  - {problema}")
        sys.exit(1)
    doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title="Sistema de Controle de Portaria", author=", ".join(INTEGRANTES))
    doc.build(montar_documento(), onLaterPages=rodape)
    print(f"PDF gerado: {SAIDA}")


if __name__ == "__main__":
    main()
