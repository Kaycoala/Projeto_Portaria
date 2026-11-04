-- Sistema de Controle de Portaria: criação das tabelas (SQLite)
-- Pode ser executado várias vezes sem apagar dados (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS perfil (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL UNIQUE,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS pessoa (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT NOT NULL,
    cpf            TEXT NOT NULL UNIQUE,              -- RN-06
    telefone       TEXT,
    email          TEXT,
    endereco_setor TEXT,
    tipo           TEXT NOT NULL
                   CHECK (tipo IN ('morador', 'funcionario', 'prestador')),
    ativo          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS usuario (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    login      TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil_id  INTEGER NOT NULL REFERENCES perfil(id),
    pessoa_id  INTEGER REFERENCES pessoa(id),         -- opcional
    ativo      INTEGER NOT NULL DEFAULT 1,
    criado_em  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS veiculo (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    placa     TEXT NOT NULL UNIQUE,                   -- RN-07
    modelo    TEXT NOT NULL,
    cor       TEXT NOT NULL,
    pessoa_id INTEGER NOT NULL REFERENCES pessoa(id), -- proprietário
    ativo     INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS visitante (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT NOT NULL,
    cpf               TEXT NOT NULL,
    telefone          TEXT,
    pessoa_visitada_id INTEGER NOT NULL REFERENCES pessoa(id),
    motivo            TEXT NOT NULL,
    criado_em         TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS autorizacao (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    visitante_id  INTEGER NOT NULL REFERENCES visitante(id),
    status        TEXT NOT NULL DEFAULT 'pendente'
                  CHECK (status IN ('pendente', 'aprovada', 'negada')),
    data_inicio   TEXT,                               -- período permitido
    data_fim      TEXT,
    aprovador_id  INTEGER REFERENCES usuario(id),     -- quem decidiu
    decidido_em   TEXT,
    observacao    TEXT,
    solicitado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS registro_acesso (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo         TEXT NOT NULL
                 CHECK (tipo IN ('pessoa', 'visitante', 'veiculo')),
    pessoa_id    INTEGER REFERENCES pessoa(id),       -- pessoa ou responsável pelo veículo
    visitante_id INTEGER REFERENCES visitante(id),
    veiculo_id   INTEGER REFERENCES veiculo(id),
    entrada_em   TEXT NOT NULL,                       -- RN-02
    saida_em     TEXT,                                -- RN-04
    porteiro_id  INTEGER NOT NULL REFERENCES usuario(id),
    observacao   TEXT,
    ativo        INTEGER NOT NULL DEFAULT 1,          -- RN-08: nunca apagar de verdade
    CHECK (
        (tipo = 'pessoa'    AND pessoa_id    IS NOT NULL) OR
        (tipo = 'visitante' AND visitante_id IS NOT NULL) OR
        (tipo = 'veiculo'   AND veiculo_id   IS NOT NULL)
    ),
    CHECK (saida_em IS NULL OR saida_em >= entrada_em)
);

CREATE TABLE IF NOT EXISTS ocorrencia (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora        TEXT NOT NULL,                   -- RN-10
    descricao        TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
    registrado_por_id INTEGER NOT NULL REFERENCES usuario(id),
    ativo            INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ocorrencia_pessoa (
    ocorrencia_id INTEGER NOT NULL REFERENCES ocorrencia(id),
    pessoa_id     INTEGER NOT NULL REFERENCES pessoa(id),
    PRIMARY KEY (ocorrencia_id, pessoa_id)
);

CREATE INDEX IF NOT EXISTS idx_acesso_entrada ON registro_acesso(entrada_em);
CREATE INDEX IF NOT EXISTS idx_acesso_pessoa  ON registro_acesso(pessoa_id);
CREATE INDEX IF NOT EXISTS idx_acesso_veiculo ON registro_acesso(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_autorizacao_status ON autorizacao(status);
