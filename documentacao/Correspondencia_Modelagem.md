# Correspondência entre a modelagem UML e a implementação

Este documento mostra como as classes do **Diagrama de Classes** foram implementadas no banco de dados
(`sistema/banco/schema.sql`). O diagrama não foi alterado.

## Classes e tabelas

| Classe (diagrama) | Tabela(s) no banco | Observações |
|---|---|---|
| **Pessoa** (id, nome, cpf, telefone, email) | `pessoa` | Acrescenta `endereco_setor` e `tipo` (morador, funcionário ou prestador), exigidos pelo RF-01, e `ativo`. CPF único (RN-06). |
| **Veiculo** (id, placa, modelo, cor) | `veiculo` | Ligado ao proprietário por `pessoa_id` (1 pessoa pode ter 0..* veículos). Placa única (RN-07). |
| **Visitante** (pessoaVisitada, motivoVisita), que "pode ser um" Pessoa | `visitante` | A herança foi implementada com uma tabela própria que repete nome, CPF e telefone. `pessoaVisitada` virou a chave estrangeira `pessoa_visitada_id`. |
| **Acesso** (id, dataHoraEntrada, dataHoraSaida, tipo) | `registro_acesso` | `tipo` indica pessoa, visitante ou veículo. Guarda o porteiro que registrou e a exclusão lógica (`ativo`), para preservar o histórico (RN-08). |
| **Ocorrencia** (id, dataHora, descricao) | `ocorrencia` e `ocorrencia_pessoa` | A tabela de ligação guarda as pessoas envolvidas (RF-09). |
| **Usuario** (id, login, senha, perfil) | `usuario` e `perfil` | A senha é guardada como hash. O atributo `perfil` virou a tabela `perfil`, e as permissões de cada perfil ficam em `sistema/app/permissoes.py`. |

## Métodos do diagrama

Os métodos (`cadastrar()`, `consultar()`, `registrarEntrada()`, `registrarSaida()`, `registrar()`,
`autenticar()`) foram implementados como funções na pasta `sistema/app/services/`, uma por regra de negócio.

## O que a implementação acrescentou

| Elemento | Motivo |
|---|---|
| Tabela `autorizacao` (visitante, status, período, quem decidiu, quando) | O RF-06 e o UC02 pedem que a decisão do aprovador fique registrada e consultável. O diagrama de classes não traz uma classe para isso. |
| Tabela `perfil` | Os perfis e as permissões (RNF-04) precisam existir de forma controlável. |
| Campos `ativo` | Permitem desativar cadastros e excluir registros sem apagá-los, preservando o histórico (RN-08). |
