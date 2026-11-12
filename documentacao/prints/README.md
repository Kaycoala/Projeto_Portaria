# Prints do sistema

Esta pasta recebe as **10 capturas de tela reais** do sistema funcionando. Elas entram no PDF final
(`documentacao/Projeto_Portaria.pdf`). Nunca use imagens montadas ou editadas: tire os prints do
sistema rodando.

## Preparação (uma vez)

No PowerShell, dentro da pasta `sistema`:

```
venv\Scripts\python.exe criar_admin.py        (só se ainda não existir um administrador)
venv\Scripts\python.exe popular_demo.py       (cria dados FICTÍCIOS de demonstração)
venv\Scripts\python.exe run.py
```

Abra http://127.0.0.1:5000. Use o navegador **maximizado, com zoom de 100%** e feche abas pessoais.
No Windows, o atalho **Win + Shift + S** captura uma área da tela; salve como **PNG** nesta pasta
com exatamente os nomes da tabela. Para o painel inicial ficar sem aviso, faça antes um backup:
menu **Backup** > **Fazer backup agora**.

Usuários de demonstração: `porteiro` e `gerente` (senha `demo123`) e o administrador que você criou.

## Lista de prints

| Arquivo | Perfil | O que mostrar |
|---|---|---|
| `01_login.png` | (sem login) | Tela de login em `/login`, com os campos vazios. |
| `02_dashboard.png` | administrador | Página **Início** completa, com os cartões e as últimas movimentações. |
| `03_cadastro_pessoas.png` | porteiro | Menu **Pessoas**, lista com as pessoas cadastradas e o botão *Nova pessoa*. |
| `04_cadastro_veiculos.png` | porteiro | Menu **Veículos**, lista com placa, modelo, cor e proprietário. |
| `05_cadastro_visitantes.png` | porteiro | Menu **Visitantes**, lista com as situações (aguardando, autorizado, negado). |
| `06_autorizacao_visitantes.png` | gerente | Menu **Autorizações** > *Analisar* no visitante Rafael Gomes. Tire o print da tela de decisão, **sem clicar** em Autorizar ou Negar. |
| `07_entrada_saida.png` | porteiro | Menu **Entrada e saída**, com a tabela **Dentro agora** visível. |
| `08_historico_acessos.png` | porteiro | Menu **Histórico**, com um filtro aplicado (por exemplo, nome `Ana`) e os resultados na tela. |
| `09_ocorrencias.png` | porteiro | Menu **Ocorrências**, lista com as ocorrências registradas. |
| `10_relatorios.png` | administrador | Menu **Relatórios**, período *Últimos 7 dias* já gerado, com o resumo e as listas. |

Os arquivos também podem ser `.jpg`, mas mantenha o número e o nome da tabela.

## Conferência

Antes de gerar o PDF, confira se os 10 arquivos existem e se estão legíveis (texto nítido, sem
partes cortadas). O gerador do PDF avisa se algum estiver faltando.
