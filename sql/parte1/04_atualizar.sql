-- Webdriver — Parte 1 · d) atualizar. Rodar na ordem: 01 a 05. Explicações no README.md

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- d) ATUALIZAR
-- ---------------------------------------------------------------------
UPDATE ARQUIVO                                                       -- d1) renomeia o arquivo 1
SET nome = 'trabalho_bd_final.pdf', data_ultima_modificacao = '2026-10-28 18:00:00'  -- novo nome e data
WHERE id_arquivo = 1;                                                -- só o arquivo 1

INSERT INTO OPERACAO (tipo_operacao, data, hora, id_usuario, id_arquivo)              -- d2) registra a operação
VALUES ('atualizar', '2026-10-28', '18:00:00', 1, 1);                                 -- bruno atualizou o 1
INSERT INTO HISTORICO_VERSAO (data, hora, operacao, conteudo_mudado, id_usuario, id_arquivo)  -- e a nova versão
VALUES ('2026-10-28', '18:00:00', 'atualizar', 'Arquivo renomeado para trabalho_bd_final.pdf', 1, 1);  -- o que mudou

UPDATE USUARIO SET email = 'bruno.novo@email.com' WHERE login = 'bruno';  -- d3) troca o e-mail do bruno
