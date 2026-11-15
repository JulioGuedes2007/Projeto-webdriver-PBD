-- Webdriver — Parte 2 · função. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

DROP FUNCTION IF EXISTS Passou_100_dias;            -- apaga a versão antiga (permite rodar de novo)

-- ---------------------------------------------------------------------
-- 2) FUNÇÃO (aula 12): 1 = verdadeiro, 0 = falso
-- ---------------------------------------------------------------------
DELIMITER $$
CREATE FUNCTION Passou_100_dias(p_id_arquivo INT) RETURNS INT  -- recebe o id do arquivo
READS SQL DATA                                       -- avisa que só lê dados (o MySQL 8 exige)
BEGIN
  DECLARE v_ultima DATETIME;                         -- última alteração do arquivo
  DECLARE v_resultado INT;                           -- resposta: 1 ou 0
  SET v_ultima = (SELECT data_ultima_modificacao     -- busca a data do arquivo
                  FROM ARQUIVO WHERE id_arquivo = p_id_arquivo);
  IF DATEDIFF(CURDATE(), v_ultima) > 100 THEN        -- mais de 100 dias até hoje?
    SET v_resultado = 1;                             -- sim: verdadeiro
  ELSE
    SET v_resultado = 0;                             -- não (ou arquivo não existe): falso
  END IF;
  RETURN v_resultado;                                -- devolve a resposta
END $$
DELIMITER ;
