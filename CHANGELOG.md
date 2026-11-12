# Changelog

Todas as versões do Sistema de Controle de Portaria e o que mudou em cada uma.
O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.0.0] — Primeira versão estável

### Adicionado
- Script `popular_demo.py`: cria dados **fictícios** (pessoas, veículos, visitantes em várias situações, entradas,
  saídas e ocorrências de vários dias) para tirar os prints e gravar o vídeo. Só roda em banco vazio.
- Roteiro dos prints reais (`documentacao/prints/README.md`) e roteiro do vídeo de 1 minuto (`video/ROTEIRO.md`).
- Gerador do PDF final (`documentacao/gerar_pdf.py`): monta o documento com requisitos, regras, diagramas,
  casos de uso e prints. Ele se recusa a gerar o PDF se faltar algum print ou se a capa não estiver preenchida.
- Documento `documentacao/Correspondencia_Modelagem.md`, que liga cada classe do diagrama às tabelas do banco.
- Testes automatizados do script de demonstração e da correção do CSV (262 testes no total).

### Alterado
- O sistema agora inicia com o modo de desenvolvimento **desligado**: erros inesperados mostram a página amigável,
  e não os detalhes técnicos. Para ligar: `$env:PORTARIA_DEBUG = "1"` antes de rodar `run.py`.
- A pasta `sistema/backups/` foi listada no `.gitignore` (ela contém dados pessoais).
- README, documentação e pastas `diagramas/`, `documentacao/` e `video/` atualizados.

### Corrigido
- O download do relatório em CSV enviava o `charset=utf-8` duas vezes no cabeçalho.
- O README da pasta `diagramas/` falava em arquivos PNG, mas os diagramas são JPG.

### Testes gerais (V1.0.0)
- 262 testes automatizados passando.
- Teste de ponta a ponta pelo servidor: cadastro, visitante pendente bloqueado, autorização, entrada, saída,
  ocorrência, histórico, exclusão lógica, relatório, CSV e backup; todas as telas em cada um dos 4 perfis.
- Desempenho com 30 mil acessos no banco: todas as telas responderam em menos de 1 segundo
  (maior tempo: relatório de 90 dias, cerca de 0,6 s), atendendo o RNF-01 (até 2 segundos).

## [0.9.0] — Interface e melhorias

### Adicionado
- Backup do banco de dados (RNF-05): script `backup.py` e tela **Backup** (somente administrador) com botão
  "Fazer backup agora" e lista dos backups. Cada cópia é conferida antes de ser aceita e são guardados os 30 mais
  recentes. A pasta `sistema/backups/` não vai para o GitHub (tem dados pessoais).
- Aviso no painel inicial do administrador quando o último backup tem mais de 24 horas ou não existe.
- Permissão `gerenciar_backup` (administrador).
- Menu lateral responsivo: em celular e tablet vira uma gaveta aberta pelo botão "Menu"; em telas grandes fica
  fixo ao lado, sem sumir ao rolar a página. A seção atual fica destacada.
- Páginas de erro amigáveis para 405 (ação não permitida) e 500 (erro inesperado), sem detalhes técnicos na tela.
- Mensagens de sucesso somem sozinhas depois de 6 segundos; mensagens de erro ficam até serem fechadas.
- Proteção contra clique duplo nos formulários (evita registrar a mesma entrada duas vezes).
- Testes automatizados de backup, navegação, menu, páginas de erro e qualidade dos templates.

### Corrigido
- O Bootstrap JavaScript não era carregado: o botão de fechar das mensagens não funcionava.
- Campos de observação da tela de entrada e saída sem rótulo para leitores de tela.
- Instruções de execução no Windows: passam a usar `venv\Scripts\python.exe`, que funciona mesmo quando o
  PowerShell bloqueia o `activate`.

## [0.8.0] — Dashboard e relatórios

### Adicionado
- Dashboard na página inicial com números lidos do banco: pessoas por tipo, veículos, visitantes,
  autorizações pendentes, entradas, saídas e ocorrências de hoje e quem está dentro agora.
- Últimas movimentações no dashboard, com link para o histórico completo.
- Atalhos no dashboard conforme o perfil; o perfil Funcionário não vê dados.
- Relatório de acessos por período (RF-10), exclusivo do administrador: resumo, lista de entradas
  e saídas e lista de ocorrências.
- Exportação do relatório em CSV (abre no Excel) e impressão sem o menu lateral.
- Permissão `ver_painel` (administrador, porteiro e aprovador).
- Testes automatizados do dashboard e dos relatórios.
- Arquivo `.gitignore` para não enviar banco de dados, chave da sessão e ambiente virtual.

## [0.7.0] — Histórico e ocorrências

### Adicionado
- Histórico de acessos (RF-08, UC03) com filtros por nome, CPF, placa, período e tipo de acesso.
- Edição da observação e exclusão lógica de registros, somente pelo administrador (RN-05, RN-08).
- Registro de ocorrências com data, horário, descrição e pessoas envolvidas (RF-09, RN-10).

## [0.6.0] — Entrada e saída

### Adicionado
- Registro de entrada e saída de pessoas, visitantes e veículos com data e hora automáticas
  (RF-03, RF-04, RF-07, RN-02, RN-04).
- Bloqueio da entrada de visitante sem autorização válida para o dia (RN-03, UC01).
- Lista de quem está dentro agora.

## [0.5.0] — Visitantes e autorizações

### Adicionado
- Cadastro de visitantes com solicitação de acesso aguardando autorização (RF-05, RN-09).
- Aprovação com período ou negação pelo aprovador, com registro da decisão (RF-06, UC02).

## [0.4.0] — Pessoas e veículos

### Adicionado
- Cadastro, consulta, edição e desativação de pessoas e veículos (RF-01, RF-02).
- Validação de CPF e placa, sem duplicidade (RN-06, RN-07).

## [0.3.0] — Autenticação e usuários

### Adicionado
- Login com senha guardada em hash e proteção dos formulários (RNF-02).
- Gerenciamento de usuários pelo administrador.
- Perfis e permissões centralizados em `app/permissoes.py` (RNF-04).
- Script `criar_admin.py` para o primeiro acesso.

## [0.2.0] — Banco de dados

### Adicionado
- Banco SQLite criado a partir de `banco/schema.sql`, com as tabelas e relacionamentos do sistema.
- Perfis iniciais em `banco/dados_iniciais.sql` e script `criar_banco.py`.

## [0.1.0] — Estrutura inicial

### Adicionado
- Estrutura do repositório, README, requisitos, casos de uso textuais e diagramas UML.
- Estrutura base da aplicação Flask.
