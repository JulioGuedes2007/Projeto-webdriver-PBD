-- Webdriver — Parte 1 · e) remover. Rodar na ordem: 01 a 05. Explicações no README.md

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- e) REMOVER
-- ---------------------------------------------------------------------
DELETE FROM COMPARTILHAMENTO WHERE id_arquivo = 2 AND id_compartilhado = 3;  -- e1) diego perde o acesso ao arquivo 2

-- e2) apaga o arquivo 4. Antes, apaga o que aponta para ele (senão a FK não deixa).
--     Tudo numa transação: ou apaga tudo, ou nada (aula 12).
START TRANSACTION;                                   -- começa a transação
DELETE FROM OPERACAO         WHERE id_arquivo = 4;   -- operações do arquivo
DELETE FROM COMENTARIO       WHERE id_arquivo = 4;   -- comentários do arquivo
DELETE FROM COMPARTILHAMENTO WHERE id_arquivo = 4;   -- acessos do arquivo
DELETE FROM HISTORICO_VERSAO WHERE id_arquivo = 4;   -- versões do arquivo
UPDATE SUPORTE SET id_arquivo = NULL WHERE id_arquivo = 4;  -- o pedido de suporte continua, sem arquivo
DELETE FROM ARQUIVO          WHERE id_arquivo = 4;   -- por fim, o arquivo
COMMIT;                                              -- grava tudo

SELECT 'arquivos' AS tabela, COUNT(*) AS linhas FROM ARQUIVO   -- conferência: esperado 3
UNION SELECT 'suportes', COUNT(*) FROM SUPORTE             -- esperado 2
UNION SELECT 'historicos', COUNT(*) FROM HISTORICO_VERSAO; -- esperado 5
