# Webdriver — conexão com o MySQL e criação da base. Explicações no README.md

import getpass                                       # pede senha sem mostrar na tela
import re                                            # expressões regulares (ler os .sql)
import warnings                                      # esconde avisos do conector
from pathlib import Path                             # caminhos de arquivo

try:
    import mysql.connector                           # conector oficial do MySQL
except ImportError:                                  # se não estiver instalado
    raise SystemExit("Falta o conector. Rode no terminal: python3.15 -m pip install mysql-connector-python")

CONFIG = {"host": "localhost", "port": 3306, "user": "root", "password": ""}  # senha vazia = perguntar
BANCO = "webdriver"                                  # nome do banco
PASTA_SQL = Path(__file__).resolve().parent.parent / "sql"  # pasta sql/ ao lado de python/
ARQUIVOS_DA_BASE = [PASTA_SQL / "parte1" / "01_criacao.sql",   # tabelas
                    PASTA_SQL / "parte1" / "02_inserir.sql"]   # dados de exemplo
ARQUIVOS_DA_BASE += sorted((PASTA_SQL / "parte2").glob("0*.sql"))  # + Parte 2, de 01 a 07
CONTAS_PROTEGIDAS = {"root", "mysql.sys", "mysql.session", "mysql.infoschema"}  # nunca apagar
PAPEIS = {"usuario": "PapelUsuario", "empresa": "PapelEmpresa", "admin": "PapelAdm"}  # perfil -> papel

_senha_ja_pedida = False                             # a senha do root só é pedida uma vez


def pedir_senha_root():                              # pede e confere a senha do root
    global _senha_ja_pedida
    CONFIG["password"] = getpass.getpass("Senha do MySQL (root) — não aparece ao digitar: ")
    _senha_ja_pedida = True
    conectar(com_banco=False).close()                # tenta entrar: dá erro se estiver errada


def senha_root_confere(senha):                       # a senha digitada é a do root?
    try:
        mysql.connector.connect(host=CONFIG["host"], port=CONFIG["port"],
                                user="root", password=senha).close()
        return True
    except mysql.connector.Error:
        return False


def conectar(com_banco=True):                        # conexão como root (o dono do banco)
    global _senha_ja_pedida
    if not CONFIG["password"] and not _senha_ja_pedida:  # ainda não tem senha
        CONFIG["password"] = getpass.getpass("Senha do MySQL (root) — não aparece ao digitar: ")
        _senha_ja_pedida = True
    cfg = dict(CONFIG)                               # copia a configuração
    if com_banco:
        cfg["database"] = BANCO                      # entra direto no banco webdriver
    try:
        return mysql.connector.connect(**cfg)
    except mysql.connector.Error as erro:
        if getattr(erro, "errno", None) == 1045:     # 1045 = senha errada
            CONFIG["password"], _senha_ja_pedida = "", False  # pergunta de novo na próxima
            raise ConnectionError("Senha do MySQL (root) incorreta.") from erro
        if getattr(erro, "errno", None) == 1049:     # 1049 = banco não existe
            raise ConnectionError("O banco ainda não existe. Crie na 'Área do dono do banco', opção 1.") from erro
        raise


def conectar_como(conta, senha, tipo=None):          # conexão com a conta de uma pessoa
    con = mysql.connector.connect(host=CONFIG["host"], port=CONFIG["port"],
                                  user=conta, password=senha)  # o MySQL confere login e senha
    if tipo:                                         # sem papel ligado a conta não pode nada
        cur = con.cursor()
        cur.execute(f"SET ROLE {PAPEIS[tipo]}")      # liga o papel do perfil (aula 11)
        cur.execute(f"USE {BANCO}")                  # só agora ela pode usar o banco
    return con


def consultar(sql, params=(), dicionario=True, con=None):  # SELECT (root, ou a conexão dada)
    propria = con is None                            # abrimos a conexão aqui?
    con = con or conectar()
    try:
        cur = con.cursor(dictionary=dicionario)      # linhas como dicionário ou tupla
        cur.execute(sql, params)                     # valores vão separados (%s)
        return cur.fetchall()
    finally:
        if propria:
            con.close()


def executar(sql, params=()):                        # INSERT/UPDATE/DELETE como root
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(sql, params)
        con.commit()                                 # grava
        return cur.lastrowid or cur.rowcount         # id novo ou linhas afetadas
    finally:
        con.close()


def chamar_procedure(nome, args=(), con=None):       # CALL de uma procedure
    propria = con is None
    con = con or conectar()
    try:
        cur = con.cursor()
        cur.callproc(nome, args)                     # executa a procedure
        with warnings.catch_warnings():              # esconde aviso do conector
            warnings.simplefilter("ignore", DeprecationWarning)
            sr = cur.stored_results                  # resultados da procedure
            resultados = list(sr() if callable(sr) else sr)
        linhas = []
        for resultado in resultados:                 # transforma em dicionários
            colunas = resultado.column_names
            linhas += [dict(zip(colunas, l)) for l in resultado.fetchall()]
        con.commit()                                 # grava o que a procedure mudou
        return linhas
    except Exception:
        con.rollback()                               # deu erro: desfaz
        raise
    finally:
        if propria:
            con.close()


def _comandos_sql(texto):                            # quebra um arquivo .sql em comandos
    sem_comentarios = re.sub(r"--[^\n]*", "", texto)  # tira os comentários
    partes = re.split(r"^\s*DELIMITER\s+(\S+)\s*$", sem_comentarios, flags=re.M | re.I)  # separa nos DELIMITER
    comandos, delimitador = [], ";"                  # começa com ; como separador
    for i, trecho in enumerate(partes):
        if i % 2 == 1:                               # posição ímpar = novo delimitador
            delimitador = trecho
            continue
        comandos += [c.strip() for c in trecho.split(delimitador) if c.strip()]
    return comandos


def _contas_do_sistema(cur):                         # contas criadas pelo sistema (para limpar)
    try:
        cur.execute("SELECT login FROM webdriver.USUARIO UNION SELECT LOWER(nome) FROM webdriver.INSTITUICAO")
        return [c for (c,) in cur.fetchall() if c not in CONTAS_PROTEGIDAS]
    except mysql.connector.Error:                    # banco ainda não existe
        return []


def _aceitar_senha_de_8_digitos(cur):                # se o MySQL exigir senha forte, afrouxa
    cur.execute("SHOW VARIABLES LIKE 'validate_password%'")
    nomes = {nome for nome, _ in cur.fetchall()}     # variáveis da regra de senha forte
    sep = "." if "validate_password.policy" in nomes else "_"  # MySQL 8 usa ponto; versões antigas, _
    if f"validate_password{sep}policy" in nomes:     # a regra está ligada
        cur.execute(f"SET GLOBAL validate_password{sep}policy = LOW")  # só exige tamanho
        cur.execute(f"SET GLOBAL validate_password{sep}length = 8")    # 8 caracteres
        print("(Aviso: a regra de senha forte do MySQL foi ajustada para aceitar 12345678.)")


def criar_base():                                    # apaga e recria tudo (Parte 1 + Parte 2)
    faltando = [a.name for a in ARQUIVOS_DA_BASE if not a.exists()]
    if faltando or len(ARQUIVOS_DA_BASE) < 9:        # 2 da Parte 1 + 7 da Parte 2
        raise FileNotFoundError(f"Arquivos .sql não encontrados na pasta {PASTA_SQL}")
    con = conectar(com_banco=False)                  # sem banco: ele pode não existir
    try:
        cur = con.cursor()
        for conta in _contas_do_sistema(cur):        # apaga as contas de quem foi cadastrado
            cur.execute("DROP USER IF EXISTS %s@'localhost'", (conta,))
        _aceitar_senha_de_8_digitos(cur)
        for arquivo in ARQUIVOS_DA_BASE:             # roda os .sql na ordem
            for comando in _comandos_sql(arquivo.read_text(encoding="utf-8")):
                try:
                    cur.execute(comando)
                    if cur.with_rows:                # descarta resultados
                        cur.fetchall()
                except Exception as erro:            # mostra onde falhou
                    trecho = " ".join(comando.split())[:150]
                    raise RuntimeError(f"{erro}\n   em {arquivo.name}: {trecho} ...") from erro
        con.commit()
    finally:
        con.close()
    print("Base criada: 11 tabelas, exemplos (bruno, carla, diego, admin, UNICAP) e toda a Parte 2.")
