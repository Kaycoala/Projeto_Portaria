# Roteiro do vídeo de demonstração

Vídeo: [`demonstracao.mp4`](demonstracao.mp4) · formato MP4 · duração de 59,9 s (limite: 1 minuto).

O vídeo mostra o sistema funcionando com o perfil **Administrador**, usando os dados fictícios criados por
`popular_demo.py`. A gravação é só da janela do navegador, em `localhost:5000`, e já começa com o login feito.
Os tempos abaixo são aproximados.

## Passo a passo

| Tempo | Tela | O que aparece | Requisito |
|---|---|---|---|
| 0:00 – 0:10 | **Início** (painel) | Números do banco: 8 pessoas cadastradas, 5 veículos, 5 visitantes (2 aguardando autorização) e 8 movimentações no dia. Lista **Dentro agora** (5 no local: 2 pessoas, 1 visitante e 2 veículos) e últimas movimentações. | RF-10 (painel), RF-04 |
| 0:10 – 0:15 | **Entrada e saída** | Formulários de entrada de pessoa, de visitante e de veículo, e a lista de quem está dentro com o botão *Registrar saída*. O aviso informa que só entra visitante com autorização válida para hoje. | RF-03, RF-04, RF-07, RN-03 |
| 0:15 – 0:23 | **Pessoas** | Lista de moradores, funcionários e prestadores. Busca por CPF. | RF-01 |
| 0:23 – 0:27 | **Veículos** | Lista com placa, modelo, cor e proprietário. | RF-02 |
| 0:27 – 0:31 | **Visitantes** | Visitantes com situações diferentes: negada, aguardando autorização e autorizada. | RF-05, RN-09 |
| 0:31 – 0:39 | **Autorizações** | Duas solicitações pendentes. O visitante é analisado e autorizado; aparece a mensagem *Visitante autorizado. A decisão foi registrada.* e os contadores mudam (pendentes 2 → 1, autorizadas 2 → 3). | RF-06 |
| 0:39 – 0:44 | **Histórico** | Filtros (nome, CPF, placa, período e tipo) e os registros com entrada, saída e porteiro. O administrador vê os botões *Editar* e *Excluir*. | RF-08, RN-05 |
| 0:44 – 0:48 | **Ocorrências** | Ocorrências com data e horário, descrição, pessoas envolvidas e quem registrou. | RF-09, RN-10 |
| 0:48 – 0:52 | **Relatórios** | Resumo do período e a lista de entradas e saídas. | RF-10 |
| 0:52 – 0:55 | **Usuários** | Usuários `admin`, `gerente` e `porteiro`, cada um com seu perfil. | RNF-04 |
| 0:55 – 1:00 | **Entrada e saída** | Entrada de veículo registrada (mensagem de confirmação); o item entra em **Dentro agora**, que passa de 5 para 6. | RF-03, RF-07, RN-02 |

## Como refazer a gravação

1. Rode `popular_demo.py` (só funciona em banco vazio) e depois `run.py`, como descrito em
   [documentacao/prints/README.md](../documentacao/prints/README.md). Entre como `admin`.
2. Grave só a janela do navegador. No Windows: **Win + G** (Xbox Game Bar) > botão de gravar; o arquivo
   sai em MP4 na pasta Vídeos > Capturas.
3. Siga a ordem da tabela acima e ensaie uma vez antes de gravar, para não passar de 1 minuto.
4. O arquivo gravado costuma ficar grande (o primeiro tinha cerca de 38 MB). Para reduzir o tamanho sem
   perder a legibilidade e já cortar em 59 segundos, use o ffmpeg:

```
ffmpeg -i gravacao.mp4 -t 59 -c:v libx264 -crf 22 -preset fast -c:a aac demonstracao.mp4
```

5. Salve o resultado como `video/demonstracao.mp4` e confira que ele tem menos de 1 minuto e menos de 25 MB.
