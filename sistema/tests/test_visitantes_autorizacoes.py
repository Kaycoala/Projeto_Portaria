"""Testes de visitantes e autorizações (V0.5.0).
Execute com: python -m unittest discover tests -v
"""
import unittest
from datetime import date, timedelta

from app.db import conectar
from app.services import autorizacao_service, pessoa_service, visitante_service
from app.services.erros import ErroNegocio
from tests.test_pessoas_veiculos import BasePessoasVeiculos

HOJE = date.today()
ONTEM = (HOJE - timedelta(days=1)).isoformat()
AMANHA = (HOJE + timedelta(days=1)).isoformat()
DEPOIS = (HOJE + timedelta(days=3)).isoformat()


def dados_visitante(pessoa_id, **mudancas):
    dados = {"nome": "Carlos Visitante", "cpf": "529.982.247-25", "telefone": "(11) 98888-7777",
             "pessoa_visitada_id": str(pessoa_id), "motivo": "Entrega de documentos"}
    dados.update(mudancas)
    return dados


class BaseVisitantes(BasePessoasVeiculos):
    def setUp(self):
        super().setUp()
        self.morador = self.criar_pessoa()

    def criar_visitante(self, **mudancas):
        db = conectar(self.caminho)
        try:
            return visitante_service.criar_visitante(db, **dados_visitante(self.morador, **mudancas))
        finally:
            db.close()

    def autorizacao(self, autorizacao_id):
        return self.consultar("SELECT * FROM autorizacao WHERE id=?", (autorizacao_id,))[0]


class TesteVisitanteServico(BaseVisitantes):
    def test_cria_visitante_e_solicitacao_pendente(self):
        visitante_id, autorizacao_id = self.criar_visitante()
        v = self.consultar("SELECT * FROM visitante WHERE id=?", (visitante_id,))[0]
        self.assertEqual(v["cpf"], "52998224725")
        self.assertEqual(v["telefone"], "11988887777")
        self.assertEqual(v["pessoa_visitada_id"], self.morador)
        a = self.autorizacao(autorizacao_id)
        self.assertEqual(a["status"], "pendente")        # RN-09
        self.assertEqual(a["visitante_id"], visitante_id)
        self.assertIsNone(a["aprovador_id"])

    def test_mesmo_cpf_pode_visitar_varias_vezes(self):
        self.criar_visitante()
        self.criar_visitante(motivo="Outra visita")
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM visitante")[0]["n"], 2)

    def test_dados_invalidos_sao_recusados(self):
        db = conectar(self.caminho)
        casos = [
            ({"nome": "Jo"}, "nome completo"),
            ({"cpf": "123"}, "11 números"),
            ({"telefone": "123"}, "telefone"),
            ({"pessoa_visitada_id": ""}, "pessoa que será visitada"),
            ({"pessoa_visitada_id": "999"}, "não encontrada"),
            ({"motivo": "  "}, "motivo"),
        ]
        for mudanca, trecho in casos:
            with self.subTest(mudanca=mudanca):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    visitante_service.criar_visitante(db, **dados_visitante(self.morador, **mudanca))
        db.close()
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM visitante")[0]["n"], 0)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM autorizacao")[0]["n"], 0)

    def test_pessoa_visitada_inativa_e_recusada(self):
        db = conectar(self.caminho)
        pessoa_service.alternar_ativo(db, self.morador)
        with self.assertRaisesRegex(ErroNegocio, "inativa"):
            visitante_service.criar_visitante(db, **dados_visitante(self.morador))
        db.close()

    def test_atualizar_visitante_nao_mexe_na_autorizacao(self):
        visitante_id, autorizacao_id = self.criar_visitante()
        db = conectar(self.caminho)
        visitante_service.atualizar_visitante(
            db, visitante_id, **dados_visitante(self.morador, nome="Carlos Souza"))
        db.close()
        self.assertEqual(self.consultar("SELECT nome FROM visitante")[0]["nome"], "Carlos Souza")
        self.assertEqual(self.autorizacao(autorizacao_id)["status"], "pendente")

    def test_listagem_mostra_a_ultima_autorizacao_e_busca(self):
        self.criar_visitante()
        self.criar_visitante(nome="Ana Convidada", cpf="11144477735")
        db = conectar(self.caminho)
        self.assertEqual(len(visitante_service.listar_visitantes(db)), 2)
        self.assertEqual(visitante_service.listar_visitantes(db)[0]["nome"], "Ana Convidada")  # mais recente
        self.assertEqual([v["nome"] for v in visitante_service.listar_visitantes(db, "ana")], ["Ana Convidada"])
        self.assertEqual([v["nome"] for v in visitante_service.listar_visitantes(db, "529.982")], ["Carlos Visitante"])
        self.assertEqual(visitante_service.listar_visitantes(db, "zzz"), [])
        self.assertEqual(visitante_service.listar_visitantes(db)[0]["status"], "pendente")
        db.close()


class TesteAutorizacaoServico(BaseVisitantes):
    def setUp(self):
        super().setUp()
        self.visitante_id, self.aut_id = self.criar_visitante()
        self.gerente = self.id_de("gerente1")

    def test_aprovar_registra_decisao_completa(self):
        db = conectar(self.caminho)
        autorizacao_service.aprovar(db, self.aut_id, self.gerente, AMANHA, DEPOIS, "Pode subir")
        db.close()
        a = self.autorizacao(self.aut_id)
        self.assertEqual(a["status"], "aprovada")
        self.assertEqual((a["data_inicio"], a["data_fim"]), (AMANHA, DEPOIS))
        self.assertEqual(a["aprovador_id"], self.gerente)
        self.assertIsNotNone(a["decidido_em"])
        self.assertEqual(a["observacao"], "Pode subir")

    def test_aprovar_sem_data_final_vale_so_no_dia(self):
        db = conectar(self.caminho)
        autorizacao_service.aprovar(db, self.aut_id, self.gerente, AMANHA, "")
        db.close()
        a = self.autorizacao(self.aut_id)
        self.assertEqual((a["data_inicio"], a["data_fim"]), (AMANHA, AMANHA))

    def test_aprovar_com_datas_invalidas(self):
        db = conectar(self.caminho)
        casos = [
            ((AMANHA, ONTEM), "anterior"),
            (("", ""), "data de início"),
            (("31/12/2030", ""), "data de início"),
            ((ONTEM, ONTEM), "já terminou"),
        ]
        for (inicio, fim), trecho in casos:
            with self.subTest(inicio=inicio, fim=fim):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    autorizacao_service.aprovar(db, self.aut_id, self.gerente, inicio, fim)
        db.close()
        self.assertEqual(self.autorizacao(self.aut_id)["status"], "pendente")

    def test_negar_registra_decisao(self):
        db = conectar(self.caminho)
        autorizacao_service.negar(db, self.aut_id, self.gerente, "Não esperado")
        db.close()
        a = self.autorizacao(self.aut_id)
        self.assertEqual(a["status"], "negada")
        self.assertEqual(a["aprovador_id"], self.gerente)
        self.assertIsNotNone(a["decidido_em"])
        self.assertEqual(a["observacao"], "Não esperado")
        self.assertIsNone(a["data_inicio"])

    def test_decisao_nao_pode_ser_refeita(self):
        db = conectar(self.caminho)
        autorizacao_service.negar(db, self.aut_id, self.gerente)
        with self.assertRaisesRegex(ErroNegocio, "já foi decidida"):
            autorizacao_service.aprovar(db, self.aut_id, self.gerente, AMANHA, "")
        with self.assertRaisesRegex(ErroNegocio, "já foi decidida"):
            autorizacao_service.negar(db, self.aut_id, self.gerente)
        db.close()
        self.assertEqual(self.autorizacao(self.aut_id)["status"], "negada")

    def test_autorizacao_inexistente(self):
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "não encontrada"):
            autorizacao_service.negar(db, 999, self.gerente)
        db.close()

    def test_nova_solicitacao_so_depois_de_decidida(self):
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "aguardando decisão"):
            autorizacao_service.solicitar_nova(db, self.visitante_id)
        autorizacao_service.negar(db, self.aut_id, self.gerente)
        nova = autorizacao_service.solicitar_nova(db, self.visitante_id)
        ultimo = visitante_service.buscar_visitante(db, self.visitante_id)
        db.close()
        self.assertEqual(self.autorizacao(nova)["status"], "pendente")
        self.assertEqual(self.autorizacao(self.aut_id)["status"], "negada")    # histórico preservado
        self.assertEqual(ultimo["autorizacao_id"], nova)

    def test_nova_solicitacao_de_visitante_inexistente(self):
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "não encontrado"):
            autorizacao_service.solicitar_nova(db, 999)
        db.close()

    def test_listar_por_status_e_contar(self):
        _, outra = self.criar_visitante(nome="Ana Convidada")
        db = conectar(self.caminho)
        autorizacao_service.aprovar(db, outra, self.gerente, AMANHA, "")
        self.assertEqual([a["id"] for a in autorizacao_service.listar_autorizacoes(db)], [self.aut_id])
        self.assertEqual([a["id"] for a in autorizacao_service.listar_autorizacoes(db, "aprovada")], [outra])
        self.assertEqual(autorizacao_service.listar_autorizacoes(db, "negada"), [])
        self.assertEqual(len(autorizacao_service.listar_autorizacoes(db, "todas")), 2)
        self.assertEqual(autorizacao_service.contar_por_status(db),
                         {"pendente": 1, "aprovada": 1, "negada": 0})
        db.close()

    def test_formatar_data(self):
        self.assertEqual(autorizacao_service.formatar_data("2026-11-04"), "04/11/2026")
        self.assertEqual(autorizacao_service.formatar_data("2026-11-04 20:30:15"), "04/11/2026 20:30")
        self.assertEqual(autorizacao_service.formatar_data(None), "—")


class TesteTelasPermissoes(BaseVisitantes):
    def test_sem_login_redireciona(self):
        for url in ("/visitantes/", "/visitantes/novo", "/autorizacoes/"):
            with self.subTest(url=url):
                resposta = self.app.test_client().get(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/login", resposta.headers["Location"])

    def test_porteiro_cadastra_mas_nao_autoriza(self):
        cliente, _ = self.entrar("porteiro1")
        self.assertEqual(cliente.get("/visitantes/").status_code, 200)
        self.assertEqual(cliente.get("/visitantes/novo").status_code, 200)
        self.assertEqual(cliente.get("/autorizacoes/").status_code, 403)

    def test_aprovador_autoriza_mas_nao_cadastra(self):
        cliente, _ = self.entrar("gerente1")
        self.assertEqual(cliente.get("/autorizacoes/").status_code, 200)
        self.assertEqual(cliente.get("/visitantes/").status_code, 403)
        self.assertEqual(cliente.get("/visitantes/novo").status_code, 403)
        resposta = self.enviar(cliente, "/visitantes/novo", dados_visitante(self.morador))
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM visitante")[0]["n"], 0)

    def test_admin_acessa_tudo(self):
        cliente, _ = self.entrar("admin")
        for url in ("/visitantes/", "/visitantes/novo", "/autorizacoes/"):
            self.assertEqual(cliente.get(url).status_code, 200)

    def test_funcionario_nao_acessa_nada(self):
        cliente, _ = self.entrar("func1")
        for url in ("/visitantes/", "/visitantes/novo", "/autorizacoes/"):
            self.assertEqual(cliente.get(url).status_code, 403)

    def test_so_admin_edita_visitante(self):
        visitante_id, _ = self.criar_visitante()
        url = f"/visitantes/{visitante_id}/editar"
        for login in ("porteiro1", "gerente1", "func1"):
            cliente, _ = self.entrar(login)
            self.assertEqual(cliente.get(url).status_code, 403, login)
            self.assertEqual(self.enviar(cliente, url, dados_visitante(self.morador, nome="Hacker Nome")).status_code, 403)
        self.assertEqual(self.consultar("SELECT nome FROM visitante")[0]["nome"], "Carlos Visitante")
        cliente, _ = self.entrar("admin")
        self.assertEqual(cliente.get(url).status_code, 200)
        self.assertEqual(self.enviar(cliente, url, dados_visitante(self.morador, nome="Carlos Souza")).status_code, 302)
        self.assertEqual(self.consultar("SELECT nome FROM visitante")[0]["nome"], "Carlos Souza")

    def test_menu_por_perfil(self):
        casos = {"porteiro1": (True, False), "gerente1": (False, True),
                 "admin": (True, True), "func1": (False, False)}
        for login, (ve_visitantes, ve_autorizacoes) in casos.items():
            with self.subTest(login=login):
                cliente, _ = self.entrar(login)
                html = cliente.get("/").get_data(as_text=True)
                self.assertEqual('href="/visitantes/"' in html, ve_visitantes)
                self.assertEqual('href="/autorizacoes/"' in html, ve_autorizacoes)

    def test_fluxo_completo_pelas_telas(self):
        porteiro, _ = self.entrar("porteiro1")
        resposta = self.enviar(porteiro, "/visitantes/novo", dados_visitante(self.morador))
        self.assertEqual(resposta.status_code, 302)
        html = porteiro.get("/visitantes/").get_data(as_text=True)
        self.assertIn("Carlos Visitante", html)
        self.assertIn("Aguardando autorização", html)
        self.assertIn("529.982.247-25", html)

        gerente, _ = self.entrar("gerente1")
        html = gerente.get("/autorizacoes/").get_data(as_text=True)
        self.assertIn("Carlos Visitante", html)
        self.assertIn("Analisar", html)
        html = gerente.get("/autorizacoes/1").get_data(as_text=True)
        self.assertIn("Entrega de documentos", html)

        resposta = self.enviar(gerente, "/autorizacoes/1", {
            "acao": "aprovar", "data_inicio": AMANHA, "data_fim": DEPOIS, "observacao": "ok"})
        self.assertEqual(resposta.status_code, 302)
        html = gerente.get("/autorizacoes/").get_data(as_text=True)
        self.assertIn("Nenhuma solicitação aguardando decisão", html)
        html = gerente.get("/autorizacoes/?status=aprovada").get_data(as_text=True)
        self.assertIn("Carlos Visitante", html)
        self.assertIn("Ver decisão", html)

        html = porteiro.get("/visitantes/").get_data(as_text=True)     # porteiro vê o resultado
        self.assertIn("Autorizada", html)
        self.assertIn(date.fromisoformat(AMANHA).strftime("%d/%m/%Y"), html)
        self.assertIn("Nova solicitação", html)

        html = gerente.get("/autorizacoes/1").get_data(as_text=True)    # decisão consultável, sem formulário
        self.assertIn("gerente1", html)
        self.assertNotIn('value="aprovar"', html)

    def test_negar_pelas_telas_e_nao_decidir_de_novo(self):
        _, aut_id = self.criar_visitante()
        gerente, _ = self.entrar("gerente1")
        self.enviar(gerente, f"/autorizacoes/{aut_id}", {"acao": "negar", "observacao": "Sem convite"})
        self.assertEqual(self.autorizacao(aut_id)["status"], "negada")
        resposta = self.enviar(gerente, f"/autorizacoes/{aut_id}",
                               {"acao": "aprovar", "data_inicio": AMANHA})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("já foi decidida", resposta.get_data(as_text=True))
        self.assertEqual(self.autorizacao(aut_id)["status"], "negada")

    def test_erro_de_data_mostra_mensagem_e_nao_decide(self):
        _, aut_id = self.criar_visitante()
        gerente, _ = self.entrar("gerente1")
        resposta = self.enviar(gerente, f"/autorizacoes/{aut_id}", {
            "acao": "aprovar", "data_inicio": AMANHA, "data_fim": ONTEM})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("anterior à data de início", resposta.get_data(as_text=True))
        self.assertEqual(self.autorizacao(aut_id)["status"], "pendente")

    def test_acao_invalida_nao_decide(self):
        _, aut_id = self.criar_visitante()
        gerente, _ = self.entrar("gerente1")
        resposta = self.enviar(gerente, f"/autorizacoes/{aut_id}", {"acao": "qualquer"})
        self.assertIn("Escolha autorizar ou negar", resposta.get_data(as_text=True))
        self.assertEqual(self.autorizacao(aut_id)["status"], "pendente")

    def test_autorizacao_inexistente_da_404(self):
        gerente, _ = self.entrar("gerente1")
        self.assertEqual(gerente.get("/autorizacoes/999").status_code, 404)

    def test_porteiro_nao_decide_autorizacao(self):
        _, aut_id = self.criar_visitante()
        porteiro, _ = self.entrar("porteiro1")
        resposta = self.enviar(porteiro, f"/autorizacoes/{aut_id}",
                               {"acao": "aprovar", "data_inicio": AMANHA})
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.autorizacao(aut_id)["status"], "pendente")

    def test_erro_no_cadastro_mantem_o_formulario(self):
        porteiro, _ = self.entrar("porteiro1")
        resposta = self.enviar(porteiro, "/visitantes/novo",
                               dados_visitante(self.morador, cpf="123", nome="Maria Teste"))
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn("11 números", html)
        self.assertIn("Maria Teste", html)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM visitante")[0]["n"], 0)

    def test_nova_solicitacao_pela_tela(self):
        _, aut_id = self.criar_visitante()
        visitante_id = self.consultar("SELECT id FROM visitante")[0]["id"]
        porteiro, _ = self.entrar("porteiro1")
        # ainda pendente: recusa
        self.enviar(porteiro, f"/visitantes/{visitante_id}/solicitar")
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM autorizacao")[0]["n"], 1)
        gerente, _ = self.entrar("gerente1")
        self.enviar(gerente, f"/autorizacoes/{aut_id}", {"acao": "negar"})
        self.enviar(porteiro, f"/visitantes/{visitante_id}/solicitar")
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM autorizacao")[0]["n"], 2)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM autorizacao WHERE status='pendente'")[0]["n"], 1)
        # aprovador não pode abrir solicitação
        self.assertEqual(self.enviar(gerente, f"/visitantes/{visitante_id}/solicitar").status_code, 403)

    def test_post_sem_token_csrf_e_recusado(self):
        _, aut_id = self.criar_visitante()
        gerente, _ = self.entrar("gerente1")
        resposta = gerente.post(f"/autorizacoes/{aut_id}", data={"acao": "negar"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.autorizacao(aut_id)["status"], "pendente")


if __name__ == "__main__":
    unittest.main()
