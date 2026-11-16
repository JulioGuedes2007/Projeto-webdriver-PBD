# Webdriver — ações com arquivos (subir, editar, compartilhar, comentar, remover, suporte). Explicações no README.md

from datetime import date, datetime                  # datas e horas

from conexao import conectar, consultar, chamar_procedure
from crud import _conferir


DEPENDENTES_DO_ARQUIVO = ["ATIVIDADES_RECENTES", "OPERACAO", "COMENTARIO",  # tabelas com FK
                          "COMPARTILHAMENTO", "HISTORICO_VERSAO"]           # para ARQUIVO


def agora():                                         # data e hora de agora
    n = datetime.now()
    return n.date().isoformat(), n.strftime("%H:%M:%S")  # ('2026-11-11', '18:30:00')


def tem_acesso(cur, id_usuario, id_arquivo):         # dono ou compartilhado?
    cur.execute("SELECT COUNT(*) FROM ARQUIVO WHERE id_arquivo = %s AND id_dono = %s",
                (id_arquivo, id_usuario))            # é o dono?
    if cur.fetchall()[0][0] > 0:
        return True
    cur.execute("SELECT COUNT(*) FROM COMPARTILHAMENTO WHERE id_arquivo = %s AND id_compartilhado = %s",
                (id_arquivo, id_usuario))            # recebeu acesso?
    return cur.fetchall()[0][0] > 0


def _exigir_dono(id_usuario, id_arquivo):            # para o que só o dono pode fazer
    if not consultar("SELECT nome FROM ARQUIVO WHERE id_arquivo = %s AND id_dono = %s", (id_arquivo, id_usuario)):
        raise PermissionError("Só o dono do arquivo pode fazer isso.")


def _exigir_acesso(id_usuario, id_arquivo):          # para o que quem tem acesso pode fazer
    con = conectar()
    try:
        if not tem_acesso(con.cursor(), id_usuario, id_arquivo):
            raise PermissionError("Você não tem acesso a este arquivo.")
    finally:
        con.close()


def _registrar(cur, tipo, id_usuario, id_arquivo, descricao):  # grava operação + versão
    dia, hora = agora()
    cur.execute("INSERT INTO OPERACAO (tipo_operacao, data, hora, id_usuario, id_arquivo) "
                "VALUES (%s, %s, %s, %s, %s)", (tipo, dia, hora, id_usuario, id_arquivo))
    cur.execute("INSERT INTO HISTORICO_VERSAO (data, hora, operacao, conteudo_mudado, id_usuario, id_arquivo) "
                "VALUES (%s, %s, %s, %s, %s, %s)", (dia, hora, tipo, descricao, id_usuario, id_arquivo))


# ---------------- listas (com o id escondido na tela) ----------------
def arquivos_acessiveis(id_usuario, so_do_dono=False):  # arquivos que a pessoa pode usar
    sql = ("SELECT A.id_arquivo, A.nome, U.login AS dono, A.localizacao AS pasta FROM ARQUIVO A "
           "INNER JOIN USUARIO U ON U.id_usuario = A.id_dono WHERE A.id_dono = %s")  # os dela
    params = [id_usuario]
    if not so_do_dono:                               # + os compartilhados com ela
        sql += " OR A.id_arquivo IN (SELECT id_arquivo FROM COMPARTILHAMENTO WHERE id_compartilhado = %s)"
        params.append(id_usuario)
    return consultar(sql + " ORDER BY A.nome", params)


def todos_os_arquivos():                             # para o admin e o root escolherem
    return consultar("SELECT A.id_arquivo, A.nome, U.login AS dono, A.localizacao AS pasta FROM ARQUIVO A "
                     "INNER JOIN USUARIO U ON U.id_usuario = A.id_dono ORDER BY A.nome")


def comentarios(id_arquivo):                         # comentários de um arquivo
    return consultar("SELECT U.login AS autor, C.data, C.hora, C.conteudo FROM COMENTARIO C "
                     "INNER JOIN USUARIO U ON U.id_usuario = C.id_usuario WHERE C.id_arquivo = %s "
                     "ORDER BY C.data, C.hora", (id_arquivo,))


def historico(id_arquivo):                           # versões de um arquivo
    return consultar("SELECT H.data, H.hora, H.operacao, U.login AS feito_por, H.conteudo_mudado "
                     "FROM HISTORICO_VERSAO H INNER JOIN USUARIO U ON U.id_usuario = H.id_usuario "
                     "WHERE H.id_arquivo = %s ORDER BY H.data, H.hora", (id_arquivo,))


# ---------------- ações ----------------
def carregar_arquivo(id_usuario, nome, tipo, tamanho_bytes, url, localizacao="/"):  # subir arquivo
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO ARQUIVO (nome, tipo, tamanho_bytes, data_ultima_modificacao, "
                    "localizacao, url, id_dono) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (nome, tipo, tamanho_bytes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     localizacao, url, id_usuario))  # 1) cria o arquivo (os triggers conferem)
        id_arquivo = cur.lastrowid                   # id do arquivo novo
        _registrar(cur, "carregar", id_usuario, id_arquivo, f"Upload de {nome}")  # 2) operação + versão
        con.commit()                                 # grava tudo junto
        return id_arquivo
    except Exception:
        con.rollback()                               # deu erro: desfaz tudo
        raise
    finally:
        con.close()


def editar_arquivo(id_usuario, id_arquivo, novos_dados, descricao_mudanca):  # editar
    _conferir("ARQUIVO", novos_dados)                # valida as colunas
    proibidas = {"id_arquivo", "id_dono", "data_ultima_modificacao"} & set(novos_dados)
    if proibidas:                                    # não deixa trocar id, dono ou data
        raise PermissionError(f"Não dá para alterar {', '.join(sorted(proibidas))} editando o arquivo.")
    con = conectar()
    try:
        cur = con.cursor()
        if not tem_acesso(cur, id_usuario, id_arquivo):  # só quem tem acesso
            raise PermissionError("Você não tem acesso a este arquivo.")
        dados = dict(novos_dados, data_ultima_modificacao=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sets = ", ".join(f"{c} = %s" for c in dados)
        cur.execute(f"UPDATE ARQUIVO SET {sets} WHERE id_arquivo = %s", list(dados.values()) + [id_arquivo])
        _registrar(cur, "atualizar", id_usuario, id_arquivo, descricao_mudanca)  # operação + versão
        con.commit()                                 # grava tudo junto
    except Exception:
        con.rollback()                               # deu erro: desfaz tudo
        raise
    finally:
        con.close()


def compartilhar(id_dono, id_arquivo, id_destino):   # dá acesso a outra pessoa
    if id_dono == id_destino:                        # não compartilha consigo mesmo
        raise ValueError("O dono já tem acesso ao próprio arquivo.")
    _exigir_dono(id_dono, id_arquivo)
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO COMPARTILHAMENTO (id_arquivo, id_dono, id_compartilhado, data_compartilhamento) "
                    "VALUES (%s, %s, %s, %s)", (id_arquivo, id_dono, id_destino, date.today().isoformat()))
        con.commit()                                 # o trigger Atualizar_acesso marca "compartilhado"
    finally:
        con.close()


def comentar(id_usuario, id_arquivo, texto):         # comentário em um arquivo
    _exigir_acesso(id_usuario, id_arquivo)
    dia, hora = agora()
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO COMENTARIO (conteudo, data, hora, id_usuario, id_arquivo) "
                    "VALUES (%s, %s, %s, %s, %s)", (texto, dia, hora, id_usuario, id_arquivo))
        con.commit()
    finally:
        con.close()


def remover_arquivo(id_usuario, id_arquivo):         # só o dono remove
    _exigir_dono(id_usuario, id_arquivo)
    con = conectar()
    try:
        cur = con.cursor()
        for tabela in DEPENDENTES_DO_ARQUIVO:         # 1) apaga o que aponta para o arquivo
            cur.execute(f"DELETE FROM {tabela} WHERE id_arquivo = %s", (id_arquivo,))
        cur.execute("UPDATE SUPORTE SET id_arquivo = NULL WHERE id_arquivo = %s", (id_arquivo,))  # 2) suporte fica
        cur.execute("DELETE FROM ARQUIVO WHERE id_arquivo = %s", (id_arquivo,))  # 3) por fim, o arquivo
        apagados = cur.rowcount
        con.commit()                                 # grava tudo junto (transação)
        return apagados
    except Exception:
        con.rollback()                               # deu erro: desfaz tudo
        raise
    finally:
        con.close()


def remover_acessos(id_usuario, id_arquivo):         # tira o acesso de todos (procedure)
    _exigir_dono(id_usuario, id_arquivo)
    return chamar_procedure("Remover_acessos", (id_arquivo,))[0]["acessos_removidos"]


def pedir_suporte(id_usuario, descricao, id_arquivo=None):  # pedido de ajuda a um admin
    admins = consultar("SELECT id_administrador FROM ADMINISTRADOR ORDER BY id_administrador")
    if not admins:
        raise ValueError("Ainda não há administrador cadastrado.")
    if id_arquivo is not None:
        _exigir_acesso(id_usuario, id_arquivo)
    dia, hora = agora()
    con = conectar()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO SUPORTE (dia, hora, descricao, id_usuario, id_administrador, id_arquivo) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (dia, hora, descricao, id_usuario, admins[0]["id_administrador"], id_arquivo))  # 1º admin
        con.commit()
        return cur.lastrowid
    finally:
        con.close()
