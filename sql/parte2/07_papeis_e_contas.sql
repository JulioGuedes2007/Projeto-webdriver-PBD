-- Webdriver — Parte 2 · papéis e contas. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md
-- Senha das contas de exemplo: 12345678. Se o MySQL recusar (erro 1819, "senha fraca"), rode antes:
--   SET GLOBAL validate_password.policy = LOW;  SET GLOBAL validate_password.length = 8;

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- 7) PAPÉIS (ROLES) E CONTAS DOS EXEMPLOS (aula 11)
-- ---------------------------------------------------------------------
DROP USER IF EXISTS 'bruno'@'localhost', 'carla'@'localhost', 'diego'@'localhost',  -- limpeza das contas de exemplo
                    'admin'@'localhost', 'unicap'@'localhost';
DROP ROLE IF EXISTS PapelUsuario, PapelEmpresa, PapelAdm;   -- limpeza dos papéis

CREATE ROLE PapelUsuario, PapelEmpresa, PapelAdm;    -- cria os 3 papéis

GRANT SELECT, INSERT, UPDATE ON webdriver.vw_meus_arquivos       TO PapelUsuario;  -- usuário: ver, inserir, atualizar
GRANT SELECT                 ON webdriver.vw_historico_operacoes TO PapelUsuario;  -- usuário: histórico só leitura

GRANT SELECT ON webdriver.vw_empresa_usuarios TO PapelEmpresa;  -- empresa: só ver funcionários
GRANT SELECT ON webdriver.vw_empresa_arquivos TO PapelEmpresa;  -- empresa: só ver arquivos deles

GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.PLANO            TO PapelAdm;  -- admin: tudo nas 10 tabelas
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.INSTITUICAO      TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.USUARIO          TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.ADMINISTRADOR    TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.ARQUIVO          TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.OPERACAO         TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.COMPARTILHAMENTO TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.COMENTARIO       TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.SUPORTE          TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.HISTORICO_VERSAO TO PapelAdm;  -- (ATIVIDADES_RECENTES fica de fora)
GRANT SELECT ON webdriver.vw_admin_arquivos TO PapelAdm;                         -- admin: suas visões
GRANT SELECT ON webdriver.vw_admin_usuarios TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.Conta_usuarios  TO PapelAdm;                -- admin: pode chamar
GRANT EXECUTE ON PROCEDURE webdriver.Remover_acessos TO PapelAdm;
GRANT EXECUTE ON FUNCTION  webdriver.Passou_100_dias TO PapelAdm;

CREATE USER 'bruno'@'localhost'  IDENTIFIED BY '12345678';  -- contas com o mesmo nome do login em USUARIO
CREATE USER 'carla'@'localhost'  IDENTIFIED BY '12345678';
CREATE USER 'diego'@'localhost'  IDENTIFIED BY '12345678';
CREATE USER 'admin'@'localhost'  IDENTIFIED BY '12345678';
CREATE USER 'unicap'@'localhost' IDENTIFIED BY '12345678';  -- conta da empresa: o nome da instituição

GRANT PapelUsuario TO 'bruno'@'localhost', 'carla'@'localhost', 'diego'@'localhost';  -- usuários comuns
GRANT PapelAdm     TO 'admin'@'localhost';                                            -- administrador
GRANT PapelEmpresa TO 'unicap'@'localhost';                                           -- empresa

-- Quem entra com uma dessas contas liga o papel com SET ROLE (aula 11). Exemplo no Workbench,
-- conectado como bruno:   SET ROLE PapelUsuario;   SELECT * FROM webdriver.vw_meus_arquivos;
-- O programa em Python faz o SET ROLE sozinho logo depois do login.
