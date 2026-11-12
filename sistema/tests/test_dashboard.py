"""Testes do dashboard (V0.8.0).
Execute com: python -m unittest discover tests -v
"""
import unittest

from app.db import conectar
from app.services import acesso_service, dashboard_service, historico_service, pessoa_service
from tests.test_historico_ocorrencias import BaseHistorico


class BaseDashboard(BaseHistorico):
    def resumo(self):
        return self.executar(dashboard_service.resumo)

    def cliente(self, login):
        return self.entrar(login)[0]

    def mudar(self, sql, parametros):
        db = conectar(self.caminho)
        db.execute(sql, parametros)
        db.commit()
        db.close()


class TesteDashboardServico(BaseDashboard):
    def test_contagens_dos_cadastros(self):
        r = self.resumo()
        self.assertEqual(r["pessoas"], 2)                     # morador + João (setUp)
        self.assertEqual(r["veiculos"], 1)
        self.assertEqual(r["visitantes"], 1)
        self.assertEqual(r["autorizacoes_pendentes"], 0)      # o visitante do setUp já foi aprovado

    def test_pessoa_e_veiculo_inativos_nao_contam(self):
        self.executar(pessoa_service.alternar_ativo, self.joao)
        self.mudar("UPDATE veiculo SET ativo = 0 WHERE id = ?", (self.veiculo,))
        r = self.resumo()
        self.assertEqual(r["pessoas"], 1)
        self.assertEqual(r["veiculos"], 0)

    def test_mesmo_visitante_em_varias_visitas_conta_uma_vez(self):
        self.criar_visitante(motivo="Segunda visita")            # mesmo CPF
        self.criar_visitante(nome="Ana Souza", cpf="111.444.777-35")
        r = self.resumo()
        self.assertEqual(r["visitantes"], 2)
        self.assertEqual(r["autorizacoes_pendentes"], 2)

    def test_movimentacoes_de_hoje_e_quem_esta_dentro(self):
        a = self.entrar_pessoa()
        self.entrar_visitante()
        self.entrar_veiculo()
        self.executar(acesso_service.registrar_saida, a)
        antigo = self.entrar_pessoa(self.joao)
        self.mudar_entrada(antigo, "2020-01-01 08:00:00")
        r = self.resumo()
        self.assertEqual(r["entradas_hoje"], 3)
        self.assertEqual(r["saidas_hoje"], 1)
        self.assertEqual(r["dentro"], {"pessoa": 1, "visitante": 1, "veiculo": 1})   # João (antigo) ainda dentro
        self.assertEqual(r["dentro_total"], 3)

    def test_registro_excluido_nao_conta(self):
        a = self.entrar_pessoa()
        self.executar(historico_service.excluir_registro, a)
        r = self.resumo()
        self.assertEqual(r["entradas_hoje"], 0)
        self.assertEqual(r["dentro_total"], 0)

    def test_ocorrencias_de_hoje(self):
        self.criar_ocorrencia()
        antiga = self.criar_ocorrencia("Ocorrência antiga")
        self.mudar("UPDATE ocorrencia SET data_hora = '2020-01-01 10:00:00' WHERE id = ?", (antiga,))
        self.assertEqual(self.resumo()["ocorrencias_hoje"], 1)

    def test_ultimas_movimentacoes_mais_recentes_primeiro(self):
        ids = [self.entrar_pessoa(), self.entrar_veiculo(), self.entrar_visitante()]
        for i, registro in enumerate(ids):
            self.mudar_entrada(registro, f"2026-01-0{i + 1} 08:00:00")
        ultimas = self.executar(dashboard_service.ultimas_movimentacoes, 2)
        self.assertEqual([r["id"] for r in ultimas], [ids[2], ids[1]])


class TesteDashboardTela(BaseDashboard):
    def test_numeros_da_tela_vem_do_banco(self):
        pagina = self.cliente("porteiro1").get("/").get_data(as_text=True)
        self.assertIn("Ainda não há movimentações registradas", pagina)
        self.entrar_pessoa(self.joao)
        pagina = self.cliente("porteiro1").get("/").get_data(as_text=True)
        self.assertIn("João Pereira", pagina)
        self.assertNotIn("Ainda não há movimentações registradas", pagina)

    def test_cada_perfil_ve_so_o_que_pode_usar(self):
        porteiro = self.cliente("porteiro1").get("/").get_data(as_text=True)
        self.assertIn("Registrar entrada ou saída", porteiro)
        self.assertNotIn("Analisar autorizações", porteiro)
        gerente = self.cliente("gerente1").get("/").get_data(as_text=True)
        self.assertIn("Analisar autorizações", gerente)
        self.assertIn("Últimas movimentações", gerente)
        self.assertNotIn("Registrar entrada ou saída", gerente)

    def test_funcionario_nao_ve_dados(self):
        self.entrar_pessoa()
        pagina = self.cliente("func1").get("/").get_data(as_text=True)
        self.assertIn("não tem operações disponíveis", pagina)
        self.assertNotIn("Maria da Silva", pagina)
        self.assertNotIn("Pessoas cadastradas", pagina)

    def test_pendentes_tem_link_para_o_aprovador(self):
        self.criar_visitante(nome="Ana Souza", cpf="111.444.777-35")
        self.assertIn("1 aguardando autorização", self.cliente("gerente1").get("/").get_data(as_text=True))
        self.assertIn('href="/autorizacoes/"', self.cliente("gerente1").get("/").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
