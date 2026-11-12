"""Testes do backup do banco de dados (V0.9.0, RNF-05).
Execute com: python -m unittest discover tests -v
"""
import subprocess
import sys
import unittest
from unittest import mock
from datetime import datetime, timedelta
from pathlib import Path

from app.db import conectar
from app.services import backup_service
from app.services.erros import ErroNegocio
from tests.test_autenticacao import BaseTeste

PASTA_SISTEMA = Path(__file__).resolve().parent.parent
AGORA = datetime(2026, 11, 12, 10, 0, 0)


class BaseBackup(BaseTeste):
    def setUp(self):
        super().setUp()
        self.pasta_backup = Path(self.pasta.name) / "backups"

    def fazer(self, agora=AGORA, manter=30):
        return backup_service.fazer_backup(self.caminho, self.pasta_backup, manter, agora)

    def arquivos(self):
        return sorted(p.name for p in self.pasta_backup.iterdir()) if self.pasta_backup.exists() else []


class TesteBackupServico(BaseBackup):
    def test_cria_arquivo_com_nome_padrao(self):
        resultado = self.fazer()
        self.assertEqual(resultado["nome"], "portaria_2026-11-12_10-00-00.db")
        self.assertEqual(self.arquivos(), ["portaria_2026-11-12_10-00-00.db"])

    def test_backup_e_um_banco_valido_com_os_mesmos_dados(self):
        resultado = self.fazer()
        copia = conectar(resultado["caminho"])
        try:
            logins = {r["login"] for r in copia.execute("SELECT login FROM usuario")}
            self.assertEqual(copia.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            copia.close()
        self.assertEqual(logins, {"admin", "porteiro1", "gerente1", "func1"})

    def test_backup_nao_muda_quando_o_banco_muda_depois(self):
        resultado = self.fazer()
        db = conectar(self.caminho)
        db.execute("UPDATE usuario SET ativo = 0 WHERE login = 'func1'")
        db.commit()
        db.close()
        copia = conectar(resultado["caminho"])
        try:
            ativo = copia.execute("SELECT ativo FROM usuario WHERE login = 'func1'").fetchone()[0]
        finally:
            copia.close()
        self.assertEqual(ativo, 1)

    def test_dois_backups_no_mesmo_segundo_nao_se_sobrescrevem(self):
        self.fazer()
        self.fazer()
        self.assertEqual(self.arquivos(), ["portaria_2026-11-12_10-00-00.db", "portaria_2026-11-12_10-00-00_2.db"])

    def test_nao_deixa_arquivo_temporario(self):
        self.fazer()
        self.assertFalse([n for n in self.arquivos() if n.endswith(".tmp")])

    def test_guarda_so_os_mais_recentes_e_nao_mexe_em_outros_arquivos(self):
        self.pasta_backup.mkdir()
        (self.pasta_backup / "anotacoes.txt").write_text("não apague")
        for dia in range(1, 6):
            self.fazer(agora=AGORA.replace(day=dia), manter=3)
        self.assertEqual(self.arquivos(), [
            "anotacoes.txt",
            "portaria_2026-11-03_10-00-00.db", "portaria_2026-11-04_10-00-00.db", "portaria_2026-11-05_10-00-00.db"])

    def test_informa_quantos_antigos_foram_apagados(self):
        self.fazer(agora=AGORA.replace(day=1), manter=1)
        resultado = self.fazer(agora=AGORA.replace(day=2), manter=1)
        self.assertEqual(resultado["removidos"], 1)

    def test_manter_menos_de_um_e_recusado_sem_apagar_nada(self):
        self.fazer()
        with self.assertRaisesRegex(ErroNegocio, "pelo menos 1"):
            self.fazer(manter=0)
        self.assertEqual(len(self.arquivos()), 1)

    def test_banco_inexistente_da_erro_e_nao_cria_nada(self):
        with self.assertRaisesRegex(ErroNegocio, "não foi encontrado"):
            backup_service.fazer_backup(Path(self.pasta.name) / "nao_existe.db", self.pasta_backup)
        self.assertFalse(self.pasta_backup.exists())

    def test_arquivo_que_nao_e_banco_da_erro_e_nao_deixa_backup(self):
        falso = Path(self.pasta.name) / "falso.db"
        falso.write_text("isto não é um banco de dados " * 50)
        with self.assertRaisesRegex(ErroNegocio, "Não foi possível criar o backup"):
            backup_service.fazer_backup(falso, self.pasta_backup, 30, AGORA)
        self.assertEqual(self.arquivos(), [])

    def test_listagem_do_mais_recente_para_o_mais_antigo_ignorando_outros_arquivos(self):
        self.fazer(agora=AGORA.replace(day=1))
        self.fazer(agora=AGORA.replace(day=3))
        self.fazer(agora=AGORA.replace(day=2))
        (self.pasta_backup / "portaria_invalido.db").write_text("x")
        (self.pasta_backup / "portaria_2026-13-45_99-99-99.db").write_text("x")
        lista = backup_service.listar_backups(self.pasta_backup)
        self.assertEqual([b["criado_em"] for b in lista],
                         ["2026-11-03 10:00:00", "2026-11-02 10:00:00", "2026-11-01 10:00:00"])
        self.assertTrue(all(b["tamanho"] > 0 for b in lista))

    def test_listagem_de_pasta_inexistente_e_vazia(self):
        self.assertEqual(backup_service.listar_backups(self.pasta_backup), [])

    def test_situacao_sem_backup_em_dia_e_atrasado(self):
        sem = backup_service.situacao(self.pasta_backup, AGORA)
        self.assertEqual((sem["ultimo"], sem["em_dia"], sem["total"]), (None, False, 0))
        self.fazer()
        em_dia = backup_service.situacao(self.pasta_backup, AGORA + timedelta(hours=23, minutes=59))
        self.assertTrue(em_dia["em_dia"])
        self.assertEqual(em_dia["ultimo"], "2026-11-12 10:00:00")
        atrasado = backup_service.situacao(self.pasta_backup, AGORA + timedelta(hours=24))   # RNF-05
        self.assertFalse(atrasado["em_dia"])

    def test_tamanho_legivel(self):
        self.assertEqual(backup_service.tamanho_legivel(500), "500 bytes")
        self.assertEqual(backup_service.tamanho_legivel(20480), "20 KB")
        self.assertEqual(backup_service.tamanho_legivel(3 * 1024 * 1024), "3,0 MB")


class TesteScriptBackup(BaseBackup):
    def rodar(self, *argumentos):
        return subprocess.run([sys.executable, "backup.py", *argumentos], cwd=PASTA_SISTEMA,
                              capture_output=True, text=True, timeout=60)

    def test_script_cria_backup(self):
        resposta = self.rodar("--banco", str(self.caminho), "--pasta", str(self.pasta_backup))
        self.assertEqual(resposta.returncode, 0, resposta.stderr)
        self.assertIn("Backup criado", resposta.stdout)
        self.assertEqual(len(self.arquivos()), 1)

    def test_script_respeita_o_limite_de_backups(self):
        for _ in range(3):
            self.rodar("--banco", str(self.caminho), "--pasta", str(self.pasta_backup), "--manter", "2")
        self.assertEqual(len(self.arquivos()), 2)

    def test_script_avisa_quando_o_banco_nao_existe(self):
        resposta = self.rodar("--banco", str(Path(self.pasta.name) / "x.db"), "--pasta", str(self.pasta_backup))
        self.assertEqual(resposta.returncode, 1)
        self.assertIn("Erro:", resposta.stdout)


class TesteTelaBackup(BaseBackup):
    def cliente(self, login):
        return self.entrar(login)[0]

    def test_testes_nao_usam_a_pasta_real_de_backups(self):
        self.assertEqual(Path(self.app.config["BACKUP_DIR"]), self.pasta_backup)

    def test_so_o_administrador_acessa(self):
        for login, esperado in (("admin", 200), ("porteiro1", 403), ("gerente1", 403), ("func1", 403)):
            with self.subTest(login=login):
                self.assertEqual(self.cliente(login).get("/backup/").status_code, esperado)
        resposta = self.app.test_client().get("/backup/")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/login", resposta.headers["Location"])

    def test_administrador_faz_backup_pela_tela(self):
        c = self.cliente("admin")
        self.assertIn("Nenhum backup", c.get("/backup/").get_data(as_text=True))
        resposta = self.enviar(c, "/backup/fazer")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(len(self.arquivos()), 1)
        pagina = c.get("/backup/").get_data(as_text=True)
        self.assertIn(self.arquivos()[0], pagina)
        self.assertIn("Em dia", pagina)

    def test_mensagem_de_sucesso_aparece_depois_do_backup(self):
        c = self.cliente("admin")
        pagina = self.enviar(c, "/backup/fazer").headers["Location"]
        corpo = c.get(pagina).get_data(as_text=True)
        self.assertIn("Backup criado com sucesso", corpo)

    def test_outros_perfis_nao_conseguem_fazer_backup(self):
        for login in ("porteiro1", "gerente1", "func1"):
            with self.subTest(login=login):
                self.assertEqual(self.enviar(self.cliente(login), "/backup/fazer").status_code, 403)
        self.assertEqual(self.arquivos(), [])

    def test_backup_sem_token_csrf_e_recusado(self):
        self.assertEqual(self.cliente("admin").post("/backup/fazer").status_code, 400)
        self.assertEqual(self.arquivos(), [])

    def test_erro_ao_fazer_backup_aparece_como_mensagem_amigavel(self):
        c = self.cliente("admin")
        erro = ErroNegocio("O banco de dados não foi encontrado; não há o que copiar.")
        with mock.patch.object(backup_service, "fazer_backup", side_effect=erro):
            resposta = c.post("/backup/fazer", data={"csrf_token": self.token(c)}, follow_redirects=True)
        corpo = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("não foi encontrado", corpo)
        self.assertIn("alert-danger", corpo)

    def test_aviso_no_inicio_so_para_o_administrador_e_some_com_backup_em_dia(self):
        admin = self.cliente("admin")
        self.assertIn("Backup em atraso", admin.get("/").get_data(as_text=True))
        self.assertNotIn("Backup em atraso", self.cliente("porteiro1").get("/").get_data(as_text=True))
        self.enviar(admin, "/backup/fazer")
        self.assertNotIn("Backup em atraso", admin.get("/").get_data(as_text=True))

    def test_aviso_volta_quando_o_backup_fica_velho(self):
        self.fazer(agora=datetime.now() - timedelta(hours=30))
        pagina = self.cliente("admin").get("/").get_data(as_text=True)
        self.assertIn("Backup em atraso", pagina)
        self.assertIn("há mais de 24 horas", pagina)

    def test_menu_mostra_backup_so_para_o_administrador(self):
        self.assertIn('href="/backup/"', self.cliente("admin").get("/").get_data(as_text=True))
        for login in ("porteiro1", "gerente1", "func1"):
            self.assertNotIn('href="/backup/"', self.cliente(login).get("/").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
