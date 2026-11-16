# Webdriver — inserir, buscar, atualizar e remover em qualquer tabela (Parte 1). Explicações no README.md

import mysql.connector                               # para reconhecer erros do MySQL
from conexao import conectar
from contas import hash_senha

TABELAS = {                                          # tabelas e colunas aceitas (evita SQL injection)
    "PLANO":            {"pk": ["id_plano"],
                         "colunas": ["nome", "duracao_meses", "data_aquisicao", "espaco_por_usuario_gb"]},
    "INSTITUICAO":      {"pk": ["id_instituicao"],
                         "colunas": ["nome", "causa_social", "endereco", "id_plano"]},
    "USUARIO":          {"pk": ["id_usuario"],
                         "colunas": ["login", "senha", "data_ingresso", "email", "id_instituicao"]},
    "ADMINISTRADOR":    {"pk": ["id_administrador"], "colunas": ["id_usuario"]},
    "ARQUIVO":          {"pk": ["id_arquivo"],
                         "colunas": ["nome", "tipo", "permissoes_acesso", "tamanho_bytes",
                                     "data_ultima_modificacao", "localizacao", "url", "id_dono"]},
    "OPERACAO":         {"pk": ["id_operacao"],
                         "colunas": ["tipo_operacao", "data", "hora", "id_usuario", "id_arquivo"]},
    "COMPARTILHAMENTO": {"pk": ["id_arquivo", "id_compartilhado"],          # chave composta
                         "colunas": ["id_dono", "data_compartilhamento"]},
    "COMENTARIO":       {"pk": ["id_comentario"],
                         "colunas": ["conteudo", "data", "hora", "id_usuario", "id_arquivo"]},
    "SUPORTE":          {"pk": ["id_suporte"],
                         "colunas": ["dia", "hora", "descricao", "id_usuario", "id_administrador", "id_arquivo"]},
    "HISTORICO_VERSAO": {"pk": ["id_historico"],
                         "colunas": ["data", "hora", "operacao", "conteudo_mudado", "id_usuario", "id_arquivo"]},
    "ATIVIDADES_RECENTES": {"pk": ["id_arquivo"], "colunas": ["ultima_versao", "acesso"]},   # Parte 2
}


def _conferir(tabela, colunas):                      # valida tabela e colunas
    tabela = tabela.upper()                          # aceita minúsculas
    if tabela not in TABELAS:                        # tabela fora da lista
        raise ValueError(f"Tabela desconhecida: {tabela}")
    validas = set(TABELAS[tabela]["pk"]) | set(TABELAS[tabela]["colunas"])  # colunas permitidas
    erradas = [c for c in colunas if c not in validas]  # colunas fora da lista
    if erradas:
        raise ValueError(f"Coluna(s) inválida(s) em {tabela}: {', '.join(erradas)}")
    return tabela                                    # nome da tabela em maiúsculas


def _proteger_senha(tabela, dados):                  # garante hash na senha do USUARIO
    if tabela == "USUARIO" and dados.get("senha"):   # só se veio senha
        dados = dict(dados, senha=hash_senha(dados["senha"]))  # troca pela versão em hash
    return dados


def inserir(tabela, dados):                          # INSERT em qualquer tabela
    tabela = _conferir(tabela, dados)                # valida
    dados = _proteger_senha(tabela, dados)           # hash da senha, se for USUARIO
    colunas = ", ".join(dados)                       # "nome, tipo, ..."
    marcas = ", ".join(["%s"] * len(dados))          # "%s, %s, ..." (valores vão separados)
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(f"INSERT INTO {tabela} ({colunas}) VALUES ({marcas})", list(dados.values()))
        con.commit()                                 # grava
        return cur.lastrowid                         # id gerado
    finally:
        con.close()


def buscar(tabela, filtros=None):                    # SELECT em qualquer tabela
    filtros = filtros or {}                          # sem filtro = tudo
    tabela = _conferir(tabela, filtros)              # valida
    condicoes, valores = [], []
    for coluna, valor in filtros.items():            # monta o WHERE
        operador = "LIKE" if isinstance(valor, str) and "%" in valor else "="  # % = parte do texto
        condicoes.append(f"{coluna} {operador} %s")
        valores.append(valor)
    sql = f"SELECT * FROM {tabela}"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)   # junta os filtros com AND
    con = conectar()
    try:
        cur = con.cursor(dictionary=True)            # linhas como dicionário
        cur.execute(sql, valores)
        return cur.fetchall()                        # lista de linhas
    finally:
        con.close()


def _where_da_chave(tabela, chave):                  # monta o WHERE pela chave primária
    pk = TABELAS[tabela]["pk"]
    if sorted(chave) != sorted(pk):                  # exige a chave completa
        raise ValueError(f"Para {tabela}, informe a chave completa: {', '.join(pk)}")
    return " AND ".join(f"{c} = %s" for c in pk), [chave[c] for c in pk]


def atualizar(tabela, chave, dados):                 # UPDATE em qualquer tabela
    tabela = _conferir(tabela, list(chave) + list(dados))  # valida
    where, valores_chave = _where_da_chave(tabela, chave)  # qual linha
    dados = _proteger_senha(tabela, dados)           # hash da senha, se for USUARIO
    sets = ", ".join(f"{c} = %s" for c in dados)     # "nome = %s, ..."
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(f"UPDATE {tabela} SET {sets} WHERE {where}", list(dados.values()) + valores_chave)
        con.commit()
        return cur.rowcount                          # quantas linhas mudaram
    finally:
        con.close()


def remover(tabela, chave):                          # DELETE em qualquer tabela
    tabela = _conferir(tabela, chave)                # valida
    where, valores = _where_da_chave(tabela, chave)  # qual linha
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute(f"DELETE FROM {tabela} WHERE {where}", valores)
        con.commit()
        return cur.rowcount                          # quantas linhas saíram
    except mysql.connector.Error as erro:
        if getattr(erro, "errno", None) == 1451:     # 1451 = outra tabela aponta para esta linha (FK)
            raise ValueError("Não dá para remover: há registros ligados a este (chave estrangeira). "
                             "Remova esses registros antes.") from erro
        raise
    finally:
        con.close()
