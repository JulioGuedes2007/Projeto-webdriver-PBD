# Webdriver — telas e menus de cada perfil (usuário, empresa, admin, dono do banco). Explicações no README.md

import getpass                                       # senha sem aparecer na tela
import time                                          # para gerar o endereço (url) do arquivo
from datetime import date, datetime

import contas
import crud
import drive
from conexao import (conectar_como, consultar, chamar_procedure, criar_base,
                     senha_root_confere)


# ---------------- ajudantes de tela ----------------
def _texto(valor):                                   # valor -> texto para a tabela
    if valor is None:
        return "-"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat(sep=" ") if isinstance(valor, datetime) else valor.isoformat()
    return str(valor)[:40]                           # corta textos longos


def mostrar(linhas, titulo=None):                    # imprime linhas como tabela
    if titulo:
        print(f"\n{titulo}")
    if not linhas:
        print("  (nada para mostrar)")
        return
    colunas = list(linhas[0].keys())
    largura = {c: max(len(c), *(len(_texto(l[c])) for l in linhas)) for c in colunas}
    print("  " + " | ".join(c.ljust(largura[c]) for c in colunas))      # cabeçalho
    print("  " + "-+-".join("-" * largura[c] for c in colunas))         # linha
    for l in linhas:
        print("  " + " | ".join(_texto(l[c]).ljust(largura[c]) for c in colunas))


def perguntar(msg, obrigatorio=True):                # lê um texto
    while True:
        valor = input(msg).strip()
        if valor or not obrigatorio:
            return valor
        print("  Campo obrigatório.")


def perguntar_numero(msg, obrigatorio=True):         # lê um número inteiro
    while True:
        valor = input(msg).strip()
        if not valor and not obrigatorio:
            return None
        if valor.isdigit():
            return int(valor)
        print("  Digite só números.")


def confirmar(msg):                                  # pergunta s/n
    return input(f"{msg} (s/n): ").strip().lower() == "s"


def pedir_senha_nova():                              # senha digitada duas vezes
    while True:
        s1 = getpass.getpass("Senha (mínimo 8 caracteres, não aparece): ")
        s2 = getpass.getpass("Repita a senha: ")
        if s1 == s2:
            return s1
        print("  As senhas não conferem. Tente de novo.")


def escolher(itens, rotulo, titulo):                 # lista numerada; devolve o item escolhido
    if not itens:
        raise ValueError("Não há nada para escolher.")
    print(f"\n{titulo}")
    for i, item in enumerate(itens, start=1):        # #1, #2... (o id fica escondido)
        print(f"  {i} - {rotulo(item)}")
    n = perguntar_numero("Número (0 = cancelar): ")
    if n == 0:
        raise ValueError("Cancelado.")
    if not 1 <= n <= len(itens):
        raise ValueError("Número fora da lista.")
    return itens[n - 1]


def _rotulo_arquivo(a):                              # como um arquivo aparece na lista
    return f"{a['nome']}  (dono: {a['dono']}, pasta: {a['pasta'] or '/'})"


def _menu(titulo, opcoes, acoes):                    # laço padrão de todo menu
    while True:
        print(f"\n===== {titulo} =====")
        for k, v in opcoes.items():                  # mostra as opções
            print(f" {k} - {v}")
        op = input("Opção: ").strip()
        if op == "0":
            return                                   # volta / sai da conta
        if op not in acoes:
            print("Opção inválida.")
            continue
        try:
            acoes[op]()                              # executa a opção
        except Exception as erro:                    # mostra o erro (do programa ou do MySQL) e continua
            print(f"ERRO: {erro}")


# ---------------- cadastro e login ----------------
def tela_cadastro():                                 # cadastrar novo usuário
    print("\n-- Cadastro de usuário --")
    login = perguntar("Login (minúsculas, sem espaço): ")
    email = perguntar("E-mail: ")
    senha = pedir_senha_nova()
    instituicoes = consultar("SELECT id_instituicao, nome FROM INSTITUICAO ORDER BY nome")
    id_inst = None
    if instituicoes and confirmar("Faz parte de uma instituição?"):
        id_inst = escolher(instituicoes, lambda i: i["nome"], "Instituições:")["id_instituicao"]
    contas.cadastrar_usuario(login, email, senha, id_inst)  # cria cadastro + conta do MySQL
    print(f"Usuário '{login.lower()}' cadastrado. Já pode entrar com o login e a senha.")


def tela_login():                                    # entrar e abrir o menu certo
    login = perguntar("Login: ")
    senha = getpass.getpass("Senha (não aparece): ")
    sessao = contas.entrar(login, senha)             # o MySQL confere a senha
    if sessao["tipo"] == "empresa":
        menu_empresa(sessao)
    elif sessao["tipo"] == "admin":
        menu_admin(sessao)
    else:
        menu_usuario(sessao)


# ---------------- usuário comum ----------------
def menu_usuario(s):
    uid = s["id_usuario"]

    def ver_meus_arquivos():                         # lido pela visão, com a conta da pessoa
        con = conectar_como(s["login"], s["senha"], s["tipo"])
        try:
            linhas = consultar("SELECT nome, tipo, permissoes_acesso AS acesso, tamanho_bytes, "
                               "data_ultima_modificacao AS modificado, localizacao AS pasta "
                               "FROM vw_meus_arquivos ORDER BY nome", con=con)
        finally:
            con.close()
        mostrar(linhas, "Meus arquivos e os compartilhados comigo (visão vw_meus_arquivos):")

    def subir():
        nome = perguntar("Nome do arquivo (com extensão, ex.: notas.pdf): ")
        tipo = nome.rsplit(".", 1)[-1].lower() if "." in nome else perguntar("Tipo (ex.: pdf): ").lower()
        tamanho = perguntar_numero("Tamanho em bytes: ")
        pasta = perguntar("Pasta (Enter = /): ", obrigatorio=False) or "/"
        url = f"https://drive.exemplo/{s['login']}/{int(time.time())}-{nome}"  # endereço único
        drive.carregar_arquivo(uid, nome, tipo, tamanho, url, pasta)  # triggers podem barrar
        print("Arquivo enviado. Operação 'carregar' registrada.")

    def editar():
        a = escolher(drive.arquivos_acessiveis(uid), _rotulo_arquivo, "Qual arquivo editar?")
        novos = {}
        nome = perguntar("Novo nome (Enter = manter): ", obrigatorio=False)
        pasta = perguntar("Nova pasta (Enter = manter): ", obrigatorio=False)
        tamanho = perguntar_numero("Novo tamanho em bytes (Enter = manter): ", obrigatorio=False)
        if nome:
            novos["nome"] = nome
        if pasta:
            novos["localizacao"] = pasta
        if tamanho is not None:
            novos["tamanho_bytes"] = tamanho
        if not novos:
            print("Nada mudou.")
            return
        descricao = perguntar("O que mudou (vai para o histórico): ")
        drive.editar_arquivo(uid, a["id_arquivo"], novos, descricao)
        print("Arquivo atualizado. Operação 'atualizar' registrada.")

    def compartilhar():
        a = escolher(drive.arquivos_acessiveis(uid, so_do_dono=True), _rotulo_arquivo, "Qual arquivo compartilhar?")
        destino = perguntar("Login de quem vai receber: ").lower()
        achado = consultar("SELECT id_usuario FROM USUARIO WHERE login = %s", (destino,))
        if not achado:
            raise ValueError("Usuário não encontrado.")
        drive.compartilhar(uid, a["id_arquivo"], achado[0]["id_usuario"])
        print(f"Compartilhado com {destino}.")

    def comentar():
        a = escolher(drive.arquivos_acessiveis(uid), _rotulo_arquivo, "Em qual arquivo?")
        drive.comentar(uid, a["id_arquivo"], perguntar("Comentário: "))
        print("Comentário publicado.")

    def ver_comentarios_e_historico():
        a = escolher(drive.arquivos_acessiveis(uid), _rotulo_arquivo, "De qual arquivo?")
        mostrar(drive.comentarios(a["id_arquivo"]), f"Comentários de {a['nome']}:")
        mostrar(drive.historico(a["id_arquivo"]), f"Histórico de versões de {a['nome']}:")

    def remover():
        a = escolher(drive.arquivos_acessiveis(uid, so_do_dono=True), _rotulo_arquivo, "Qual arquivo remover?")
        if confirmar(f"Remover '{a['nome']}' e tudo ligado a ele?"):
            drive.remover_arquivo(uid, a["id_arquivo"])
            print("Arquivo removido.")

    def tirar_acessos():
        a = escolher(drive.arquivos_acessiveis(uid, so_do_dono=True), _rotulo_arquivo, "De qual arquivo?")
        print("Acessos removidos:", drive.remover_acessos(uid, a["id_arquivo"]))

    def pedir_suporte():
        descricao = perguntar("Descreva o problema: ")
        id_arquivo = None
        if confirmar("É sobre um arquivo?"):
            id_arquivo = escolher(drive.arquivos_acessiveis(uid), _rotulo_arquivo, "Qual?")["id_arquivo"]
        drive.pedir_suporte(uid, descricao, id_arquivo)
        print("Pedido enviado ao administrador.")

    _menu(f"Olá, {s['login']}", {
        "1": "Ver meus arquivos", "2": "Subir arquivo", "3": "Editar arquivo",
        "4": "Compartilhar arquivo", "5": "Comentar em um arquivo",
        "6": "Ver comentários e histórico de um arquivo", "7": "Remover arquivo (só o dono)",
        "8": "Tirar o acesso de todos (só o dono)", "9": "Pedir suporte", "0": "Sair da conta"},
        {"1": ver_meus_arquivos, "2": subir, "3": editar, "4": compartilhar, "5": comentar,
         "6": ver_comentarios_e_historico, "7": remover, "8": tirar_acessos, "9": pedir_suporte})


# ---------------- empresa ----------------
def menu_empresa(s):
    def ver(visao, titulo):                          # lido pela visão, com a conta da empresa
        con = conectar_como(s["login"], s["senha"], s["tipo"])
        try:
            mostrar(consultar(f"SELECT * FROM {visao}", con=con), titulo)
        finally:
            con.close()

    _menu(f"{s['nome']} (empresa)", {"1": "Ver funcionários", "2": "Ver arquivos dos funcionários",
                                     "0": "Sair da conta"},
          {"1": lambda: ver("vw_empresa_usuarios", "Funcionários (visão vw_empresa_usuarios):"),
           "2": lambda: ver("vw_empresa_arquivos", "Arquivos dos funcionários (visão vw_empresa_arquivos):")})


# ---------------- administrador ----------------
def menu_admin(s):
    def com_conta_admin(sql, titulo):                # lido com a conta do admin (papel PapelAdm)
        con = conectar_como(s["login"], s["senha"], s["tipo"])
        try:
            mostrar(consultar(sql, con=con), titulo)
        finally:
            con.close()

    def cadastrar_plano():
        nome = perguntar("Nome do plano: ")
        meses = perguntar_numero("Duração em meses: ")
        espaco = perguntar_numero("Espaço por usuário (GB): ")
        contas.cadastrar_plano(nome, meses, espaco)
        print("Plano cadastrado.")

    def cadastrar_instituicao():
        nome = perguntar("Nome (vira o login da empresa; sem espaço, ex.: cafeteria): ")
        causa = perguntar("Causa social (Enter = nenhuma): ", obrigatorio=False) or None
        endereco = perguntar("Endereço (Enter = nenhum): ", obrigatorio=False) or None
        livres = consultar("SELECT id_plano, nome, espaco_por_usuario_gb AS gb FROM PLANO "
                           "WHERE id_plano NOT IN (SELECT id_plano FROM INSTITUICAO WHERE id_plano IS NOT NULL)")
        id_plano = None
        if livres and confirmar("Vai aderir a um plano?"):
            id_plano = escolher(livres, lambda p: f"{p['nome']} ({p['gb']} GB por pessoa)", "Planos livres:")["id_plano"]
        print("Senha da conta da empresa:")
        contas.cadastrar_instituicao(nome, causa, endereco, id_plano, pedir_senha_nova())
        print(f"Instituição cadastrada. Login da empresa: {nome.strip().lower()}")

    def tornar_admin():
        contas.tornar_admin(perguntar("Login do usuário: "))
        print("Agora ele é administrador (vale a partir do próximo login dele).")

    def contar_usuarios():
        a = escolher(drive.todos_os_arquivos(), _rotulo_arquivo, "De qual arquivo?")
        con = conectar_como(s["login"], s["senha"], s["tipo"])  # o admin tem permissão de chamar
        try:
            mostrar(chamar_procedure("Conta_usuarios", (a["id_arquivo"],), con=con), "Conta_usuarios:")
        finally:
            con.close()

    _menu(f"Olá, {s['login']} (administrador)", {
        "1": "Visão geral dos arquivos", "2": "Visão geral dos usuários", "3": "Pedidos de suporte",
        "4": "Cadastrar plano", "5": "Cadastrar instituição", "6": "Tornar um usuário administrador",
        "7": "Contar usuários de um arquivo (Conta_usuarios)", "0": "Sair da conta"},
        {"1": lambda: com_conta_admin("SELECT * FROM vw_admin_arquivos", "Arquivos (visão vw_admin_arquivos):"),
         "2": lambda: com_conta_admin("SELECT * FROM vw_admin_usuarios", "Usuários (visão vw_admin_usuarios):"),
         "3": lambda: com_conta_admin(
             "SELECT S.dia, S.hora, U.login AS pediu, "
             "(SELECT A.nome FROM ARQUIVO A WHERE A.id_arquivo = S.id_arquivo) AS arquivo, "  # vazio se não houver
             "S.descricao FROM SUPORTE S INNER JOIN USUARIO U ON U.id_usuario = S.id_usuario "
             "ORDER BY S.dia, S.hora", "Pedidos de suporte:"),
         "4": cadastrar_plano, "5": cadastrar_instituicao, "6": tornar_admin, "7": contar_usuarios})


# ---------------- dono do banco (root) ----------------
def menu_root():
    if not senha_root_confere(getpass.getpass("Confirme a senha do MySQL (root): ")):
        print("Senha incorreta.")
        return

    def recriar():
        if confirmar("Isso APAGA tudo e recria com os exemplos. Continuar?"):
            criar_base()

    def ver_atividades():
        mostrar(consultar("SELECT A.nome AS arquivo, R.ultima_versao, R.acesso FROM ATIVIDADES_RECENTES R "
                          "INNER JOIN ARQUIVO A ON A.id_arquivo = R.id_arquivo ORDER BY A.nome"),
                "Tabela atividades_recentes (só o root vê):")

    def chavear():
        a = escolher(drive.todos_os_arquivos(), _rotulo_arquivo, "Qual arquivo?")
        mostrar(chamar_procedure("Chavear", (a["id_arquivo"],)), "Chavear:")

    def funcao_100_dias():
        a = escolher(drive.todos_os_arquivos(), _rotulo_arquivo, "Qual arquivo?")
        r = consultar("SELECT Passou_100_dias(%s) AS r", (a["id_arquivo"],))[0]["r"]
        print("Mais de 100 dias sem alteração?", "SIM" if r else "NÃO")

    _menu("Área do dono do banco", {
        "1": "Criar / recriar a base (com os exemplos)", "2": "Ver a tabela atividades_recentes",
        "3": "Verificar_atividades", "4": "Chavear um arquivo",
        "5": "Função: mais de 100 dias sem alteração?",
        "6": "Inserir / buscar / atualizar / remover em qualquer tabela", "0": "Voltar"},
        {"1": recriar, "2": ver_atividades,
         "3": lambda: mostrar(chamar_procedure("Verificar_atividades"), "Verificar_atividades:"),
         "4": chavear, "5": funcao_100_dias, "6": menu_crud})


def _ler_campos(msg):                                # lê "coluna=valor; coluna=valor"
    campos = {}
    for par in filter(None, (p.strip() for p in input(msg).split(";"))):
        coluna, _, valor = par.partition("=")        # separa no =
        campos[coluna.strip()] = valor.strip() or None  # vazio vira NULL
    return campos


def menu_crud():                                     # CRUD genérico da Parte 1 (root)
    def tabela():
        print("Tabelas:", ", ".join(crud.TABELAS))
        t = crud._conferir(perguntar("Tabela: "), [])  # valida
        print("Colunas:", ", ".join(crud.TABELAS[t]["pk"] + crud.TABELAS[t]["colunas"]))
        return t

    def inserir():
        t = tabela()
        print("Inserido. id =", crud.inserir(t, _ler_campos("Valores (ex.: nome=Plano X; duracao_meses=12): ")))

    def buscar():
        t = tabela()
        mostrar(crud.buscar(t, _ler_campos("Filtros (Enter = tudo; % = parte do texto): ")), f"{t}:")

    def atualizar():
        t = tabela()
        chave = _ler_campos(f"Chave ({', '.join(crud.TABELAS[t]['pk'])}): ")
        print("Linhas atualizadas:", crud.atualizar(t, chave, _ler_campos("Novos valores: ")))

    def remover():
        t = tabela()
        print("Linhas removidas:", crud.remover(t, _ler_campos(f"Chave ({', '.join(crud.TABELAS[t]['pk'])}): ")))

    _menu("CRUD de qualquer tabela", {"1": "Inserir", "2": "Buscar", "3": "Atualizar", "4": "Remover",
                                      "0": "Voltar"},
          {"1": inserir, "2": buscar, "3": atualizar, "4": remover})
