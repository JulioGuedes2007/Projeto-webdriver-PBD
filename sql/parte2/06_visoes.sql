-- Webdriver — Parte 2 · visões. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

DROP VIEW IF EXISTS vw_meus_arquivos;               -- apaga as versões antigas (permite rodar de novo)
DROP VIEW IF EXISTS vw_historico_operacoes;
DROP VIEW IF EXISTS vw_admin_arquivos;
DROP VIEW IF EXISTS vw_admin_usuarios;
DROP VIEW IF EXISTS vw_empresa_usuarios;
DROP VIEW IF EXISTS vw_empresa_arquivos;

-- ---------------------------------------------------------------------
-- 6) VISÕES (aula 11). Nenhuma mostra ids.
--    USER() devolve quem está conectado, por exemplo 'bruno@localhost'.
--    USER() LIKE CONCAT(login, '@%') = "a conta conectada é este login".
-- ---------------------------------------------------------------------
CREATE VIEW vw_meus_arquivos AS                      -- usuário: arquivos dele + compartilhados com ele
SELECT A.nome, A.tipo, A.permissoes_acesso, A.tamanho_bytes,  -- colunas sem id
       A.data_ultima_modificacao, A.localizacao, A.url
FROM ARQUIVO A
WHERE A.id_dono IN (SELECT U.id_usuario FROM USUARIO U         -- ele é o dono
                    WHERE USER() LIKE CONCAT(U.login, '@%'))
   OR A.id_arquivo IN (SELECT C.id_arquivo                     -- ou recebeu acesso
                       FROM COMPARTILHAMENTO C
                       INNER JOIN USUARIO U ON U.id_usuario = C.id_compartilhado
                       WHERE USER() LIKE CONCAT(U.login, '@%'));

CREATE VIEW vw_historico_operacoes AS                -- usuário: operações dos arquivos que ele acessa
SELECT A.nome AS arquivo, U.login AS feita_por, O.tipo_operacao, O.data, O.hora  -- colunas sem id
FROM OPERACAO O
INNER JOIN ARQUIVO A ON A.id_arquivo = O.id_arquivo  -- nome do arquivo
INNER JOIN USUARIO U ON U.id_usuario = O.id_usuario  -- quem fez
WHERE A.id_dono IN (SELECT U2.id_usuario FROM USUARIO U2       -- arquivo dele
                    WHERE USER() LIKE CONCAT(U2.login, '@%'))
   OR A.id_arquivo IN (SELECT C.id_arquivo                     -- ou compartilhado com ele
                       FROM COMPARTILHAMENTO C
                       INNER JOIN USUARIO U3 ON U3.id_usuario = C.id_compartilhado
                       WHERE USER() LIKE CONCAT(U3.login, '@%'));

CREATE VIEW vw_admin_arquivos AS                     -- admin: todos os arquivos
SELECT A.nome AS arquivo, A.tipo, A.tamanho_bytes, A.permissoes_acesso,
       A.data_ultima_modificacao, U.login AS dono,
       (SELECT I.nome FROM INSTITUICAO I             -- instituição do dono (vazio se não tiver)
        WHERE I.id_instituicao = U.id_instituicao) AS instituicao,
       (SELECT COUNT(*) FROM COMPARTILHAMENTO C      -- com quantos foi compartilhado
        WHERE C.id_arquivo = A.id_arquivo) AS compartilhado_com,
       (SELECT COUNT(*) FROM OPERACAO O              -- quantas operações teve
        WHERE O.id_arquivo = A.id_arquivo) AS operacoes
FROM ARQUIVO A
INNER JOIN USUARIO U ON U.id_usuario = A.id_dono;    -- dono

CREATE VIEW vw_admin_usuarios AS                     -- admin: todos os usuários
SELECT U.login, U.email, U.data_ingresso,
       (SELECT I.nome FROM INSTITUICAO I             -- instituição (vazio se não tiver)
        WHERE I.id_instituicao = U.id_instituicao) AS instituicao,
       (SELECT COUNT(*) FROM ADMINISTRADOR AD        -- 1 = é administrador, 0 = não
        WHERE AD.id_usuario = U.id_usuario) AS administrador,
       (SELECT COUNT(*) FROM ARQUIVO A WHERE A.id_dono = U.id_usuario) AS arquivos  -- quantos arquivos
FROM USUARIO U;

CREATE VIEW vw_empresa_usuarios AS                   -- empresa: funcionários dela
SELECT U.login, U.email, U.data_ingresso, I.nome AS instituicao
FROM USUARIO U
INNER JOIN INSTITUICAO I ON I.id_instituicao = U.id_instituicao
WHERE USER() LIKE CONCAT(LOWER(I.nome), '@%');       -- a conta conectada é a da instituição

CREATE VIEW vw_empresa_arquivos AS                   -- empresa: arquivos dos funcionários
SELECT A.nome AS arquivo, A.tipo, A.tamanho_bytes,
       A.data_ultima_modificacao, U.login AS dono
FROM ARQUIVO A
INNER JOIN USUARIO U ON U.id_usuario = A.id_dono     -- dono do arquivo
INNER JOIN INSTITUICAO I ON I.id_instituicao = U.id_instituicao  -- instituição do dono
WHERE USER() LIKE CONCAT(LOWER(I.nome), '@%');       -- a conta conectada é a da instituição
