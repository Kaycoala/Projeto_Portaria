"""Testes do histórico de acessos e das ocorrências (V0.7.0).
Execute com: python -m unittest discover tests -v
"""
import unittest
from datetime import datetime, timedelta
from unittest import mock

from app.db import conectar
from app.services import acesso_service, historico_service, ocorrencia_service, pessoa_service
from app.services.erros import ErroNegocio
from tests.test_acessos import BaseAcessos

FUTURO = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
ONTEM_HORA = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")


class BaseHistorico(BaseAcessos):
    """Cria um morador com veículo, um segundo morador e um visitante autorizado."""

    def setUp(self):
        super().setUp()
        self.joao = self.criar_pessoa(nome="João Pereira", cpf="390.533.447-05")
        self.veiculo = self.criar_veiculo(self.morador, placa="ABC-1234", modelo="Gol")
        self.visitante = self.visitante_autorizado()

    def entrar_veiculo(self, veiculo_id=None):
        return self.executar(acesso_service.registrar_entrada_veiculo,
                             veiculo_id or self.veiculo, self.porteiro, "")

    def entrar_visitante(self):
        return self.executar(acesso_service.registrar_entrada_visitante,
                             self.visitante, self.porteiro, "")

    def historico(self, **filtros):
        return self.executar(lambda db: historico_service.listar_historico(db, **filtros))[0]

    def nomes(self, **filtros):
        return [r["tipo"] for r in self.historico(**filtros)]

    def mudar_entrada(self, registro_id, quando):
        db = conectar(self.caminho)
        db.execute("UPDATE registro_acesso SET entrada_em=? WHERE id=?", (quando, registro_id))
        db.commit()
        db.close()

    def ocorrencias(self, **filtros):
        return self.executar(lambda db: ocorrencia_service.listar_ocorrencias(db, **filtros))

    def criar_ocorrencia(self, descricao="Barulho excessivo no bloco A", data_hora="", pessoas=()):
        return self.executar(ocorrencia_service.criar_ocorrencia, data_hora, descricao,
                             [str(p) for p in pessoas], self.porteiro)


class TesteHistoricoConsulta(BaseHistorico):
    def test_historico_vazio(self):
        self.assertEqual(self.historico(), [])

    def test_mostra_os_tres_tipos_do_mais_recente_para_o_mais_antigo(self):
        a = self.entrar_pessoa()
        b = self.entrar_visitante()
        c = self.entrar_veiculo()
        self.mudar_entrada(a, "2026-01-01 08:00:00")
        self.mudar_entrada(b, "2026-01-02 08:00:00")
        self.mudar_entrada(c, "2026-01-03 08:00:00")
        self.assertEqual(self.nomes(), ["veiculo", "visitante", "pessoa"])

    def test_filtro_por_nome_em_pessoa_visitante_e_dono_do_veiculo(self):
        self.entrar_pessoa(self.joao)
        self.entrar_visitante()
        self.entrar_veiculo()
        self.assertEqual(self.nomes(nome="joão"), ["pessoa"])
        self.assertEqual(self.nomes(nome="CARLOS"), ["visitante"])
        self.assertEqual(self.nomes(nome="maria da silva"), ["veiculo"])   # dono do veículo
        self.assertEqual(self.nomes(nome="zzz"), [])

    def test_filtro_por_cpf_com_ou_sem_pontuacao(self):
        self.entrar_pessoa(self.joao)
        self.entrar_visitante()
        self.entrar_veiculo()
        self.assertEqual(self.nomes(cpf="390.533.447-05"), ["pessoa"])
        self.assertEqual(self.nomes(cpf="39053344705"), ["pessoa"])
        self.assertEqual(self.nomes(cpf="529.982.247-25"), ["visitante"])
        self.assertEqual(self.nomes(cpf="111.444.777-35"), ["veiculo"])
        self.assertEqual(self.nomes(cpf="99999999999"), [])
        with self.assertRaisesRegex(ErroNegocio, "números"):
            self.historico(cpf="abc")

    def test_filtro_por_placa_aceita_traco_e_minuscula(self):
        self.entrar_pessoa()
        self.entrar_veiculo()
        self.assertEqual(self.nomes(placa="abc-1234"), ["veiculo"])
        self.assertEqual(self.nomes(placa="ABC1234"), ["veiculo"])
        self.assertEqual(self.nomes(placa="abc"), ["veiculo"])
        self.assertEqual(self.nomes(placa="XYZ9999"), [])

    def test_filtro_por_tipo(self):
        self.entrar_pessoa()
        self.entrar_visitante()
        self.entrar_veiculo()
        for tipo in ("pessoa", "visitante", "veiculo"):
            with self.subTest(tipo=tipo):
                self.assertEqual(self.nomes(tipo=tipo), [tipo])
        with self.assertRaisesRegex(ErroNegocio, "Tipo de acesso"):
            self.historico(tipo="outro")

    def test_filtro_por_data_inclui_o_dia_inicial_e_o_final(self):
        a = self.entrar_pessoa()
        b = self.entrar_visitante()
        c = self.entrar_veiculo()
        self.mudar_entrada(a, "2026-03-10 23:59:59")
        self.mudar_entrada(b, "2026-03-11 00:00:00")
        self.mudar_entrada(c, "2026-03-12 12:00:00")
        self.assertEqual(self.nomes(data_de="2026-03-11", data_ate="2026-03-11"), ["visitante"])
        self.assertEqual(self.nomes(data_de="2026-03-11"), ["veiculo", "visitante"])
        self.assertEqual(self.nomes(data_ate="2026-03-11"), ["visitante", "pessoa"])
        self.assertEqual(self.nomes(data_de="2026-03-13"), [])

    def test_datas_invalidas_sao_recusadas(self):
        with self.assertRaisesRegex(ErroNegocio, "inicial é inválida"):
            self.historico(data_de="31/02/2026")
        with self.assertRaisesRegex(ErroNegocio, "final é inválida"):
            self.historico(data_ate="abc")
        with self.assertRaisesRegex(ErroNegocio, "não pode ser depois"):
            self.historico(data_de="2026-03-12", data_ate="2026-03-10")

    def test_filtros_combinados(self):
        self.entrar_pessoa()
        self.entrar_veiculo()
        self.assertEqual(self.nomes(nome="maria", tipo="veiculo"), ["veiculo"])
        self.assertEqual(self.nomes(nome="maria", tipo="visitante"), [])

    def test_caracteres_especiais_da_busca_sao_letras_comuns(self):
        self.entrar_pessoa()
        self.assertEqual(self.nomes(nome="%"), [])
        self.assertEqual(self.nomes(nome="_"), [])

    def test_consulta_nao_altera_os_registros(self):          # UC03: pós-condição
        self.entrar_pessoa()
        self.entrar_veiculo()
        antes = [tuple(r) for r in self.consultar("SELECT * FROM registro_acesso ORDER BY id")]
        self.historico(nome="maria", cpf="111", placa="abc", data_de="2020-01-01", tipo="pessoa")
        depois = [tuple(r) for r in self.consultar("SELECT * FROM registro_acesso ORDER BY id")]
        self.assertEqual(antes, depois)

    def test_mostra_quem_ainda_esta_dentro_e_quem_ja_saiu(self):
        a = self.entrar_pessoa()
        self.executar(acesso_service.registrar_saida, a)
        self.entrar_veiculo()
        linhas = {r["tipo"]: r for r in self.historico()}
        self.assertIsNotNone(linhas["pessoa"]["saida_em"])
        self.assertIsNone(linhas["veiculo"]["saida_em"])

    def test_limite_de_linhas_avisa_que_ha_mais(self):
        self.entrar_pessoa(self.morador)
        self.entrar_pessoa(self.joao)
        self.entrar_veiculo()
        with mock.patch.object(historico_service, "LIMITE", 2):
            linhas, tem_mais = self.executar(historico_service.listar_historico)
        self.assertEqual(len(linhas), 2)
        self.assertTrue(tem_mais)
        linhas, tem_mais = self.executar(historico_service.listar_historico)
        self.assertEqual(len(linhas), 3)
        self.assertFalse(tem_mais)


class TesteHistoricoExclusaoLogica(BaseHistorico):
    def test_excluir_esconde_mas_nao_apaga(self):
        registro_id = self.entrar_pessoa()
        self.executar(historico_service.excluir_registro, registro_id)
        self.assertEqual(self.historico(), [])                                # RN-08
        admin = self.executar(lambda db: historico_service.listar_historico(db, incluir_excluidos=True))[0]
        self.assertEqual(len(admin), 1)
        self.assertEqual(admin[0]["ativo"], 0)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM registro_acesso")[0]["n"], 1)

    def test_excluir_duas_vezes_ou_inexistente_da_erro(self):
        registro_id = self.entrar_pessoa()
        self.executar(historico_service.excluir_registro, registro_id)
        with self.assertRaisesRegex(ErroNegocio, "já excluído"):
            self.executar(historico_service.excluir_registro, registro_id)
        with self.assertRaisesRegex(ErroNegocio, "não encontrado"):
            self.executar(historico_service.excluir_registro, 999)

    def test_atualizar_observacao_mexe_so_na_observacao(self):
        registro_id = self.entrar_pessoa(obs="antiga")
        antes = dict(self.registro(registro_id))
        self.executar(historico_service.atualizar_observacao, registro_id, "  corrigida  ")
        depois = dict(self.registro(registro_id))
        self.assertEqual(depois["observacao"], "corrigida")
        antes.pop("observacao"), depois.pop("observacao")
        self.assertEqual(antes, depois)

    def test_observacao_vazia_limpa_e_muito_longa_e_recusada(self):
        registro_id = self.entrar_pessoa(obs="algo")
        self.executar(historico_service.atualizar_observacao, registro_id, "   ")
        self.assertIsNone(self.registro(registro_id)["observacao"])
        with self.assertRaisesRegex(ErroNegocio, "300"):
            self.executar(historico_service.atualizar_observacao, registro_id, "x" * 301)

    def test_nao_edita_registro_excluido(self):
        registro_id = self.entrar_pessoa()
        self.executar(historico_service.excluir_registro, registro_id)
        with self.assertRaisesRegex(ErroNegocio, "excluído"):
            self.executar(historico_service.atualizar_observacao, registro_id, "x")


class TesteOcorrenciaServico(BaseHistorico):
    def test_cria_com_pessoas_envolvidas_e_quem_registrou(self):
        oc = self.criar_ocorrencia(data_hora=ONTEM_HORA, pessoas=[self.morador, self.joao])
        linha = self.consultar("SELECT * FROM ocorrencia WHERE id=?", (oc,))[0]
        self.assertEqual(linha["descricao"], "Barulho excessivo no bloco A")
        self.assertEqual(linha["registrado_por_id"], self.porteiro)
        self.assertEqual(linha["data_hora"], ONTEM_HORA.replace("T", " ") + ":00")
        self.assertEqual(linha["ativo"], 1)
        ligadas = self.consultar("SELECT pessoa_id FROM ocorrencia_pessoa WHERE ocorrencia_id=?", (oc,))
        self.assertEqual({r["pessoa_id"] for r in ligadas}, {self.morador, self.joao})

    def test_sem_data_usa_o_momento_atual(self):
        oc = self.criar_ocorrencia()
        grava = datetime.fromisoformat(self.consultar("SELECT data_hora FROM ocorrencia WHERE id=?", (oc,))[0][0])
        self.assertLess(abs((datetime.now() - grava).total_seconds()), 60)      # RN-10

    def test_pessoas_sao_opcionais_e_repetidas_contam_uma_vez(self):
        sem = self.criar_ocorrencia()
        com = self.criar_ocorrencia(pessoas=[self.morador, self.morador])
        n = lambda oc: self.consultar("SELECT COUNT(*) AS n FROM ocorrencia_pessoa WHERE ocorrencia_id=?", (oc,))[0]["n"]
        self.assertEqual((n(sem), n(com)), (0, 1))

    def test_dados_invalidos_nao_gravam_nada(self):
        casos = [
            ({"descricao": ""}, "Descreva"),
            ({"descricao": "  oi "}, "Descreva"),
            ({"descricao": "x" * 2001}, "no máximo"),
            ({"data_hora": "ontem"}, "inválidos"),
            ({"data_hora": FUTURO}, "futuro"),
            ({"pessoas": [999]}, "não foi encontrada"),
            ({"pessoas": ["abc"]}, "inválida"),
        ]
        for mudanca, trecho in casos:
            with self.subTest(mudanca=mudanca):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    self.criar_ocorrencia(**mudanca)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia")[0]["n"], 0)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia_pessoa")[0]["n"], 0)

    def test_pessoa_inativa_nao_pode_ser_envolvida(self):
        self.executar(pessoa_service.alternar_ativo, self.joao)
        with self.assertRaisesRegex(ErroNegocio, "inativo"):
            self.criar_ocorrencia(pessoas=[self.joao])

    def test_atualizar_troca_dados_e_pessoas(self):
        oc = self.criar_ocorrencia(pessoas=[self.morador])
        self.executar(ocorrencia_service.atualizar_ocorrencia, oc, ONTEM_HORA, "Descrição corrigida", [str(self.joao)])
        linha = self.consultar("SELECT * FROM ocorrencia WHERE id=?", (oc,))[0]
        self.assertEqual(linha["descricao"], "Descrição corrigida")
        ligadas = self.consultar("SELECT pessoa_id FROM ocorrencia_pessoa WHERE ocorrencia_id=?", (oc,))
        self.assertEqual([r["pessoa_id"] for r in ligadas], [self.joao])

    def test_atualizar_mantem_pessoa_que_ficou_inativa_depois(self):
        oc = self.criar_ocorrencia(pessoas=[self.joao])
        self.executar(pessoa_service.alternar_ativo, self.joao)
        self.executar(ocorrencia_service.atualizar_ocorrencia, oc, "", "Texto atualizado ok", [str(self.joao)])
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia_pessoa")[0]["n"], 1)

    def test_atualizar_invalido_preserva_o_original(self):
        oc = self.criar_ocorrencia(pessoas=[self.morador])
        with self.assertRaises(ErroNegocio):
            self.executar(ocorrencia_service.atualizar_ocorrencia, oc, "", "x", [str(self.joao)])
        self.assertEqual(self.consultar("SELECT descricao FROM ocorrencia")[0][0], "Barulho excessivo no bloco A")
        self.assertEqual(self.consultar("SELECT pessoa_id FROM ocorrencia_pessoa")[0][0], self.morador)

    def test_excluir_e_logico(self):
        oc = self.criar_ocorrencia()
        self.executar(ocorrencia_service.excluir_ocorrencia, oc)
        self.assertEqual(self.ocorrencias(), [])
        self.assertEqual(len(self.ocorrencias(incluir_excluidas=True)), 1)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia")[0]["n"], 1)
        with self.assertRaisesRegex(ErroNegocio, "já excluída"):
            self.executar(ocorrencia_service.excluir_ocorrencia, oc)
        with self.assertRaisesRegex(ErroNegocio, "já excluída"):
            self.executar(ocorrencia_service.atualizar_ocorrencia, oc, "", "Novo texto aqui", [])

    def test_listagem_mostra_envolvidos_e_filtra_por_periodo(self):
        self.criar_ocorrencia("Primeira ocorrência", "2026-02-01T10:00", [self.joao, self.morador])
        self.criar_ocorrencia("Segunda ocorrência", "2026-02-10T10:00")
        todas = self.ocorrencias()
        self.assertEqual([o["descricao"] for o in todas], ["Segunda ocorrência", "Primeira ocorrência"])
        self.assertEqual(todas[1]["envolvidos"], "João Pereira, Maria da Silva")
        self.assertIsNone(todas[0]["envolvidos"])
        self.assertEqual(todas[1]["registrador"], "porteiro1")
        periodo = self.ocorrencias(data_de="2026-02-05", data_ate="2026-02-10")
        self.assertEqual([o["descricao"] for o in periodo], ["Segunda ocorrência"])
        with self.assertRaisesRegex(ErroNegocio, "inválida"):
            self.ocorrencias(data_de="xx")


class TesteTelasEPermissoes(BaseHistorico):
    def cliente(self, login):
        return self.entrar(login)[0]

    def test_sem_login_vai_para_o_login(self):
        for url in ("/historico/", "/ocorrencias/"):
            resposta = self.app.test_client().get(url)
            self.assertEqual(resposta.status_code, 302)
            self.assertIn("/login", resposta.headers["Location"])

    def test_quem_pode_ver_o_historico(self):
        for login, esperado in (("admin", 200), ("porteiro1", 200), ("gerente1", 200), ("func1", 403)):
            with self.subTest(login=login):
                self.assertEqual(self.cliente(login).get("/historico/").status_code, esperado)

    def test_quem_pode_ver_as_ocorrencias(self):
        for login, esperado in (("admin", 200), ("porteiro1", 200), ("gerente1", 403), ("func1", 403)):
            with self.subTest(login=login):
                self.assertEqual(self.cliente(login).get("/ocorrencias/").status_code, esperado)
                self.assertEqual(self.cliente(login).get("/ocorrencias/nova").status_code, esperado)

    def test_historico_mostra_dados_e_aplica_filtros(self):
        self.entrar_pessoa()
        self.entrar_veiculo()
        pagina = self.cliente("porteiro1").get("/historico/").get_data(as_text=True)
        self.assertIn("Maria da Silva", pagina)
        self.assertIn("ABC-1234", pagina)
        filtrada = self.cliente("porteiro1").get("/historico/?tipo=veiculo&placa=abc").get_data(as_text=True)
        self.assertIn("ABC-1234", filtrada)
        vazia = self.cliente("porteiro1").get("/historico/?nome=zzz").get_data(as_text=True)
        self.assertIn("Nenhum registro encontrado", vazia)

    def test_filtro_invalido_mostra_mensagem_sem_quebrar(self):
        resposta = self.cliente("porteiro1").get("/historico/?data_de=abc")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("inválida", resposta.get_data(as_text=True))

    def test_aprovador_consulta_mas_nao_ve_botoes_de_alteracao(self):
        self.entrar_pessoa()
        pagina = self.cliente("gerente1").get("/historico/").get_data(as_text=True)
        self.assertIn("Maria da Silva", pagina)
        self.assertNotIn("Excluir", pagina)

    def test_so_o_administrador_edita_ou_exclui_acessos(self):
        registro_id = self.entrar_pessoa()
        for login in ("porteiro1", "gerente1", "func1"):
            with self.subTest(login=login):
                c = self.cliente(login)
                self.assertEqual(c.get(f"/historico/{registro_id}/editar").status_code, 403)
                self.assertEqual(self.enviar(c, f"/historico/{registro_id}/editar", {"observacao": "x"}).status_code, 403)
                self.assertEqual(self.enviar(c, f"/historico/{registro_id}/excluir").status_code, 403)
        self.assertEqual(self.registro(registro_id)["ativo"], 1)

        admin = self.cliente("admin")
        self.assertEqual(admin.get(f"/historico/{registro_id}/editar").status_code, 200)
        resposta = self.enviar(admin, f"/historico/{registro_id}/editar", {"observacao": "Corrigido"})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.registro(registro_id)["observacao"], "Corrigido")
        self.assertEqual(self.enviar(admin, f"/historico/{registro_id}/excluir").status_code, 302)
        self.assertEqual(self.registro(registro_id)["ativo"], 0)
        self.assertEqual(admin.get(f"/historico/{registro_id}/editar").status_code, 404)

    def test_registro_excluido_so_aparece_para_o_administrador(self):
        registro_id = self.entrar_pessoa()
        self.executar(historico_service.excluir_registro, registro_id)
        self.assertNotIn("Maria da Silva", self.cliente("porteiro1").get("/historico/").get_data(as_text=True))
        pagina = self.cliente("admin").get("/historico/").get_data(as_text=True)
        self.assertIn("Maria da Silva", pagina)
        self.assertIn("Excluído", pagina)

    def test_exclusao_sem_token_csrf_e_recusada(self):
        registro_id = self.entrar_pessoa()
        c = self.cliente("admin")
        self.assertEqual(c.post(f"/historico/{registro_id}/excluir").status_code, 400)
        self.assertEqual(self.registro(registro_id)["ativo"], 1)

    def test_porteiro_registra_ocorrencia_pela_tela(self):
        c = self.cliente("porteiro1")
        resposta = self.enviar(c, "/ocorrencias/nova", {
            "data_hora": ONTEM_HORA, "descricao": "Portão ficou aberto durante a noite",
            "pessoas": [str(self.morador), str(self.joao)]})
        self.assertEqual(resposta.status_code, 302)
        pagina = c.get("/ocorrencias/").get_data(as_text=True)
        self.assertIn("Portão ficou aberto", pagina)
        self.assertIn("Maria da Silva", pagina)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia_pessoa")[0]["n"], 2)

    def test_ocorrencia_invalida_volta_ao_formulario_com_os_dados_digitados(self):
        c = self.cliente("porteiro1")
        resposta = self.enviar(c, "/ocorrencias/nova", {
            "data_hora": FUTURO, "descricao": "Texto que será mantido", "pessoas": [str(self.joao)]})
        pagina = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("futuro", pagina)
        self.assertIn("Texto que será mantido", pagina)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM ocorrencia")[0]["n"], 0)

    def test_descricao_com_html_e_exibida_como_texto(self):
        c = self.cliente("porteiro1")
        self.enviar(c, "/ocorrencias/nova", {"data_hora": ONTEM_HORA, "descricao": "<script>alert(1)</script> teste"})
        pagina = c.get("/ocorrencias/").get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", pagina)
        self.assertIn("&lt;script&gt;", pagina)

    def test_so_o_administrador_edita_ou_exclui_ocorrencias(self):
        oc = self.criar_ocorrencia()
        for login in ("porteiro1", "gerente1", "func1"):
            with self.subTest(login=login):
                c = self.cliente(login)
                self.assertEqual(c.get(f"/ocorrencias/{oc}/editar").status_code, 403)
                self.assertEqual(self.enviar(c, f"/ocorrencias/{oc}/editar", {"descricao": "mudou aqui"}).status_code, 403)
                self.assertEqual(self.enviar(c, f"/ocorrencias/{oc}/excluir").status_code, 403)
        self.assertEqual(self.consultar("SELECT descricao, ativo FROM ocorrencia")[0][0], "Barulho excessivo no bloco A")

        admin = self.cliente("admin")
        self.assertEqual(admin.get(f"/ocorrencias/{oc}/editar").status_code, 200)
        resposta = self.enviar(admin, f"/ocorrencias/{oc}/editar", {
            "data_hora": ONTEM_HORA, "descricao": "Descrição corrigida pelo admin", "pessoas": [str(self.joao)]})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.consultar("SELECT descricao FROM ocorrencia")[0][0], "Descrição corrigida pelo admin")
        self.assertEqual(self.enviar(admin, f"/ocorrencias/{oc}/excluir").status_code, 302)
        self.assertEqual(self.consultar("SELECT ativo FROM ocorrencia")[0][0], 0)
        self.assertEqual(admin.get(f"/ocorrencias/{oc}/editar").status_code, 404)

    def test_ocorrencia_excluida_so_aparece_para_o_administrador(self):
        oc = self.criar_ocorrencia("Ocorrência que será excluída")
        self.executar(ocorrencia_service.excluir_ocorrencia, oc)
        self.assertNotIn("será excluída", self.cliente("porteiro1").get("/ocorrencias/").get_data(as_text=True))
        self.assertIn("será excluída", self.cliente("admin").get("/ocorrencias/").get_data(as_text=True))

    def test_menu_mostra_so_o_que_o_perfil_pode_usar(self):
        self.assertIn("/historico/", self.cliente("gerente1").get("/").get_data(as_text=True))
        self.assertNotIn("/ocorrencias/", self.cliente("gerente1").get("/").get_data(as_text=True))
        menu = self.cliente("porteiro1").get("/").get_data(as_text=True)
        self.assertIn("/historico/", menu)
        self.assertIn("/ocorrencias/", menu)
        self.assertNotIn("/historico/", self.cliente("func1").get("/").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
