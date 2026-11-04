-- Dados necessários para o sistema funcionar (perfis de acesso).
INSERT OR IGNORE INTO perfil (nome, descricao) VALUES
    ('administrador', 'Gerencia usuários e tem acesso administrativo a registros, ocorrências e relatórios'),
    ('aprovador',     'Autoriza ou nega a entrada de visitantes'),
    ('porteiro',      'Realiza cadastros, registra entradas e saídas e consulta o histórico'),
    ('funcionario',   'Tem seus dados e veículos cadastrados');
