-- Webdriver — Parte 2 · procedures. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

DROP PROCEDURE IF EXISTS Verificar_atividades;      -- apaga as versões antigas (permite rodar de novo)
DROP PROCEDURE IF EXISTS Conta_usuarios;
DROP PROCEDURE IF EXISTS Chavear;
DROP PROCEDURE IF EXISTS Remover_acessos;

-- ---------------------------------------------------------------------
-- 3) PROCEDURES (aula 12)
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE Verificar_atividades()              -- recalcula a tabela com a data de hoje
BEGIN
  INSERT INTO ATIVIDADES_RECENTES (id_arquivo, ultima_versao, acesso)  -- cria as linhas que faltam
  SELECT id_arquivo, DATE_FORMAT(data_ultima_modificacao, '%Y-%m-%d'), 'prioritario'  -- só o dia (aula 12)
  FROM ARQUIVO                                       -- de todos os arquivos
  WHERE id_arquivo NOT IN (SELECT id_arquivo FROM ATIVIDADES_RECENTES);  -- que ainda não estão na tabela

  UPDATE ATIVIDADES_RECENTES                         -- atualiza a data de todas as linhas
  SET ultima_versao = (SELECT DATE_FORMAT(A.data_ultima_modificacao, '%Y-%m-%d')  -- subconsulta: dia do arquivo
                       FROM ARQUIVO A
                       WHERE A.id_arquivo = ATIVIDADES_RECENTES.id_arquivo)
  WHERE id_arquivo > 0;                              -- todas as linhas (filtro pela chave: exigido pelo Workbench)

  UPDATE ATIVIDADES_RECENTES SET acesso = 'nao prioritario'  -- mais de 100 dias parado
  WHERE id_arquivo > 0 AND Passou_100_dias(id_arquivo) = 1;  -- usa a função
  UPDATE ATIVIDADES_RECENTES SET acesso = 'prioritario'      -- mexido nos últimos 100 dias
  WHERE id_arquivo > 0 AND Passou_100_dias(id_arquivo) = 0;

  SELECT A.nome AS arquivo, R.ultima_versao, R.acesso  -- mostra o resultado
  FROM ATIVIDADES_RECENTES R
  INNER JOIN ARQUIVO A ON A.id_arquivo = R.id_arquivo
  ORDER BY A.nome;
END $$

CREATE PROCEDURE Conta_usuarios(IN p_id_arquivo INT) -- quantos usuários diferentes têm o arquivo
BEGIN
  SELECT COUNT(*) AS total_usuarios                  -- conta as linhas abaixo
  FROM (
    SELECT id_dono AS id_usuario FROM ARQUIVO        -- o dono
    WHERE id_arquivo = p_id_arquivo
    UNION                                            -- junta sem repetir (aula 11)
    SELECT id_compartilhado FROM COMPARTILHAMENTO    -- quem recebeu acesso
    WHERE id_arquivo = p_id_arquivo
  ) AS usuarios;
END $$

CREATE PROCEDURE Chavear(IN p_id_arquivo INT)        -- troca prioritário <-> não prioritário
BEGIN
  DECLARE v_acesso VARCHAR(20);                      -- valor atual
  SET v_acesso = (SELECT acesso FROM ATIVIDADES_RECENTES WHERE id_arquivo = p_id_arquivo);

  IF v_acesso IS NULL THEN                           -- arquivo não está na tabela
    SELECT 'Arquivo não encontrado em atividades_recentes' AS aviso;
  ELSE
    IF v_acesso = 'prioritario' THEN                 -- inverte o valor
      UPDATE ATIVIDADES_RECENTES SET acesso = 'nao prioritario' WHERE id_arquivo = p_id_arquivo;
    ELSE
      UPDATE ATIVIDADES_RECENTES SET acesso = 'prioritario' WHERE id_arquivo = p_id_arquivo;
    END IF;
    SELECT A.nome AS arquivo, R.acesso               -- mostra como ficou
    FROM ATIVIDADES_RECENTES R
    INNER JOIN ARQUIVO A ON A.id_arquivo = R.id_arquivo
    WHERE R.id_arquivo = p_id_arquivo;
  END IF;
END $$

CREATE PROCEDURE Remover_acessos(IN p_id_arquivo INT)  -- tira o acesso de todos, menos do dono
BEGIN
  DECLARE v_removidos INT DEFAULT 0;                 -- contador

  DELETE FROM COMPARTILHAMENTO                       -- apaga os acessos do arquivo
  WHERE id_arquivo = p_id_arquivo
    AND id_compartilhado <> id_dono;                 -- nunca o do dono
  SET v_removidos = ROW_COUNT();                     -- quantos foram apagados (aula 13)

  UPDATE ARQUIVO SET permissoes_acesso = 'privado'   -- o arquivo volta a ser privado
  WHERE id_arquivo = p_id_arquivo;

  SELECT v_removidos AS acessos_removidos;           -- mostra o total
END $$

DELIMITER ;
