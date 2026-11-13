-- Webdriver — Parte 1 · c) buscar. Rodar na ordem: 01 a 05. Explicações no README.md

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- c) BUSCAR
-- ---------------------------------------------------------------------
-- c1) arquivos do bruno
SELECT A.nome, A.tipo, A.tamanho_bytes, A.data_ultima_modificacao   -- colunas mostradas
FROM ARQUIVO A                                                       -- tabela de arquivos
INNER JOIN USUARIO U ON A.id_dono = U.id_usuario                     -- junta com o dono
WHERE U.login = 'bruno';                                            -- só os do bruno

-- c2) arquivos compartilhados com o bruno e o dono de cada um
SELECT A.nome, D.login AS dono, C.data_compartilhamento              -- colunas mostradas
FROM COMPARTILHAMENTO C                                              -- tabela de acessos
INNER JOIN ARQUIVO A ON C.id_arquivo = A.id_arquivo                  -- nome do arquivo
INNER JOIN USUARIO D ON C.id_dono = D.id_usuario                     -- D = dono
INNER JOIN USUARIO R ON C.id_compartilhado = R.id_usuario            -- R = quem recebeu
WHERE R.login = 'bruno';                                            -- só o que o bruno recebeu

-- c3) arquivo por parte do nome
SELECT nome, tipo, url FROM ARQUIVO WHERE nome LIKE '%relat%';       -- nome contém relat

-- c4) histórico do arquivo 3, do mais novo ao mais antigo
SELECT H.data, H.hora, H.operacao, U.login AS alterado_por, H.conteudo_mudado  -- colunas mostradas
FROM HISTORICO_VERSAO H                                              -- tabela de versões
INNER JOIN USUARIO U ON H.id_usuario = U.id_usuario                  -- quem alterou
WHERE H.id_arquivo = 3                                               -- só o arquivo 3
ORDER BY H.data DESC, H.hora DESC;                                   -- mais novo primeiro

-- c5) usuários de cada instituição e o plano dela
SELECT I.nome AS instituicao, P.nome AS plano, U.login               -- colunas mostradas
FROM USUARIO U                                                       -- tabela de usuários
INNER JOIN INSTITUICAO I ON U.id_instituicao = I.id_instituicao      -- só quem tem instituição
INNER JOIN PLANO P       ON I.id_plano = P.id_plano                  -- plano da instituição
ORDER BY I.nome, U.login;                                            -- ordena por instituição

-- c6) pedidos de suporte, com o arquivo quando houver
SELECT S.dia, S.hora, U.login AS usuario, ADM_U.login AS administrador,  -- colunas mostradas
       (SELECT A.nome FROM ARQUIVO A WHERE A.id_arquivo = S.id_arquivo) AS arquivo,  -- subconsulta: vazio se não houver
       S.descricao                                                       -- o problema
FROM SUPORTE S                                                       -- tabela de suporte
INNER JOIN USUARIO U        ON S.id_usuario = U.id_usuario           -- quem pediu
INNER JOIN ADMINISTRADOR AD ON S.id_administrador = AD.id_administrador  -- qual admin
INNER JOIN USUARIO ADM_U    ON AD.id_usuario = ADM_U.id_usuario;     -- login do admin
