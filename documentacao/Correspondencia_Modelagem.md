# Correspondência entre a modelagem UML e a implementação

Este documento mostra como as classes do **Diagrama de Classes** (versão revisada, em `diagramas/`) foram
implementadas no banco de dados (`sistema/banco/schema.sql`) e nos serviços (`sistema/app/services/`).

## Classes e tabelas

| Classe (diagrama) | Tabela(s) no banco | Serviço | Observações |
|---|---|---|---|
| **Perfil** | `perfil` | `usuario_service` | 4 perfis iniciais. As permissões de cada perfil ficam em `sistema/app/permissoes.py`. |
| **Usuario** | `usuario` | `usuario_service` | Login único; senha guardada como hash; ligado a um `perfil` e, opcionalmente, a uma pessoa. Não permite desativar o último administrador. |
| **Pessoa** | `pessoa` | `pessoa_service` | `tipo` (morador, funcionário ou prestador), `endereco_setor` e `ativo`. CPF único (RN-06). |
| **Veiculo** | `veiculo` | `veiculo_service` | Ligado ao proprietário por `pessoa_id` (1 pessoa pode ter 0..* veículos). Placa única (RN-07). |
| **Visitante** | `visitante` | `visitante_service` | Tabela independente, com nome, CPF e telefone próprios (não herda de Pessoa). `pessoa_visitada_id` é chave estrangeira obrigatória para `pessoa`. |
| **Autorizacao** | `autorizacao` | `autorizacao_service` | Status (pendente, aprovada ou negada), período, quem decidiu e quando (RF-06, RN-09). |
| **RegistroAcesso** | `registro_acesso` | `acesso_service`, `historico_service` | `tipo` indica pessoa, visitante ou veículo; uma restrição `CHECK` exige o vínculo correspondente. Guarda o porteiro que registrou e a exclusão lógica (`ativo`, RN-08). A saída não pode ser anterior à entrada. |
| **Ocorrencia** | `ocorrencia` e `ocorrencia_pessoa` | `ocorrencia_service` | A tabela de ligação guarda as pessoas envolvidas (RF-09). Exclusão lógica. |

## Métodos do diagrama

O código não usa classes de domínio com métodos. As operações desenhadas no diagrama (`cadastrar()`, `consultar()`,
`registrarEntrada()`, `registrarSaida()`, `aprovar()`, `negar()`, `autenticar()` e outras) representam a responsabilidade
lógica de cada entidade e foram implementadas como funções na pasta `sistema/app/services/`, uma por assunto.

## Diferenças em relação ao primeiro diagrama de classes

| Primeiro diagrama | Sistema implementado |
|---|---|
| Visitante "pode ser um" Pessoa (herança). | Visitante é uma tabela independente; liga-se a uma Pessoa apenas como pessoa visitada. |
| `pessoaVisitada` era um texto. | Virou a chave estrangeira `pessoa_visitada_id`. |
| Acesso se relacionava só com Pessoa. | O registro de acesso se relaciona com Pessoa, Visitante ou Veículo, conforme o tipo, e com o Usuário que registrou. |
| Acesso "pode registrar" Ocorrência. | A ocorrência liga-se ao usuário que a registrou e, por associação N:N, às pessoas envolvidas. |
| Não havia classe para a decisão de autorização. | Existe `Autorizacao`, indispensável para RF-06 e RN-09. |
| `Usuario` tinha o atributo `perfil`. | `Perfil` é uma classe e uma tabela próprias. |
| Sem atributos de situação. | `ativo` em Pessoa, Veiculo, Usuario, RegistroAcesso e Ocorrencia permite desativar ou excluir logicamente sem perder dados (RN-08). |
