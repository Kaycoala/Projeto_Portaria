"""Testes de entrada e saída de pessoas, visitantes e veículos (V0.6.0).
Execute com: python -m unittest discover tests -v
"""
import unittest
from datetime import date, timedelta

from app.db import conectar
from app.services import acesso_service, autorizacao_service, pessoa_service, veiculo_service
from app.services.erros import ErroNegocio
from tests.test_visitantes_autorizacoes import AMANHA, DEPOIS, HOJE, BaseVisitantes

HOJE_TXT = HOJE.isoformat()


class BaseAcessos(BaseVisitantes):
    def setUp(self):
        super().setUp()
        self.porteiro = self.id_de("porteiro1")
        self.gerente = self.id_de("gerente1")

    def executar(self, funcao, *args):
        db = conectar(self.caminho)
        try:
            return funcao(db, *args)
        finally:
            db.close()

    def entrar_pessoa(self, pessoa_id=None, obs=""):
        return self.executar(acesso_service.registrar_entrada_pessoa,
                             pessoa_id or self.morador, self.porteiro, obs)

    def visitante_autorizado(self, inicio=HOJE_TXT, fim=""):
        visitante_id, aut_id = self.criar_visitante()
        self.executar(autorizacao_service.aprovar, aut_id, self.gerente, inicio, fim)
        return visitante_id

    def registro(self, registro_id):
        return self.consultar("SELECT * FROM registro_acesso WHERE id=?", (registro_id,))[0]

    def total_registros(self):
        return self.consultar("SELECT COUNT(*) AS n FROM registro_acesso")[0]["n"]


class TesteEntradaPessoa(BaseAcessos):
    def test_entrada_grava_data_hora_e_porteiro(self):
        registro_id = self.entrar_pessoa(obs="  Reunião  ")
        r = self.registro(registro_id)
        self.assertEqual(r["tipo"], "pessoa")
        self.assertEqual(r["pessoa_id"], self.morador)
        self.assertTrue(r["entrada_em"].startswith(HOJE_TXT))     # RN-02
        self.assertIsNone(r["saida_em"])
        self.assertEqual(r["porteiro_id"], self.porteiro)
        self.assertEqual(r["observacao"], "Reunião")
        self.assertEqual(r["ativo"], 1)

    def test_pessoa_ja_dentro_nao_entra_de_novo(self):
        self.entrar_pessoa()
        with self.assertRaisesRegex(ErroNegocio, "já está dentro"):
            self.entrar_pessoa()
        self.assertEqual(self.total_registros(), 1)

    def test_pessoa_pode_entrar_de_novo_depois_da_saida(self):
        primeiro = self.entrar_pessoa()
        self.executar(acesso_service.registrar_saida, primeiro)
        segundo = self.entrar_pessoa()
        self.assertNotEqual(primeiro, segundo)
        self.assertEqual(self.total_registros(), 2)

    def test_pessoa_inexistente_inativa_ou_invalida(self):
        with self.assertRaisesRegex(ErroNegocio, "Cadastre-a"):
            self.entrar_pessoa(999)
        with self.assertRaisesRegex(ErroNegocio, "Escolha a pessoa"):
            self.executar(acesso_service.registrar_entrada_pessoa, "", self.porteiro, "")
        self.executar(pessoa_service.alternar_ativo, self.morador)
        with self.assertRaisesRegex(ErroNegocio, "inativo"):
            self.entrar_pessoa()
        self.assertEqual(self.total_registros(), 0)


class TesteSaida(BaseAcessos):
    def test_saida_preenche_horario_e_preserva_o_registro(self):
        registro_id = self.entrar_pessoa()
        self.executar(acesso_service.registrar_saida, registro_id)
        r = self.registro(registro_id)
        self.assertIsNotNone(r["saida_em"])                       # RN-04
        self.assertGreaterEqual(r["saida_em"], r["entrada_em"])
        self.assertEqual(r["ativo"], 1)                           # RN-08: não apaga
        self.assertEqual(self.total_registros(), 1)

    def test_saida_so_uma_vez(self):
        registro_id = self.entrar_pessoa()
        self.executar(acesso_service.registrar_saida, registro_id)
        with self.assertRaisesRegex(ErroNegocio, "já foi registrada"):
            self.executar(acesso_service.registrar_saida, registro_id)

    def test_saida_sem_entrada(self):
        with self.assertRaisesRegex(ErroNegocio, "não encontrado"):
            self.executar(acesso_service.registrar_saida, 999)

    def test_lista_de_quem_esta_dentro(self):
        pessoa = self.entrar_pessoa()
        veiculo_id = self.criar_veiculo(self.morador)
        self.executar(acesso_service.registrar_entrada_veiculo, veiculo_id, self.porteiro, "")
        db = conectar(self.caminho)
        dentro = acesso_service.listar_dentro(db)
        self.assertEqual([r["tipo"] for r in dentro], ["pessoa", "veiculo"])
        self.assertEqual(dentro[0]["pessoa_nome"], "Maria da Silva")
        self.assertEqual(dentro[1]["placa"], "ABC1234")
        self.assertEqual(dentro[1]["proprietario_nome"], "Maria da Silva")
        acesso_service.registrar_saida(db, pessoa)
        self.assertEqual([r["tipo"] for r in acesso_service.listar_dentro(db)], ["veiculo"])
        db.close()


class TesteEntradaVisitante(BaseAcessos):
    def test_visitante_autorizado_hoje_entra(self):
        visitante_id = self.visitante_autorizado()
        registro_id = self.executar(acesso_service.registrar_entrada_visitante,
                                    visitante_id, self.porteiro, "")
        r = self.registro(registro_id)
        self.assertEqual((r["tipo"], r["visitante_id"], r["pessoa_id"]), ("visitante", visitante_id, None))
        self.assertTrue(r["entrada_em"].startswith(HOJE_TXT))

    def test_visitante_no_periodo_entra(self):
        visitante_id = self.visitante_autorizado(inicio=HOJE_TXT, fim=DEPOIS)
        self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")

    def test_visitante_pendente_e_bloqueado(self):
        visitante_id, _ = self.criar_visitante()
        with self.assertRaisesRegex(ErroNegocio, "aguardando autorização"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")
        self.assertEqual(self.total_registros(), 0)

    def test_visitante_negado_e_bloqueado(self):
        visitante_id, aut_id = self.criar_visitante()
        self.executar(autorizacao_service.negar, aut_id, self.gerente, "")
        with self.assertRaisesRegex(ErroNegocio, "negada"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")
        self.assertEqual(self.total_registros(), 0)

    def test_autorizacao_de_data_futura_e_bloqueada(self):
        visitante_id = self.visitante_autorizado(inicio=AMANHA, fim=DEPOIS)
        with self.assertRaisesRegex(ErroNegocio, "só vale a partir de"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")

    def test_autorizacao_vencida_e_bloqueada(self):
        visitante_id = self.visitante_autorizado()
        ontem = (HOJE - timedelta(days=1)).isoformat()
        db = conectar(self.caminho)
        db.execute("UPDATE autorizacao SET data_inicio = ?, data_fim = ?", (ontem, ontem))
        db.commit()
        db.close()
        with self.assertRaisesRegex(ErroNegocio, "venceu em"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")

    def test_a_autorizacao_mais_recente_vale(self):
        visitante_id = self.visitante_autorizado()
        self.executar(autorizacao_service.solicitar_nova, visitante_id)       # nova solicitação pendente
        with self.assertRaisesRegex(ErroNegocio, "aguardando autorização"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")

    def test_visitante_ja_dentro_e_visitante_inexistente(self):
        visitante_id = self.visitante_autorizado()
        registro_id = self.executar(acesso_service.registrar_entrada_visitante,
                                    visitante_id, self.porteiro, "")
        with self.assertRaisesRegex(ErroNegocio, "já está dentro"):
            self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")
        self.executar(acesso_service.registrar_saida, registro_id)
        self.executar(acesso_service.registrar_entrada_visitante, visitante_id, self.porteiro, "")
        with self.assertRaisesRegex(ErroNegocio, "não encontrado"):
            self.executar(acesso_service.registrar_entrada_visitante, 999, self.porteiro, "")
        with self.assertRaisesRegex(ErroNegocio, "Escolha o visitante"):
            self.executar(acesso_service.registrar_entrada_visitante, "x", self.porteiro, "")

    def test_lista_de_visitantes_mostra_situacao(self):
        autorizado = self.visitante_autorizado()
        pendente, _ = self.criar_visitante(nome="Ana Convidada", cpf="11144477735")
        db = conectar(self.caminho)
        situacoes = {v["id"]: v["status"] for v in acesso_service.listar_visitantes_para_entrada(db)}
        self.assertEqual(situacoes, {autorizado: "aprovada", pendente: "pendente"})
        acesso_service.registrar_entrada_visitante(db, autorizado, self.porteiro, "")
        self.assertEqual([v["id"] for v in acesso_service.listar_visitantes_para_entrada(db)], [pendente])
        db.close()


class TesteEntradaVeiculo(BaseAcessos):
    def setUp(self):
        super().setUp()
        self.veiculo = self.criar_veiculo(self.morador)

    def entrar_veiculo(self, veiculo_id=None):
        return self.executar(acesso_service.registrar_entrada_veiculo,
                             veiculo_id or self.veiculo, self.porteiro, "")

    def test_entrada_de_veiculo_registra_proprietario(self):
        r = self.registro(self.entrar_veiculo())
        self.assertEqual((r["tipo"], r["veiculo_id"], r["pessoa_id"]), ("veiculo", self.veiculo, self.morador))
        self.assertTrue(r["entrada_em"].startswith(HOJE_TXT))
        self.assertIsNone(r["saida_em"])

    def test_veiculo_ja_dentro_e_saida(self):
        registro_id = self.entrar_veiculo()
        with self.assertRaisesRegex(ErroNegocio, "já está dentro"):
            self.entrar_veiculo()
        self.executar(acesso_service.registrar_saida, registro_id)
        self.assertIsNotNone(self.registro(registro_id)["saida_em"])
        self.entrar_veiculo()

    def test_veiculo_pessoa_e_veiculo_dentro_ao_mesmo_tempo(self):
        self.entrar_pessoa()
        self.entrar_veiculo()                                     # mesmo dono, registros independentes
        self.assertEqual(self.total_registros(), 2)

    def test_veiculo_inexistente_inativo_ou_de_dono_inativo(self):
        with self.assertRaisesRegex(ErroNegocio, "Cadastre-o"):
            self.entrar_veiculo(999)
        self.executar(veiculo_service.alternar_ativo, self.veiculo)
        with self.assertRaisesRegex(ErroNegocio, "veículo está inativo"):
            self.entrar_veiculo()
        self.executar(veiculo_service.alternar_ativo, self.veiculo)
        self.executar(pessoa_service.alternar_ativo, self.morador)
        with self.assertRaisesRegex(ErroNegocio, "proprietário"):
            self.entrar_veiculo()
        self.assertEqual(self.total_registros(), 0)

    def test_descrever(self):
        db = conectar(self.caminho)
        rid = acesso_service.registrar_entrada_veiculo(db, self.veiculo, self.porteiro, "")
        self.assertEqual(acesso_service.descrever(acesso_service.buscar_registro(db, rid)), "ABC-1234 (Gol)")
        db.close()


class TesteTelasPermissoes(BaseAcessos):
    def test_sem_login_redireciona(self):
        resposta = self.app.test_client().get("/acessos/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login", resposta.headers["Location"])

    def test_so_porteiro_e_admin_acessam(self):
        for login, esperado in (("porteiro1", 200), ("admin", 200), ("gerente1", 403), ("func1", 403)):
            with self.subTest(login=login):
                cliente, _ = self.entrar(login)
                self.assertEqual(cliente.get("/acessos/").status_code, esperado)

    def test_aprovador_e_funcionario_nao_registram(self):
        registro_id = self.entrar_pessoa()
        for login in ("gerente1", "func1"):
            cliente, _ = self.entrar(login)
            for url, dados in (("/acessos/entrada/pessoa", {"pessoa_id": self.morador}),
                               ("/acessos/entrada/visitante", {"visitante_id": 1}),
                               ("/acessos/entrada/veiculo", {"veiculo_id": 1}),
                               (f"/acessos/{registro_id}/saida", {})):
                with self.subTest(login=login, url=url):
                    self.assertEqual(self.enviar(cliente, url, dados).status_code, 403)
        self.assertEqual(self.total_registros(), 1)
        self.assertIsNone(self.registro(registro_id)["saida_em"])

    def test_menu_por_perfil(self):
        for login, ve in (("porteiro1", True), ("admin", True), ("gerente1", False), ("func1", False)):
            with self.subTest(login=login):
                cliente, _ = self.entrar(login)
                self.assertEqual('href="/acessos/"' in cliente.get("/").get_data(as_text=True), ve)

    def test_fluxo_de_pessoa_pelas_telas(self):
        cliente, _ = self.entrar("porteiro1")
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Maria da Silva", html)                     # aparece para entrada
        self.assertIn("Ninguém está dentro", html)

        resposta = self.enviar(cliente, "/acessos/entrada/pessoa", {"pessoa_id": self.morador})
        self.assertEqual(resposta.status_code, 302)
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Entrada registrada: Maria da Silva", html)
        self.assertIn("Registrar saída", html)
        self.assertIn(HOJE.strftime("%d/%m/%Y"), html)
        self.assertNotIn("Ninguém está dentro", html)

        resposta = self.enviar(cliente, "/acessos/entrada/pessoa", {"pessoa_id": self.morador})
        self.assertIn("já está dentro", cliente.get("/acessos/").get_data(as_text=True))
        self.assertEqual(self.total_registros(), 1)

        registro_id = self.consultar("SELECT id FROM registro_acesso")[0]["id"]
        self.enviar(cliente, f"/acessos/{registro_id}/saida")
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Saída registrada: Maria da Silva", html)
        self.assertIn("Ninguém está dentro", html)
        self.enviar(cliente, f"/acessos/{registro_id}/saida")
        self.assertIn("já foi registrada", cliente.get("/acessos/").get_data(as_text=True))
        self.assertEqual(self.total_registros(), 1)

    def test_visitante_bloqueado_e_liberado_pelas_telas(self):
        visitante_id, aut_id = self.criar_visitante()
        cliente, _ = self.entrar("porteiro1")
        self.enviar(cliente, "/acessos/entrada/visitante", {"visitante_id": visitante_id})
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Entrada bloqueada", html)
        self.assertEqual(self.total_registros(), 0)

        gerente, _ = self.entrar("gerente1")
        self.enviar(gerente, f"/autorizacoes/{aut_id}", {"acao": "aprovar", "data_inicio": HOJE_TXT})
        self.enviar(cliente, "/acessos/entrada/visitante", {"visitante_id": visitante_id})
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Entrada registrada: Carlos Visitante (visitante)", html)
        self.assertIn("Visita a Maria da Silva", html)
        self.assertEqual(self.total_registros(), 1)

    def test_veiculo_pelas_telas(self):
        veiculo_id = self.criar_veiculo(self.morador)
        cliente, _ = self.entrar("admin")
        self.assertIn("ABC-1234", cliente.get("/acessos/").get_data(as_text=True))
        self.enviar(cliente, "/acessos/entrada/veiculo", {"veiculo_id": veiculo_id, "observacao": "Visita"})
        html = cliente.get("/acessos/").get_data(as_text=True)
        self.assertIn("Entrada registrada: ABC-1234 (Gol)", html)
        self.assertIn("Prata", html)
        self.assertIn("Visita", html)

    def test_dados_invalidos_nao_quebram_a_tela(self):
        cliente, _ = self.entrar("porteiro1")
        for url, campo in (("/acessos/entrada/pessoa", "pessoa_id"),
                           ("/acessos/entrada/visitante", "visitante_id"),
                           ("/acessos/entrada/veiculo", "veiculo_id")):
            for valor in ("", "abc", "999"):
                with self.subTest(url=url, valor=valor):
                    self.assertEqual(self.enviar(cliente, url, {campo: valor}).status_code, 302)
        self.assertEqual(self.enviar(cliente, "/acessos/999/saida").status_code, 302)
        self.assertEqual(self.total_registros(), 0)

    def test_post_sem_token_csrf_e_recusado(self):
        cliente, _ = self.entrar("porteiro1")
        resposta = cliente.post("/acessos/entrada/pessoa", data={"pessoa_id": self.morador})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.total_registros(), 0)

    def test_nao_existe_rota_para_apagar_registros(self):
        registro_id = self.entrar_pessoa()
        cliente, _ = self.entrar("admin")
        for metodo in (cliente.delete, cliente.put):
            self.assertIn(metodo(f"/acessos/{registro_id}").status_code, (404, 405))
        self.assertEqual(self.total_registros(), 1)


if __name__ == "__main__":
    unittest.main()
