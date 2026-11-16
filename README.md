# Projeto Webdriver

Banco de dados de um drive de arquivos para instituições sociais, em **MySQL 8**, com um sistema em **Python** (a linguagem de apoio).
Disciplina Projeto de Banco de Dados — UNICAP. Grupo: Heitor, Julio, Gabriel e João.

## Pastas

```
webdriver/
├── README.md
├── modelos/      modelo_conceitual.png · modelo_logico.png · webdriver.mwb (abre no Workbench)
├── sql/
│   ├── parte1/   01_criacao · 02_inserir · 03_buscar · 04_atualizar · 05_remover
│   └── parte2/   01_atividades_recentes · 02_funcao · 03_procedures · 04_triggers
│                 05_carga_inicial · 06_visoes · 07_papeis_e_contas
└── python/       main.py · conexao.py · contas.py · drive.py · areas.py · crud.py · testes.py
```

| Arquivo Python | O que tem |
| --- | --- |
| `main.py` | Menu inicial. É o que se roda |
| `conexao.py` | Conectar ao MySQL, ler os `.sql` e criar a base |
| `contas.py` | Cadastro, login e contas do MySQL (senha em hash) |
| `drive.py` | Ações com arquivos: subir, editar, compartilhar, comentar, remover, suporte |
| `areas.py` | Telas e menus de cada perfil (usuário, empresa, admin, dono do banco) |
| `crud.py` | Inserir, buscar, atualizar e remover em qualquer tabela (Parte 1) |
| `testes.py` | Teste automático de tudo (fora do menu) |

## Como rodar

1. Deixe o serviço **MySQL80** ligado (Windows: Serviços → MySQL80 → Iniciar).
2. Instale o conector uma vez: `python3.15 -m pip install mysql-connector-python`.
3. Abra o terminal na pasta `python/` e rode `python3.15 main.py`.
4. Digite a senha do MySQL do dono do banco (**root**).
5. **Na primeira vez:** opção 3 (Área do dono do banco) → opção 1 (Criar / recriar a base).

Teste automático: `python3.15 testes.py`. Ele recria a base, testa cadastro, login, visões, papéis, função, procedures e triggers, e recria a base de novo no final.

Para rodar só o SQL no Workbench: abra e execute (raio) os arquivos **na ordem**, `parte1/01` a `05` e depois `parte2/01` a `07`. Rodar a Parte 1 inteira também executa as buscas, os updates e os deletes de exemplo.

Para testar uma conta no Workbench: crie uma conexão com o usuário (ex.: `bruno`, senha `12345678`) e rode primeiro `SET ROLE PapelUsuario;` (aula 11). Sem isso a conta não pode nada. Depois: `SELECT * FROM webdriver.vw_meus_arquivos;`.

## Senhas e contas

Existem dois tipos de senha:

- **Senha do root:** do dono do banco, a que vocês usam no Workbench. O programa pede ao abrir.
- **Senha de cada conta:** quem se cadastra escolhe a sua. O sistema guarda o **hash** dela na tabela USUARIO e cria uma **conta no MySQL** com o mesmo login e a mesma senha. No login, quem confere a senha é o próprio MySQL.

Contas de exemplo (senha de todas: **12345678**):

| Login | Tipo | Situação |
| --- | --- | --- |
| `bruno` | Usuário | UNICAP; dono de 2 arquivos |
| `carla` | Usuário | UNICAP; dona de 1 arquivo; recebeu um compartilhamento |
| `diego` | Usuário | Sem instituição; dono de 1 arquivo |
| `admin` | Administrador | Sem instituição; atende o suporte |
| `unicap` | Empresa | A conta da UNICAP |

## Navegação

```
===== WEBDRIVER =====
 1 - Entrar (login e senha)        → abre o menu do perfil da conta
 2 - Cadastrar novo usuário         → login, e-mail, senha e instituição
 3 - Área do dono do banco (root)   → pede a senha do root de novo
 0 - Sair
```

| Perfil | Opções |
| --- | --- |
| **Usuário** | Ver meus arquivos · Subir · Editar · Compartilhar · Comentar · Ver comentários e histórico · Remover (só o dono) · Tirar o acesso de todos (só o dono) · Pedir suporte |
| **Empresa** | Ver funcionários · Ver arquivos dos funcionários |
| **Administrador** | Visão geral dos arquivos · Visão geral dos usuários · Pedidos de suporte · Cadastrar plano · Cadastrar instituição (cria a conta da empresa) · Tornar usuário administrador · Conta_usuarios |
| **Dono do banco** | Criar / recriar a base · Ver atividades_recentes · Verificar_atividades · Chavear · Função dos 100 dias · CRUD de qualquer tabela |

- Os arquivos aparecem numerados na tela; os ids ficam escondidos.
- O que a pessoa **vê** vem das visões, lidas com a conta dela: o próprio banco limita.
- O que a pessoa **faz** passa pelas regras do programa e pelos triggers.

---

## Parte 1

### Modelo lógico

PK = primeira coluna; `->` = chave estrangeira.

```
PLANO(id_plano, nome, duracao_meses, data_aquisicao, espaco_por_usuario_gb)
INSTITUICAO(id_instituicao, nome, causa_social, endereco, id_plano -> PLANO)
USUARIO(id_usuario, login, senha, data_ingresso, email, id_instituicao -> INSTITUICAO)
ADMINISTRADOR(id_administrador, id_usuario -> USUARIO)
ARQUIVO(id_arquivo, nome, tipo, permissoes_acesso, tamanho_bytes,
        data_ultima_modificacao, localizacao, url, id_dono -> USUARIO)
OPERACAO(id_operacao, tipo_operacao, data, hora, id_usuario -> USUARIO, id_arquivo -> ARQUIVO)
COMPARTILHAMENTO((id_arquivo, id_compartilhado), id_dono, data_compartilhamento)
        (id_arquivo, id_dono) -> ARQUIVO ; id_compartilhado -> USUARIO
COMENTARIO(id_comentario, conteudo, data, hora, id_usuario -> USUARIO, id_arquivo -> ARQUIVO)
SUPORTE(id_suporte, dia, hora, descricao, id_usuario -> USUARIO,
        id_administrador -> ADMINISTRADOR, id_arquivo -> ARQUIVO (opcional))
HISTORICO_VERSAO(id_historico, data, hora, operacao, conteudo_mudado,
        id_usuario -> USUARIO, id_arquivo -> ARQUIVO)
```

### Por que cada tabela é assim

- **PLANO × INSTITUICAO (1:1):** FK em INSTITUICAO, opcional e `UNIQUE` (um plano não serve a duas instituições). Um plano em uso não pode ser apagado (a FK impede).
- **USUARIO (1:N com INSTITUICAO):** FK no lado N, opcional (existe usuário sem instituição).
- **ADMINISTRADOR (especialização parcial):** tudo do usuário (via FK) mais o `id_administrador`. `UNIQUE` em `id_usuario`: admin no máximo uma vez.
- **ARQUIVO (1:N com o dono):** o par `UNIQUE (id_arquivo, id_dono)` existe para o COMPARTILHAMENTO conferir o dono.
- **OPERACAO e COMENTARIO (N:N usuário × arquivo):** tabelas próprias com data e hora. A operação só aceita `carregar`, `atualizar` ou `remover` (`CHECK`).
- **COMPARTILHAMENTO (N:N):** o enunciado pede o id do dono. A FK composta `(id_arquivo, id_dono)` impede gravar um dono falso.
- **SUPORTE (entidade associativa usuário × admin):** pode ser sobre um arquivo ou não (`id_arquivo` opcional). Ao apagar o arquivo, o pedido continua, com `id_arquivo` vazio.
- **HISTORICO_VERSAO:** quem alterou e o que mudou, em texto.
- **Remover:** a FK não deixa apagar um arquivo que outras tabelas usam. Por isso o `05_remover.sql` (e o Python) apaga primeiro as operações, comentários, compartilhamentos e o histórico, esvazia o `id_arquivo` do suporte e só então apaga o arquivo, tudo numa transação (`START TRANSACTION` … `COMMIT`, aulas 9 e 12).
- **Exemplos:** 1 plano, a UNICAP, 4 usuários, 4 arquivos, operações, compartilhamentos, comentários, suportes e histórico. Rodando a Parte 1 inteira, a conferência final dá 3 arquivos, 2 suportes e 5 versões.

---

## Parte 2

### O que cada item faz

| Item | Tipo | O que faz |
| --- | --- | --- |
| `ATIVIDADES_RECENTES` | Tabela | Uma linha por arquivo: última data e se é prioritário. Só o root acessa (nenhum papel recebe GRANT nela) |
| `Passou_100_dias(id)` | Função | 1 se a última alteração tem mais de 100 dias, 0 se não |
| `Verificar_atividades()` | Procedure | Cria as linhas que faltam e recalcula tudo com a data de hoje |
| `Conta_usuarios(id)` | Procedure | Dono + pessoas com acesso, sem repetir |
| `Chavear(id)` | Procedure | Troca prioritário ↔ não prioritário |
| `Remover_acessos(id)` | Procedure | Apaga os compartilhamentos e deixa o arquivo privado; o dono continua |
| `Definir_dono` | Trigger | Arquivo inserido pela visão (sem dono) fica com quem está logado |
| `Safe_security` | Trigger | Bloqueia executáveis (`exe`, `bat`, `msi`, `sh`, `apk`...) pelo tipo ou pela extensão |
| `Limite_espaco` / `Limite_espaco_update` | Trigger | Bloqueia se os arquivos do usuário passarem do espaço do plano |
| `Registrar_operacao` | Trigger | Toda operação nova atualiza a data em ATIVIDADES_RECENTES e volta a prioritário |
| `Atualizar_acesso` | Trigger | Quando alguém ganha acesso, o arquivo passa a `compartilhado` |

No ARQUIVO há 3 triggers "antes de inserir". O MySQL roda na ordem em que foram criados: Definir_dono → Safe_security → Limite_espaco.

### Visões e papéis

| Papel | Contas | Pode |
| --- | --- | --- |
| `PapelUsuario` | usuários comuns | Ver, inserir e atualizar em `vw_meus_arquivos`; só ver `vw_historico_operacoes` |
| `PapelEmpresa` | contas de empresa | Só ver `vw_empresa_usuarios` e `vw_empresa_arquivos` |
| `PapelAdm` | administradores | Tudo nas 10 tabelas, menos ATIVIDADES_RECENTES; ver `vw_admin_arquivos` e `vw_admin_usuarios`; chamar Conta_usuarios |

- Nenhuma visão mostra ids. Elas filtram pela conta conectada: `USER() LIKE CONCAT(login, '@%')` (USER() devolve, por exemplo, `bruno@localhost`).
- O papel é ligado com `SET ROLE` (aula 11) depois do login. O programa faz isso sozinho.
- Por causa do `LIKE`, o login aceita só letras minúsculas, números, ponto e hífen (sem `_`, que no LIKE é coringa).

### Decisões onde o enunciado era ambíguo

- **Verificar_atividades:** "atualizar com a data atual" = recalcular comparando com hoje.
- **Atualizar_acesso:** "atualizar os registros de arquivo" = marcar o arquivo como `compartilhado`.
- **Admin "acessa toda a base"** e **"só o root acessa atividades_recentes":** o admin recebe as 10 tabelas, menos essa. Por isso Verificar_atividades e Chavear ficam na área do dono do banco.
- **Conta da empresa:** o login da empresa é o nome da instituição em minúsculas.
- **Nome `Conta_usuarios`:** sem acento, para evitar erro de digitação.

---

## Segurança no Python

- **Proteção contra SQL injection:**
  - os valores sempre vão como parâmetro `%s`;
  - nomes de tabela e coluna só entram se estiverem na lista `TABELAS`.
- **Senhas:** guardadas como hash sha256. A senha do root é pedida com `getpass` e não fica gravada.
- **Transações:** subir e editar gravam arquivo, operação e versão juntos (`commit`), ou nada (`rollback`).
- **Regras do drive:**
  - só quem tem acesso edita ou comenta;
  - só o dono compartilha, remove ou tira acessos;
  - ninguém troca o dono de um arquivo.

## O que não está nos slides (e por quê)

Tudo o resto vem das aulas 2 a 14. Estes itens ficaram porque o MySQL não tem outro jeito de fazer:

| Item | Onde | Por que precisa |
| --- | --- | --- |
| `DELIMITER $$` | função, procedures, triggers | O arquivo `.sql` usa `;` para separar comandos. Sem trocar o separador, o MySQL cortaria a procedure no primeiro `;` de dentro dela. Nos slides o código aparece no editor do Workbench, que faz isso escondido. |
| `READS SQL DATA` | função | O MySQL 8 recusa criar função sem dizer o que ela faz com os dados (erro 1418). |
| `SIGNAL SQLSTATE '45000'` | Safe_security, Limite_espaco | É o único jeito de um trigger **impedir** a inserção (o enunciado pede "impeça"). |


No Python (a linguagem de apoio, que não é das aulas): `mysql-connector-python`, parâmetros `%s`, `hashlib`, `getpass`, `callproc`, a consulta em `mysql.user` (para saber se a conta já existe) e o ajuste `SET GLOBAL validate_password` (só para o MySQL aceitar a senha 12345678).

## Quem fez cada parte

Cada integrante fez um pedaço de cada camada: modelo, SQL da Parte 1, SQL da Parte 2 e Python.

| Pessoa | Modelo | SQL Parte 1 | SQL Parte 2 | Python |
| --- | --- | --- | --- | --- |
| Heitor | `modelo_logico.png` (1ª versão) | `01_criacao.sql` | `01_atividades_recentes.sql` · `05_carga_inicial.sql` | `main.py` · `conexao.py` |
| Julio | `modelo_conceitual.png` (1ª versão) | `02_inserir.sql` · `03_buscar.sql` | `02_funcao.sql` | `crud.py` · `testes.py` |
| Gabriel | `modelo_conceitual.png` (versão final) | `05_remover.sql` | `06_visoes.sql` · `07_papeis_e_contas.sql` | `contas.py` · `drive.py` |
| João | `modelo_logico.png` (versão final) · `webdriver.mwb` | `04_atualizar.sql` | `03_procedures.sql` · `04_triggers.sql` | `areas.py` |

Heitor também fez o `README.md` e o `.gitignore`.
