"""Quem pode fazer o quê.

Cada permissão lista os perfis que podem usá-la. Para mudar uma regra,
basta editar este arquivo.
"""

ADM = "administrador"
APROVADOR = "aprovador"
PORTEIRO = "porteiro"
FUNCIONARIO = "funcionario"

PERMISSOES = {
    "gerenciar_usuarios":   {ADM},
    "gerenciar_cadastros":  {ADM, PORTEIRO},             # pessoas e veículos
    "cadastrar_visitantes": {ADM, PORTEIRO},
    "registrar_acesso":     {ADM, PORTEIRO},             # entradas e saídas
    "autorizar_visitantes": {ADM, APROVADOR},
    "consultar_historico":  {ADM, PORTEIRO, APROVADOR},
    "registrar_ocorrencia": {ADM, PORTEIRO},
    "administrar_registros": {ADM},                      # alterar/excluir acessos, visitantes e ocorrências (RN-05, RN-08)
    "ver_relatorios":       {ADM},
}

NOMES_PERFIL = {
    ADM: "Administrador",
    APROVADOR: "Aprovador (Gerente)",
    PORTEIRO: "Porteiro",
    FUNCIONARIO: "Funcionário",
}


def tem_permissao(perfil, permissao):
    return perfil in PERMISSOES[permissao]


def nome_perfil(perfil):
    return NOMES_PERFIL.get(perfil, perfil)
