# Changelog

Todas as versões do Sistema de Controle de Portaria e o que mudou em cada uma.
O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e as versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Planejado]

- **0.9.0 — Interface e melhorias:** ajustes visuais, navegação, responsividade, mensagens e correções.
- **1.0.0 — Primeira versão estável:** testes gerais, README e documentação finais, prints, vídeo e PDF.

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
