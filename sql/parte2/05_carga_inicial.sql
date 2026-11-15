-- Webdriver — Parte 2 · carga inicial. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- 5) CARGA INICIAL (uma linha para cada arquivo que já existe; a tabela foi recriada no 01)
-- ---------------------------------------------------------------------
INSERT INTO ATIVIDADES_RECENTES (id_arquivo, ultima_versao, acesso)  -- parados há mais de 100 dias
SELECT id_arquivo, DATE_FORMAT(data_ultima_modificacao, '%Y-%m-%d'), 'nao prioritario'
FROM ARQUIVO WHERE Passou_100_dias(id_arquivo) = 1;

INSERT INTO ATIVIDADES_RECENTES (id_arquivo, ultima_versao, acesso)  -- mexidos nos últimos 100 dias
SELECT id_arquivo, DATE_FORMAT(data_ultima_modificacao, '%Y-%m-%d'), 'prioritario'
FROM ARQUIVO WHERE Passou_100_dias(id_arquivo) = 0;
