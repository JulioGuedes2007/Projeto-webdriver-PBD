-- Webdriver — Parte 2 · triggers. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

DROP TRIGGER IF EXISTS Definir_dono;                -- apaga as versões antigas (permite rodar de novo)
DROP TRIGGER IF EXISTS Safe_security;
DROP TRIGGER IF EXISTS Limite_espaco;
DROP TRIGGER IF EXISTS Limite_espaco_update;
DROP TRIGGER IF EXISTS Registrar_operacao;
DROP TRIGGER IF EXISTS Atualizar_acesso;

-- ---------------------------------------------------------------------
-- 4) TRIGGERS (aula 13)
--    No ARQUIVO há 3 "antes de inserir". O MySQL roda na ordem em que foram criados:
--    Definir_dono -> Safe_security -> Limite_espaco
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER Definir_dono BEFORE INSERT ON ARQUIVO  -- antes de gravar um arquivo novo
FOR EACH ROW                                         -- para cada linha
BEGIN
  IF NEW.id_dono IS NULL OR NEW.id_dono = 0 THEN     -- veio sem dono (inserido pela visão)
    SET NEW.id_dono = (SELECT id_usuario FROM USUARIO  -- dono = quem está logado
                       WHERE USER() LIKE CONCAT(login, '@%'));  -- USER() = 'login@computador'
  END IF;
  IF NEW.data_ultima_modificacao IS NULL THEN        -- veio sem data (igual ao exemplo da aula 13)
    SET NEW.data_ultima_modificacao = NOW();         -- usa agora
  END IF;
END $$

CREATE TRIGGER Safe_security BEFORE INSERT ON ARQUIVO  -- antes de gravar um arquivo novo
FOR EACH ROW
BEGIN
  IF LOWER(NEW.tipo) IN ('exe', 'bat', 'cmd', 'com', 'msi', 'sh',   -- o tipo é executável
                         'bin', 'apk', 'jar', 'ps1', 'vbs', 'scr')
     OR LOWER(NEW.nome) LIKE '%.exe' OR LOWER(NEW.nome) LIKE '%.bat'  -- ou o nome termina
     OR LOWER(NEW.nome) LIKE '%.cmd' OR LOWER(NEW.nome) LIKE '%.com'  -- com uma extensão
     OR LOWER(NEW.nome) LIKE '%.msi' OR LOWER(NEW.nome) LIKE '%.sh'   -- de executável
     OR LOWER(NEW.nome) LIKE '%.bin' OR LOWER(NEW.nome) LIKE '%.apk'
     OR LOWER(NEW.nome) LIKE '%.jar' OR LOWER(NEW.nome) LIKE '%.ps1'
     OR LOWER(NEW.nome) LIKE '%.vbs' OR LOWER(NEW.nome) LIKE '%.scr' THEN
    SIGNAL SQLSTATE '45000'                          -- cancela o INSERT com uma mensagem de erro
      SET MESSAGE_TEXT = 'Safe_security: arquivos executáveis não podem ser inseridos no drive';
  END IF;
END $$

CREATE TRIGGER Limite_espaco BEFORE INSERT ON ARQUIVO  -- antes de gravar um arquivo novo
FOR EACH ROW
BEGIN
  DECLARE v_limite_gb DECIMAL(10,2);                 -- limite do plano (GB)
  DECLARE v_usado DECIMAL(20,0);                     -- quanto o dono já usa (bytes)

  SET v_limite_gb = (SELECT P.espaco_por_usuario_gb  -- busca o limite do plano do dono
                     FROM USUARIO U
                     INNER JOIN INSTITUICAO I ON I.id_instituicao = U.id_instituicao
                     INNER JOIN PLANO P ON P.id_plano = I.id_plano
                     WHERE U.id_usuario = NEW.id_dono);

  IF v_limite_gb IS NOT NULL THEN                    -- sem plano = sem limite
    SET v_usado = (SELECT SUM(tamanho_bytes)         -- soma os arquivos dele
                   FROM ARQUIVO WHERE id_dono = NEW.id_dono);
    IF v_usado IS NULL THEN                          -- ainda não tem arquivos
      SET v_usado = 0;
    END IF;
    IF v_usado + NEW.tamanho_bytes > v_limite_gb * 1024 * 1024 * 1024 THEN  -- passou do limite?
      SIGNAL SQLSTATE '45000'                        -- cancela o INSERT com uma mensagem de erro
        SET MESSAGE_TEXT = 'Limite_espaco: o arquivo passa do espaço por usuário do plano';
    END IF;
  END IF;
END $$

CREATE TRIGGER Limite_espaco_update BEFORE UPDATE ON ARQUIVO  -- antes de alterar um arquivo
FOR EACH ROW
BEGIN
  DECLARE v_limite_gb DECIMAL(10,2);                 -- limite do plano (GB)
  DECLARE v_usado DECIMAL(20,0);                     -- uso dos outros arquivos (bytes)

  SET v_limite_gb = (SELECT P.espaco_por_usuario_gb  -- limite do plano do dono
                     FROM USUARIO U
                     INNER JOIN INSTITUICAO I ON I.id_instituicao = U.id_instituicao
                     INNER JOIN PLANO P ON P.id_plano = I.id_plano
                     WHERE U.id_usuario = NEW.id_dono);
  IF v_limite_gb IS NOT NULL THEN                    -- sem plano = sem limite
    SET v_usado = (SELECT SUM(tamanho_bytes)         -- soma os outros arquivos dele
                   FROM ARQUIVO
                   WHERE id_dono = NEW.id_dono AND id_arquivo <> NEW.id_arquivo);
    IF v_usado IS NULL THEN                          -- não tem outros arquivos
      SET v_usado = 0;
    END IF;
    IF v_usado + NEW.tamanho_bytes > v_limite_gb * 1024 * 1024 * 1024 THEN  -- passou?
      SIGNAL SQLSTATE '45000'                        -- cancela o UPDATE com uma mensagem de erro
        SET MESSAGE_TEXT = 'Limite_espaco: o arquivo passa do espaço por usuário do plano';
    END IF;
  END IF;
END $$

CREATE TRIGGER Registrar_operacao AFTER INSERT ON OPERACAO  -- depois de gravar uma operação
FOR EACH ROW
BEGIN
  IF (SELECT COUNT(*) FROM ATIVIDADES_RECENTES WHERE id_arquivo = NEW.id_arquivo) = 0 THEN
    INSERT INTO ATIVIDADES_RECENTES (id_arquivo, ultima_versao, acesso)  -- arquivo novo: cria a linha
    VALUES (NEW.id_arquivo, NEW.data, 'prioritario');
  ELSE
    UPDATE ATIVIDADES_RECENTES                       -- já existe: atualiza a data
    SET ultima_versao = NEW.data, acesso = 'prioritario'  -- e volta a prioritário
    WHERE id_arquivo = NEW.id_arquivo;
  END IF;
END $$

CREATE TRIGGER Atualizar_acesso AFTER INSERT ON COMPARTILHAMENTO  -- depois de alguém ganhar acesso
FOR EACH ROW
BEGIN
  UPDATE ARQUIVO SET permissoes_acesso = 'compartilhado'  -- o arquivo passa a compartilhado
  WHERE id_arquivo = NEW.id_arquivo;
END $$

DELIMITER ;
