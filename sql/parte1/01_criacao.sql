-- Webdriver — Parte 1 · a) criação da base. Rodar na ordem: 01 a 05. Explicações no README.md

-- ---------------------------------------------------------------------
-- a) CRIAÇÃO DA BASE DE DADOS
-- ---------------------------------------------------------------------
DROP DATABASE IF EXISTS webdriver;                   -- apaga o banco antigo, se existir
CREATE DATABASE webdriver CHARACTER SET utf8mb4;     -- cria o banco (aceita acentos)
USE webdriver;                                       -- passa a usar este banco

CREATE TABLE PLANO(                                  -- plano que a instituição assina
  id_plano              INT AUTO_INCREMENT,                                      -- id gerado sozinho
  nome                  VARCHAR(50)   NOT NULL,                                  -- nome do plano
  duracao_meses         INT           NOT NULL CHECK (duracao_meses > 0),        -- duração positiva
  data_aquisicao        DATE          NOT NULL,                                  -- quando foi contratado
  espaco_por_usuario_gb DECIMAL(10,2) NOT NULL CHECK (espaco_por_usuario_gb > 0), -- limite por usuário
  PRIMARY KEY (id_plano)                                                         -- chave primária
);

CREATE TABLE INSTITUICAO(                            -- empresa/ONG que usa o drive
  id_instituicao INT AUTO_INCREMENT,                 -- id gerado sozinho
  nome           VARCHAR(100) NOT NULL,              -- nome da instituição
  causa_social   VARCHAR(150),                       -- causa (opcional)
  endereco       VARCHAR(200),                       -- endereço (opcional)
  id_plano       INT UNIQUE,                         -- plano: opcional e exclusivo (1:1)
  PRIMARY KEY (id_instituicao),                      -- chave primária
  FOREIGN KEY (id_plano) REFERENCES PLANO(id_plano)  -- liga ao plano
);

CREATE TABLE USUARIO(                                -- pessoa que usa o drive
  id_usuario     INT AUTO_INCREMENT,                 -- id gerado sozinho
  login          VARCHAR(50)  NOT NULL UNIQUE,       -- login único
  senha          VARCHAR(255) NOT NULL,              -- hash da senha
  data_ingresso  DATE         NOT NULL,              -- quando entrou
  email          VARCHAR(100) NOT NULL UNIQUE,       -- e-mail único
  id_instituicao INT,                                -- instituição (opcional, 1:N)
  PRIMARY KEY (id_usuario),                          -- chave primária
  FOREIGN KEY (id_instituicao) REFERENCES INSTITUICAO(id_instituicao)  -- liga à instituição
);

CREATE TABLE ADMINISTRADOR(                          -- especialização de USUARIO
  id_administrador INT AUTO_INCREMENT,               -- id próprio do admin
  id_usuario       INT NOT NULL UNIQUE,              -- o usuário que é admin (no máximo 1 vez)
  PRIMARY KEY (id_administrador),                    -- chave primária
  FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)  -- liga ao usuário
);

CREATE TABLE ARQUIVO(                                -- arquivo guardado no drive
  id_arquivo              INT AUTO_INCREMENT,                        -- id gerado sozinho
  nome                    VARCHAR(255) NOT NULL,                     -- nome com extensão
  tipo                    VARCHAR(50)  NOT NULL,                     -- extensão: pdf, png, mp4...
  permissoes_acesso       VARCHAR(30)  NOT NULL DEFAULT 'privado',   -- privado ou compartilhado
  tamanho_bytes           INT          NOT NULL CHECK (tamanho_bytes >= 0),  -- tamanho não negativo
  data_ultima_modificacao DATETIME     NOT NULL,                     -- última alteração
  localizacao             VARCHAR(255),                              -- pasta (opcional)
  url                     VARCHAR(500) NOT NULL UNIQUE,              -- endereço único
  id_dono                 INT          NOT NULL,                     -- dono (1:N com USUARIO)
  PRIMARY KEY (id_arquivo),                                          -- chave primária
  UNIQUE (id_arquivo, id_dono),                                      -- par usado pela FK do compartilhamento
  FOREIGN KEY (id_dono) REFERENCES USUARIO(id_usuario)  -- liga ao dono
);

CREATE TABLE OPERACAO(                               -- N:N usuário x arquivo (o que foi feito)
  id_operacao   INT AUTO_INCREMENT,                  -- id gerado sozinho
  tipo_operacao VARCHAR(10) NOT NULL CHECK (tipo_operacao IN ('carregar','atualizar','remover')),  -- só 3 tipos
  data          DATE NOT NULL,                       -- dia da operação
  hora          TIME NOT NULL,                       -- hora da operação
  id_usuario    INT  NOT NULL,                       -- quem fez
  id_arquivo    INT  NOT NULL,                       -- em qual arquivo
  PRIMARY KEY (id_operacao),                         -- chave primária
  FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),  -- liga ao usuário
  FOREIGN KEY (id_arquivo) REFERENCES ARQUIVO(id_arquivo)  -- liga ao arquivo
);

CREATE TABLE COMPARTILHAMENTO(                       -- N:N arquivo x usuário (quem recebeu acesso)
  id_arquivo            INT  NOT NULL,               -- arquivo compartilhado
  id_dono               INT  NOT NULL,               -- dono do arquivo
  id_compartilhado      INT  NOT NULL,               -- quem recebeu o acesso
  data_compartilhamento DATE NOT NULL,               -- quando
  PRIMARY KEY (id_arquivo, id_compartilhado),        -- chave composta
  FOREIGN KEY (id_arquivo, id_dono) REFERENCES ARQUIVO(id_arquivo, id_dono),  -- garante o dono verdadeiro
  FOREIGN KEY (id_compartilhado) REFERENCES USUARIO(id_usuario)  -- liga ao usuário
);

CREATE TABLE COMENTARIO(                             -- N:N usuário x arquivo (comentários)
  id_comentario INT AUTO_INCREMENT,                  -- id gerado sozinho
  conteudo      TEXT NOT NULL,                       -- texto do comentário
  data          DATE NOT NULL,                       -- dia
  hora          TIME NOT NULL,                       -- hora
  id_usuario    INT  NOT NULL,                       -- quem comentou
  id_arquivo    INT  NOT NULL,                       -- em qual arquivo
  PRIMARY KEY (id_comentario),                       -- chave primária
  FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),  -- liga ao usuário
  FOREIGN KEY (id_arquivo) REFERENCES ARQUIVO(id_arquivo)  -- liga ao arquivo
);

CREATE TABLE SUPORTE(                                -- entidade associativa usuário x admin
  id_suporte       INT AUTO_INCREMENT,               -- id gerado sozinho
  dia              DATE NOT NULL,                    -- dia do pedido
  hora             TIME NOT NULL,                    -- hora do pedido
  descricao        TEXT NOT NULL,                    -- o problema
  id_usuario       INT  NOT NULL,                    -- quem pediu
  id_administrador INT  NOT NULL,                    -- quem atende
  id_arquivo       INT,                              -- arquivo (opcional)
  PRIMARY KEY (id_suporte),                          -- chave primária
  FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),  -- liga ao usuário
  FOREIGN KEY (id_administrador) REFERENCES ADMINISTRADOR(id_administrador),  -- liga ao admin
  FOREIGN KEY (id_arquivo) REFERENCES ARQUIVO(id_arquivo)  -- liga ao arquivo (pode ficar vazio)
);

CREATE TABLE HISTORICO_VERSAO(                       -- versões de cada arquivo
  id_historico    INT AUTO_INCREMENT,                -- id gerado sozinho
  data            DATE NOT NULL,                     -- dia da versão
  hora            TIME NOT NULL,                     -- hora da versão
  operacao        VARCHAR(10) NOT NULL CHECK (operacao IN ('carregar','atualizar','remover')),  -- só 3 tipos
  conteudo_mudado TEXT NOT NULL,                     -- o que mudou, em texto
  id_usuario      INT  NOT NULL,                     -- quem alterou
  id_arquivo      INT  NOT NULL,                     -- qual arquivo
  PRIMARY KEY (id_historico),                        -- chave primária
  FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario),  -- liga ao usuário
  FOREIGN KEY (id_arquivo) REFERENCES ARQUIVO(id_arquivo)  -- liga ao arquivo
);
