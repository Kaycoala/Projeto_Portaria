"""Testes do relatório de acessos (V0.8.0).
Execute com: python -m unittest discover tests -v
"""
import unittest
from datetime import date

from app.db import conectar
from app.services import (acesso_service, autorizacao_service, historico_service, ocorrencia_service,
                          relatorio_service)
from app.services.erros import ErroNegocio
from tests.test_historico_ocorrencias import BaseHistorico

HOJE_TXT = date.today().isoformat()


class BaseRelatorio(BaseHistorico):
    def relatorio(self, data_de="2026-01-01", data_ate="2026-01-31"):
        return self.executar(relatorio_service.gerar_relatorio, data_de, data_ate)

    def mudar_saida(self, registro_id, quando):
        db = conectar(self.caminho)
        db.execute("UPDATE registro_acesso SET saida_em=? WHERE id=?", (quando, registro_id))
        db.commit()
        db.close()

    def mudar_ocorrencia(self, ocorrencia_id, quando):
        db = conectar(self.caminho)
        db.execute("UPDATE ocorrencia SET data_hora=? WHERE id=?", (quando, ocorrencia_id))
        db.commit()
        db.close()


class TesteRelatorioServico(BaseRelatorio):
    def test_periodo_sem_movimento(self):
        r = self.relatorio()
        self.assertEqual(r["resumo"]["entradas"], 0)
        self.assertEqual(r["resumo"]["ocorrencias"], 0)
        self.assertEqual(r["acessos"], [])
        self.assertEqual(r["dias"], 31)

    def test_conta_entradas_por_tipo_saidas_e_quem_ficou_sem_saida(self):
        a = self.entrar_pessoa()
        b = self.entrar_visitante()
        c = self.entrar_veiculo()
        self.mudar_entrada(a, "2026-01-10 08:00:00")
        self.mudar_entrada(b, "2026-01-10 09:00:00")
        self.mudar_entrada(c, "2026-01-11 07:00:00")
        self.mudar_saida(a, "2026-01-10 18:00:00")
        resumo = self.relatorio()["resumo"]
        self.assertEqual(resumo["entradas"], 3)
        self.assertEqual(resumo["entradas_por_tipo"], {"pessoa": 1, "visitante": 1, "veiculo": 1})
        self.assertEqual(resumo["saidas"], 1)
        self.assertEqual(resumo["sem_saida"], 2)
        self.assertEqual(resumo["visitantes_distintos"], 1)
        self.assertEqual(resumo["veiculos_distintos"], 1)

    def test_datas_sao_inclusivas_e_fora_do_periodo_nao_entra(self):
        dentro_inicio = self.entrar_pessoa()
        self.executar(acesso_service.registrar_saida, dentro_inicio)
        dentro_fim = self.entrar_pessoa(self.joao)
        self.executar(acesso_service.registrar_saida, dentro_fim)
        fora = self.entrar_pessoa()
        self.mudar_entrada(dentro_inicio, "2026-01-01 00:00:00")
        self.mudar_entrada(dentro_fim, "2026-01-31 23:59:59")
        self.mudar_entrada(fora, "2026-02-01 00:00:00")
        ids = [a["id"] for a in self.relatorio()["acessos"]]
        self.assertEqual(ids, [dentro_inicio, dentro_fim])     # ordem cronológica

    def test_registro_excluido_nao_aparece(self):
        a = self.entrar_pessoa()
        self.mudar_entrada(a, "2026-01-05 10:00:00")
        self.executar(historico_service.excluir_registro, a)
        self.assertEqual(self.relatorio()["resumo"]["entradas"], 0)

    def test_autorizacoes_e_ocorrencias_do_periodo(self):
        _, aut_id = self.criar_visitante()
        self.executar(autorizacao_service.negar, aut_id, self.gerente, "Sem confirmação")
        ocorrencia = self.criar_ocorrencia()
        excluida = self.criar_ocorrencia("Portão travado")
        self.executar(ocorrencia_service.excluir_ocorrencia, excluida)
        r = self.relatorio(HOJE_TXT, HOJE_TXT)
        self.assertEqual(r["resumo"]["autorizacoes"]["negada"], 1)
        self.assertEqual(r["resumo"]["autorizacoes"]["aprovada"], 1)    # a do visitante do setUp
        self.assertEqual([o["id"] for o in r["ocorrencias"]], [ocorrencia])
        self.assertEqual(r["resumo"]["ocorrencias"], 1)

    def test_periodo_invalido(self):
        casos = [(("", "2026-01-31"), "Informe"),
                 (("2026-01-01", ""), "Informe"),
                 (("abc", "2026-01-31"), "inválida"),
                 (("2026-02-01", "2026-01-01"), "depois da data final"),
                 (("2025-01-01", "2026-12-31"), "no máximo")]
        for (de, ate), trecho in casos:
            with self.subTest(de=de, ate=ate):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    self.relatorio(de, ate)

    def test_periodo_padrao_e_do_inicio_do_mes_ate_hoje(self):
        self.assertEqual(relatorio_service.periodo_padrao(date(2026, 3, 17)), ("2026-03-01", "2026-03-17"))

    def test_csv_tem_acessos_ocorrencias_e_bloqueia_formulas(self):
        a = self.entrar_pessoa(obs="=SOMA(A1:A9)")
        self.mudar_entrada(a, "2026-01-10 08:00:00")
        o = self.criar_ocorrencia("Visitante discutiu na portaria")
        self.mudar_ocorrencia(o, "2026-01-12 14:00:00")
        texto = relatorio_service.gerar_csv(self.relatorio())
        self.assertIn("Maria da Silva", texto)
        self.assertIn("Visitante discutiu na portaria", texto)
        self.assertIn("'=SOMA(A1:A9)", texto)
        self.assertNotIn(";=SOMA", texto)


class TesteRelatorioTelas(BaseRelatorio):
    def cliente(self, login):
        return self.entrar(login)[0]

    def test_somente_o_administrador_acessa(self):
        for login, esperado in (("admin", 200), ("porteiro1", 403), ("gerente1", 403), ("func1", 403)):
            with self.subTest(login=login):
                cliente = self.cliente(login)
                self.assertEqual(cliente.get("/relatorios/").status_code, esperado)
                self.assertEqual(cliente.get("/relatorios/csv").status_code, esperado)

    def test_sem_login_vai_para_o_login(self):
        resposta = self.app.test_client().get("/relatorios/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login", resposta.headers["Location"])

    def test_tela_mostra_o_periodo_atual_por_padrao(self):
        self.entrar_pessoa()
        pagina = self.cliente("admin").get("/relatorios/").get_data(as_text=True)
        self.assertIn("Relatório de acessos", pagina)
        self.assertIn("Maria da Silva", pagina)
        self.assertIn("Baixar CSV", pagina)

    def test_periodo_invalido_mostra_mensagem_sem_quebrar(self):
        resposta = self.cliente("admin").get("/relatorios/?data_de=2026-02-01&data_ate=2026-01-01")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("depois da data final", resposta.get_data(as_text=True))
        csv = self.cliente("admin").get("/relatorios/csv?data_de=x&data_ate=y")
        self.assertEqual(csv.status_code, 302)

    def test_download_do_csv(self):
        self.entrar_pessoa()
        resposta = self.cliente("admin").get(f"/relatorios/csv?data_de={HOJE_TXT}&data_ate={HOJE_TXT}")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("text/csv", resposta.headers["Content-Type"])
        self.assertIn(f"relatorio_acessos_{HOJE_TXT}_a_{HOJE_TXT}.csv", resposta.headers["Content-Disposition"])
        self.assertIn("Maria da Silva", resposta.get_data(as_text=True))

    def test_menu_mostra_relatorios_so_para_o_administrador(self):
        inicio = self.cliente("admin").get("/").get_data(as_text=True)
        self.assertIn("/relatorios/", inicio)
        self.assertIn("Gerar relatório", inicio)                 # atalho no dashboard
        for login in ("porteiro1", "gerente1", "func1"):
            with self.subTest(login=login):
                self.assertNotIn("/relatorios/", self.cliente(login).get("/").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
