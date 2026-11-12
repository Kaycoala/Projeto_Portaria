# Código-fonte — Sistema de Controle de Portaria

## Como executar (Windows)

Requisito: Python 3.10 ou superior.

```
cd sistema
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe criar_admin.py
venv\Scripts\python.exe run.py
```

Abra http://127.0.0.1:5000 no navegador. (Usamos `venv\Scripts\python.exe` direto, sem `activate`,
porque o PowerShell costuma bloquear o `activate`.)

## Estrutura

- `app/routes/`: telas e ações de cada módulo
- `app/services/`: regras de negócio e validações
- `app/templates/`: páginas HTML
- `app/static/`: CSS e JavaScript
- `run.py`: inicia o sistema
- `backup.py`: cria uma cópia de segurança do banco
- `popular_demo.py`: cria dados fictícios para demonstração (veja abaixo)

## Banco de dados

O banco é um arquivo SQLite (`instance/portaria.db`), criado a partir de `banco/schema.sql`.
Na primeira execução do sistema ele é criado automaticamente. Também é possível criar manualmente:

```
venv\Scripts\python.exe criar_banco.py             (cria, sem apagar dados)
venv\Scripts\python.exe criar_banco.py --recriar   (APAGA tudo e cria de novo)
```

Tabelas: `perfil`, `pessoa`, `usuario`, `veiculo`, `visitante`, `autorizacao`,
`registro_acesso`, `ocorrencia`, `ocorrencia_pessoa`.

## Testes

```
venv\Scripts\python.exe -m unittest discover tests -v
```

## Primeiro acesso (login)

O sistema exige login. Antes de entrar pela primeira vez, crie o administrador:

```
venv\Scripts\python.exe criar_admin.py
```

O script pergunta o login e a senha (mínimo de 6 caracteres). Depois rode
`venv\Scripts\python.exe run.py` e entre em http://127.0.0.1:5000.

O administrador cadastra os demais usuários no menu **Usuários**.

## Painel inicial (dashboard)

Depois do login, a página **Início** mostra os números atuais, lidos do banco de dados:

- Pessoas cadastradas (por tipo), veículos, visitantes e autorizações aguardando decisão.
- Movimentações de hoje (entradas, saídas e ocorrências) e quem está **dentro agora**.
- As últimas movimentações, com link para o histórico completo.
- Botões de atalho conforme o perfil. O perfil **Funcionário** não vê dados.

Cadastros desativados e registros excluídos não entram nas contagens.

## Cadastro de pessoas e veículos

No menu lateral, **Pessoas** e **Veículos** (administrador e porteiro):

- Cadastre primeiro a pessoa e depois o veículo, escolhendo o proprietário.
- O CPF e a placa não podem se repetir. O CPF pode ser digitado com ou sem pontos e traço;
  a placa aceita `ABC-1234` e `ABC1D23` (maiúsculas ou minúsculas).
- Use a caixa de busca para achar pessoas (nome ou CPF) e veículos (placa, modelo ou proprietário).
- Cadastros não são apagados: use **Desativar**, para que o histórico de acessos seja preservado.

## Visitantes e autorizações

- **Porteiro:** menu **Visitantes** > *Novo visitante*. A solicitação fica "aguardando autorização".
- **Aprovador (gerente):** menu **Autorizações** > *Analisar*. Escolha **Autorizar** (com a data inicial
  e, se quiser, a data final) ou **Negar**. A decisão fica registrada e não pode ser desfeita.
- Se o visitante voltar outro dia, o porteiro usa **Nova solicitação** na lista de visitantes.
- A autorização é conferida na hora da entrada (veja a seção abaixo).

## Entrada e saída

No menu **Entrada e saída** (porteiro e administrador):

- Escolha a pessoa, o visitante ou o veículo e clique em **Registrar entrada**. A data e a hora são gravadas automaticamente.
- **Visitante:** só entra com autorização válida para hoje. Se estiver aguardando, negada, ainda sem data
  de início ou vencida, o sistema bloqueia e explica o motivo.
- Quem já está dentro aparece na tabela **Dentro agora**; use **Registrar saída** quando sair.
- Os registros nunca são apagados, a saída só completa o horário.

## Histórico de acessos

No menu **Histórico** (administrador, porteiro e aprovador):

- Preencha um ou mais filtros (nome, CPF, placa, data inicial e final, tipo de acesso) e clique em **Pesquisar**. Sem filtros, aparecem os registros mais recentes (no máximo 200).
- O nome também encontra o proprietário de um veículo. A consulta não altera nada.
- **Só o administrador** vê os botões **Editar** (corrige a observação) e **Excluir**. A exclusão é lógica: o registro continua guardado e o administrador o enxerga marcado como "Excluído".

## Ocorrências

No menu **Ocorrências** (administrador e porteiro):

- Clique em **Nova ocorrência**, confira a data e o horário (já vêm preenchidos), escreva a descrição e marque as pessoas envolvidas, se houver.
- Use o filtro de datas para ver as ocorrências de um período.
- Só o administrador edita ou exclui ocorrências (exclusão lógica).

## Relatórios

No menu **Relatórios** (somente administrador):

- Escolha a data inicial e a final (ou use **Últimos 7 dias** / **Últimos 30 dias**) e clique em **Gerar relatório**.
  Ao abrir a tela, o período vem preenchido do primeiro dia do mês até hoje.
- O resumo mostra entradas por tipo, saídas, entradas ainda sem saída, visitantes e veículos diferentes,
  autorizações (autorizadas, negadas e pendentes) e ocorrências do período.
- Logo abaixo aparecem a lista de entradas e saídas e a lista de ocorrências.
- **Baixar CSV** gera um arquivo que abre direto no Excel; **Imprimir** imprime só o relatório (sem o menu).
- Registros e ocorrências excluídos não entram no relatório. O período máximo é de 366 dias.

## Backup (RNF-05)

O banco de dados é o arquivo `instance/portaria.db`. Os backups ficam na pasta `backups/` (ela não vai para o GitHub,
porque tem dados pessoais).

**Fazer um backup agora**
- Pelo sistema: menu **Backup** (somente administrador) > **Fazer backup agora**.
- Pelo terminal, dentro de `sistema`: `venv\Scripts\python.exe backup.py` (use `--manter 60` para guardar mais cópias;
  o padrão é guardar as 30 mais recentes).

**Todo dia, automaticamente (Windows)** — Agendador de Tarefas > *Criar Tarefa Básica* > *Diariamente* > *Iniciar um programa*:
- Programa: o caminho completo de `sistema\venv\Scripts\python.exe`
- Argumentos: o caminho completo de `sistema\backup.py`
- Iniciar em: o caminho da pasta `sistema`

Se o computador estiver desligado no horário, a tarefa pode ser configurada para rodar assim que ele ligar.
Enquanto não houver backup das últimas 24 horas, o painel inicial do administrador mostra um aviso.

**Guarde uma cópia fora do computador:** copie a pasta `backups` para um pendrive ou serviço de nuvem de confiança.
Uma cópia só no mesmo computador não protege contra defeito no disco.

**Restaurar um backup**
1. Feche o sistema (`Ctrl+C` no terminal onde ele está rodando).
2. Guarde uma cópia do `instance/portaria.db` atual em outro lugar, por segurança.
3. Copie o backup escolhido para a pasta `instance/` e renomeie-o para `portaria.db`.
4. Abra o sistema de novo.

## Perfis e permissões

| Perfil | O que pode fazer |
|---|---|
| Administrador | Tudo: usuários, cadastros, acessos, autorizações, ocorrências, relatórios, backup |
| Porteiro | Cadastros, visitantes, entradas e saídas, histórico e ocorrências |
| Aprovador (Gerente) | Autorizar/negar visitantes e consultar o histórico |
| Funcionário | Apenas entra no sistema (sem operações) |

As regras ficam em `app/permissoes.py`.

## Dados de demonstração

Para mostrar o sistema com dados (apresentação, prints e vídeo), rode dentro de `sistema`, depois de criar o administrador:

```
venv\Scripts\python.exe popular_demo.py
```

Ele cria **dados fictícios**: os usuários `porteiro` e `gerente` (senha `demo123`), 8 pessoas, 5 veículos,
5 visitantes (aguardando, autorizados e negado), entradas e saídas dos últimos dias e 2 ocorrências.
Por segurança, o script **não roda** se o banco já tiver pessoas cadastradas. Para recomeçar do zero em um banco
de testes, use `criar_banco.py --recriar` e depois `criar_admin.py`.

## Modo de desenvolvimento

Por padrão o sistema roda com o modo de desenvolvimento desligado: se algo der errado, o usuário vê uma página de
erro simples. Quem estiver alterando o código pode ligar o recarregamento automático e os detalhes técnicos dos erros:

```
$env:PORTARIA_DEBUG = "1"
venv\Scripts\python.exe run.py
```
