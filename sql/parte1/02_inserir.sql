-- Webdriver — Parte 1 · b) inserir (dados de exemplo). Rodar na ordem: 01 a 05. Explicações no README.md
-- Senha de todos os exemplos: 12345678 (aqui fica só o hash dela)

USE webdriver;                                       -- usa o banco

-- ---------------------------------------------------------------------
-- b) INSERIR OBJETOS (dados de exemplo)
-- ---------------------------------------------------------------------
INSERT INTO PLANO (nome, duracao_meses, data_aquisicao, espaco_por_usuario_gb) VALUES
  ('Educacional', 12, '2026-02-01', 50.00);                                    -- plano 1: 50 GB por pessoa

INSERT INTO INSTITUICAO (nome, causa_social, endereco, id_plano) VALUES
  ('UNICAP', 'Educação superior', 'Rua do Príncipe, 526 - Recife', 1);         -- instituição 1, com o plano 1

INSERT INTO USUARIO (login, senha, data_ingresso, email, id_instituicao) VALUES
  ('bruno', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', '2026-03-01', 'bruno@email.com', 1),     -- usuário 1: UNICAP
  ('carla', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', '2026-03-05', 'carla@email.com', 1),     -- usuário 2: UNICAP
  ('diego', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', '2026-04-10', 'diego@email.com', NULL),  -- usuário 3: sem instituição
  ('admin', 'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f', '2026-01-15', 'admin@email.com', NULL);  -- usuário 4: sem instituição

INSERT INTO ADMINISTRADOR (id_usuario) VALUES (4);                             -- o usuário 4 (admin) vira administrador 1

INSERT INTO ARQUIVO (nome, tipo, permissoes_acesso, tamanho_bytes,
                     data_ultima_modificacao, localizacao, url, id_dono) VALUES
  ('trabalho_bd.pdf',  'pdf',  'privado',       524288,   '2026-10-20 14:30:00', '/faculdade/bd', 'https://drive.exemplo/f/1', 1),  -- arquivo 1: do bruno
  ('foto_turma.png',   'png',  'compartilhado', 2097152,  '2026-10-21 09:00:00', '/fotos',        'https://drive.exemplo/f/2', 1),  -- arquivo 2: do bruno
  ('relatorio.docx',   'docx', 'compartilhado', 102400,   '2026-10-25 10:15:00', '/projetos',     'https://drive.exemplo/f/3', 2),  -- arquivo 3: da carla
  ('apresentacao.mp4', 'mp4',  'privado',       52428800, '2026-10-23 11:10:00', '/aulas',        'https://drive.exemplo/f/4', 3);  -- arquivo 4: do diego

INSERT INTO OPERACAO (tipo_operacao, data, hora, id_usuario, id_arquivo) VALUES
  ('carregar',  '2026-10-20', '14:30:00', 1, 1),   -- bruno subiu o arquivo 1
  ('carregar',  '2026-10-21', '09:00:00', 1, 2),   -- bruno subiu o arquivo 2
  ('carregar',  '2026-10-22', '16:45:00', 2, 3),   -- carla subiu o arquivo 3
  ('atualizar', '2026-10-25', '10:15:00', 1, 3),   -- bruno editou o arquivo 3
  ('carregar',  '2026-10-23', '11:10:00', 3, 4);   -- diego subiu o arquivo 4

INSERT INTO COMPARTILHAMENTO (id_arquivo, id_dono, id_compartilhado, data_compartilhamento) VALUES
  (2, 1, 2, '2026-10-21'),   -- bruno deu acesso à carla
  (2, 1, 3, '2026-10-22'),   -- bruno deu acesso ao diego
  (3, 2, 1, '2026-10-23');   -- carla deu acesso ao bruno

INSERT INTO COMENTARIO (conteudo, data, hora, id_usuario, id_arquivo) VALUES
  ('Ótima foto!',                   '2026-10-22', '08:00:00', 2, 2),   -- carla no arquivo 2
  ('Revisei a introdução.',         '2026-10-25', '10:20:00', 1, 3),   -- bruno no arquivo 3
  ('Falta a referência do slide 4.','2026-10-26', '19:05:00', 2, 3);   -- carla no arquivo 3

INSERT INTO SUPORTE (dia, hora, descricao, id_usuario, id_administrador, id_arquivo) VALUES
  ('2026-10-24', '13:00:00', 'Não consigo abrir o vídeo.',  3, 1, 4),     -- diego, sobre o arquivo 4
  ('2026-10-26', '17:30:00', 'Como altero minha senha?',    2, 1, NULL);  -- carla, sem arquivo

INSERT INTO HISTORICO_VERSAO (data, hora, operacao, conteudo_mudado, id_usuario, id_arquivo) VALUES
  ('2026-10-20', '14:30:00', 'carregar',  'Versão inicial do trabalho.',          1, 1),   -- 1ª versão do arquivo 1
  ('2026-10-21', '09:00:00', 'carregar',  'Upload da foto da turma.',             1, 2),   -- 1ª versão do arquivo 2
  ('2026-10-22', '16:45:00', 'carregar',  'Versão inicial do relatório.',         2, 3),   -- 1ª versão do arquivo 3
  ('2026-10-25', '10:15:00', 'atualizar', 'Introdução reescrita (2 parágrafos).', 1, 3),   -- 2ª versão do arquivo 3
  ('2026-10-23', '11:10:00', 'carregar',  'Upload da gravação da aula.',          3, 4);   -- 1ª versão do arquivo 4
