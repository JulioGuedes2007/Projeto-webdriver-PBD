# Webdriver — cadastro, login e contas do MySQL. Explicações no README.md

import hashlib                                       # gera o hash da senha
import re                                            # confere o formato do login
from datetime import date                            # data de hoje

import mysql.connector                               # para reconhecer erros do MySQL
from conexao import conectar, conectar_como, consultar, CONTAS_PROTEGIDAS

FORMATO_CONTA = re.compile(r"^[a-z0-9.-]{1,32}$")    # minúsculas, números, ponto e hífen (até 32)


SQL_PESSOA = ("SELECT U.id_usuario, "                # id do usuário e se ele é admin (1 ou 0)
              "(SELECT COUNT(*) FROM ADMINISTRADOR A WHERE A.id_usuario = U.id_usuario) AS eh_admin "
              "FROM USUARIO U WHERE U.login = %s")


def hash_senha(senha):                               # transforma a senha em hash
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()  # sha256 em texto


def _validar_conta(nome):                            # o nome serve como conta do MySQL?
    if not FORMATO_CONTA.match(nome) or nome in CONTAS_PROTEGIDAS:
        raise ValueError("Use só letras minúsculas, números, ponto ou hífen (até 32 caracteres, sem espaço).")


def _validar_senha(senha):                           # senha mínima
    if len(senha) < 8:
        raise ValueError("A senha precisa ter pelo menos 8 caracteres.")


def _nome_em_uso(cur, nome):                         # já existe conta, usuário ou empresa com esse nome?
    cur.execute("SELECT COUNT(*) FROM mysql.user WHERE user = %s", (nome,))  # conta do MySQL
    total = cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM USUARIO WHERE login = %s", (nome,))    # login de usuário
    total += cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM INSTITUICAO WHERE LOWER(nome) = %s", (nome,))  # conta de empresa
    total += cur.fetchall()[0][0]
    return total > 0


def _criar_conta_mysql(cur, conta, senha, papel):    # cria a conta e entrega o crachá (papel)
    cur.execute("CREATE USER %s@'localhost' IDENTIFIED BY %s", (conta, senha))  # login + senha
    cur.execute(f"GRANT {papel} TO %s@'localhost'", (conta,))                   # papel fixo do código


def cadastrar_usuario(login, email, senha, id_instituicao=None):  # novo usuário do drive
    login = login.strip().lower()                    # login sempre em minúsculas
    _validar_conta(login)
    _validar_senha(senha)
    con = conectar()
    try:
        cur = con.cursor()
        if _nome_em_uso(cur, login):
            raise ValueError("Esse login já está em uso.")
        _criar_conta_mysql(cur, login, senha, "PapelUsuario")  # 1) conta no MySQL
        try:
            cur.execute("INSERT INTO USUARIO (login, senha, data_ingresso, email, id_instituicao) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (login, hash_senha(senha), date.today().isoformat(), email, id_instituicao))  # 2) cadastro
            con.commit()
            return cur.lastrowid                     # id do usuário novo
        except Exception:
            con.rollback()                           # cadastro falhou:
            cur.execute("DROP USER IF EXISTS %s@'localhost'", (login,))  # desfaz a conta
            raise
    finally:
        con.close()


def cadastrar_instituicao(nome, causa_social, endereco, id_plano, senha):  # nova empresa/ONG
    nome = nome.strip()
    conta = nome.lower()                             # a conta da empresa é o nome em minúsculas
    _validar_conta(conta)
    _validar_senha(senha)
    con = conectar()
    try:
        cur = con.cursor()
        if _nome_em_uso(cur, conta):
            raise ValueError("Esse nome já está em uso por outra conta.")
        _criar_conta_mysql(cur, conta, senha, "PapelEmpresa")  # 1) conta da empresa
        try:
            cur.execute("INSERT INTO INSTITUICAO (nome, causa_social, endereco, id_plano) VALUES (%s, %s, %s, %s)",
                        (nome, causa_social, endereco, id_plano))  # 2) cadastro
            con.commit()
            return cur.lastrowid
        except Exception:
            con.rollback()
            cur.execute("DROP USER IF EXISTS %s@'localhost'", (conta,))  # desfaz a conta
            raise
    finally:
        con.close()


def cadastrar_plano(nome, duracao_meses, espaco_gb):  # novo plano
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO PLANO (nome, duracao_meses, data_aquisicao, espaco_por_usuario_gb) "
                    "VALUES (%s, %s, %s, %s)", (nome, duracao_meses, date.today().isoformat(), espaco_gb))
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def tornar_admin(login):                             # usuário vira administrador
    linhas = consultar(SQL_PESSOA, (login.strip().lower(),))
    if not linhas:
        raise ValueError("Usuário não encontrado.")
    if linhas[0]["eh_admin"]:
        raise ValueError("Esse usuário já é administrador.")
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO ADMINISTRADOR (id_usuario) VALUES (%s)", (linhas[0]["id_usuario"],))  # especialização
        con.commit()
        conta = login.strip().lower()
        try:
            cur.execute("REVOKE PapelUsuario FROM %s@'localhost'", (conta,))  # tira o crachá antigo
        except mysql.connector.Error:
            pass                                     # não tinha: segue
        cur.execute("GRANT PapelAdm TO %s@'localhost'", (conta,))            # dá o crachá de admin
    finally:
        con.close()


def entrar(login, senha):                            # login: devolve a sessão da pessoa
    login = login.strip().lower()
    if login in CONTAS_PROTEGIDAS:
        raise ValueError("A conta root entra pela 'Área do dono do banco'.")
    try:
        conectar_como(login, senha).close()          # o próprio MySQL confere login e senha
    except mysql.connector.Error:
        raise ValueError("Login ou senha incorretos.")
    empresa = consultar("SELECT id_instituicao, nome FROM INSTITUICAO WHERE LOWER(nome) = %s", (login,))
    if empresa:                                      # é a conta de uma empresa
        return {"tipo": "empresa", "login": login, "senha": senha,
                "nome": empresa[0]["nome"], "id_instituicao": empresa[0]["id_instituicao"]}
    pessoa = consultar(SQL_PESSOA, (login,))
    if not pessoa:
        raise ValueError("Essa conta não tem cadastro no Webdriver.")
    return {"tipo": "admin" if pessoa[0]["eh_admin"] else "usuario",  # admin ou usuário comum
            "login": login, "senha": senha, "nome": login, "id_usuario": pessoa[0]["id_usuario"]}
