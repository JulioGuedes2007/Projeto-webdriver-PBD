-- Webdriver — Parte 2 · tabela atividades_recentes. Rodar depois da Parte 1, na ordem 01 a 07. Explicações no README.md

USE webdriver;                                       -- usa o banco

DROP TABLE IF EXISTS ATIVIDADES_RECENTES;           -- apaga a versão antiga (permite rodar de novo)

-- ---------------------------------------------------------------------
-- 1) TABELA ATIVIDADES_RECENTES (só o root acessa)
-- ---------------------------------------------------------------------
CREATE TABLE ATIVIDADES_RECENTES(                    -- uma linha por arquivo (1:1)
  id_arquivo    INT         NOT NULL,                -- o arquivo
  ultima_versao DATE        NOT NULL,                -- última data em que foi mexido
  acesso        VARCHAR(20) NOT NULL DEFAULT 'prioritario'           -- prioritário ou não
                CHECK (acesso IN ('prioritario', 'nao prioritario')), -- só esses 2 valores
  PRIMARY KEY (id_arquivo),                          -- PK = o próprio arquivo
  FOREIGN KEY (id_arquivo) REFERENCES ARQUIVO(id_arquivo)  -- liga ao arquivo
);
