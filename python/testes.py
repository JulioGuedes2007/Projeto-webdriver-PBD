# Webdriver — teste automático (recria a base, testa tudo e recria de novo). Rodar: python3.15 testes.py
# Explicações no README.md

from datetime import date

import contas
import drive
from conexao import (conectar_como, consultar, executar, chamar_procedure, criar_base,
                     pedir_senha_root)

SENHA = "12345678"                                   # senha das contas de exemplo
TIPO = {"bruno": "usuario", "carla": "usuario", "diego": "usuario",  # perfil de cada conta
        "admin": "admin", "unicap": "empresa", "cafeteria": "empresa"}  # (decide o SET ROLE)
resultados = []                                      # True/False de cada teste


def ok(nome, condicao, detalhe=""):                  # registra e imprime um teste
    resultados.append(bool(condicao))
    print(("  OK      " if condicao else "  FALHOU  ") + nome + (f"  [{detalhe}]" if detalhe else ""))


def bloqueado(nome, funcao, trecho):                 # espera que a ação dê erro
    try:
        funcao()
        ok(nome, False, "deveria ter sido bloqueado")
    except Exception as e:
        msg = " ".join(str(e).split())
        ok(nome, trecho.lower() in msg.lower(), msg[:110])  # erro certo = OK


def tentar(nome, funcao):                            # roda; se der erro, marca FALHOU
    try:
        return funcao()
    except Exception as e:
        ok(nome, False, " ".join(str(e).split())[:160])
        return None


def como(conta, sql, alterar=False, senha=SENHA, com_papel=True):  # roda SQL com a conta de uma pessoa
    con = conectar_como(conta, senha, TIPO[conta] if com_papel else None)  # SET ROLE do perfil
    try:
        cur = con.cursor()
        cur.execute(sql)
        if alterar:                                  # INSERT/UPDATE/DELETE
            con.commit()
            return cur.rowcount
        return cur.column_names, cur.fetchall()      # SELECT
    finally:
        con.close()


def um(sql, params=()):                              # primeiro valor de um SELECT (root)
    return list(consultar(sql, params)[0].values())[0]


def main():
    pedir_senha_root()
    print("\n== TESTE AUTOMÁTICO (a base é recriada antes e depois) ==")
    criar_base()
    ids = {l["login"]: l["id_usuario"] for l in consultar("SELECT id_usuario, login FROM USUARIO")}

    print("\n[Cadastro e login]")
    for conta, tipo in [("bruno", "usuario"), ("admin", "admin"), ("unicap", "empresa")]:
        s = tentar(f"login de {conta}", lambda c=conta: contas.entrar(c, SENHA))  # c=conta: usa o valor desta volta
        if s:
            ok(f"{conta} entra como {tipo}", s["tipo"] == tipo)
    bloqueado("senha errada é recusada", lambda: contas.entrar("bruno", "errada123"), "incorretos")
    novo = tentar("cadastrar usuário", lambda: contas.cadastrar_usuario("testecad", "t@t.com", "senhaTeste1", 1))
    if novo:
        hash_ok = um("SELECT senha FROM USUARIO WHERE id_usuario = %s", (novo,)) == contas.hash_senha("senhaTeste1")
        ok("cadastro guarda a senha como hash", hash_ok)
        s = tentar("login do cadastrado", lambda: contas.entrar("testecad", "senhaTeste1"))
        ok("cadastrado entra com a senha que escolheu", bool(s) and s["tipo"] == "usuario")
    bloqueado("login repetido é recusado", lambda: contas.cadastrar_usuario("bruno", "x@x.com", SENHA), "em uso")
    tentar("tornar admin", lambda: contas.tornar_admin("testecad"))
    s = tentar("login do novo admin", lambda: contas.entrar("testecad", "senhaTeste1"))
    ok("usuário promovido entra como admin", bool(s) and s["tipo"] == "admin")
    tentar("cadastrar empresa", lambda: contas.cadastrar_instituicao("cafeteria", None, None, None, SENHA))
    r = tentar("cafeteria vê funcionários", lambda: como("cafeteria", "SELECT * FROM vw_empresa_usuarios"))
    ok("empresa nova não vê ninguém da UNICAP", bool(r) and len(r[1]) == 0)

    print("\n[Tabela atividades_recentes]")
    n_arq, n_atv = um("SELECT COUNT(*) FROM ARQUIVO"), um("SELECT COUNT(*) FROM ATIVIDADES_RECENTES")
    ok("tem uma linha para cada arquivo", n_arq == n_atv, f"{n_atv} de {n_arq}")

    print("\n[Visões e PapelUsuario — conta 'carla']")
    esperado = {l["nome"] for l in drive.arquivos_acessiveis(ids["carla"])}
    r = tentar("carla vê vw_meus_arquivos", lambda: como("carla", "SELECT * FROM vw_meus_arquivos"))
    if r:
        cols, linhas = r
        vistos = {l[cols.index("nome")] for l in linhas}
        ok("carla vê só os arquivos a que tem acesso", vistos == esperado, ", ".join(sorted(vistos)))
        ok("a visão não mostra ids", not any(c.lower().startswith("id") for c in cols))
    bloqueado("sem SET ROLE, carla não vê nem a visão", lambda: como(
        "carla", "SELECT * FROM webdriver.vw_meus_arquivos", com_papel=False), "denied")
    bloqueado("carla NÃO lê a tabela ARQUIVO direto", lambda: como("carla", "SELECT * FROM ARQUIVO"), "denied")
    bloqueado("carla NÃO lê atividades_recentes", lambda: como("carla", "SELECT * FROM ATIVIDADES_RECENTES"), "denied")
    n = tentar("carla atualiza pela visão", lambda: como(
        "carla", "UPDATE vw_meus_arquivos SET localizacao = '/carla' WHERE nome = 'relatorio.docx'", alterar=True))
    ok("carla atualiza arquivo dela pela visão", n == 1, f"{n} linha")
    n = tentar("carla não altera de outro", lambda: como(
        "carla", "UPDATE vw_meus_arquivos SET localizacao = '/x' WHERE nome = 'trabalho_bd.pdf'", alterar=True))
    ok("carla não consegue alterar arquivo sem acesso", n == 0, f"{n} linha")
    n = tentar("carla insere pela visão", lambda: como(
        "carla", "INSERT INTO vw_meus_arquivos (nome, tipo, tamanho_bytes, url) "
                 "VALUES ('anotacoes.pdf', 'pdf', 1000, 'https://drive.exemplo/f/c1')", alterar=True))
    if n is not None:
        dono = consultar("SELECT id_dono FROM ARQUIVO WHERE url = 'https://drive.exemplo/f/c1'")
        ok("carla insere pela visão e vira a dona", bool(dono) and dono[0]["id_dono"] == ids["carla"])
    bloqueado("carla NÃO deleta pela visão", lambda: como(
        "carla", "DELETE FROM vw_meus_arquivos WHERE nome = 'relatorio.docx'", alterar=True), "denied")
    bloqueado("carla NÃO altera o histórico", lambda: como(
        "carla", "UPDATE vw_historico_operacoes SET tipo_operacao = 'remover'", alterar=True), "denied")

    print("\n[PapelEmpresa — conta 'unicap']")
    usu = {l["login"] for l in consultar("SELECT U.login FROM USUARIO U INNER JOIN INSTITUICAO I "
                                         "ON I.id_instituicao = U.id_instituicao WHERE I.nome = 'UNICAP'")}
    r = tentar("unicap vê funcionários", lambda: como("unicap", "SELECT login FROM vw_empresa_usuarios"))
    if r:
        ok("unicap vê só os funcionários dela", {l[0] for l in r[1]} == usu, ", ".join(sorted(usu)))
    bloqueado("unicap NÃO altera (só visualiza)", lambda: como(
        "unicap", "UPDATE vw_empresa_usuarios SET email = 'x@x.com'", alterar=True), "denied")
    bloqueado("unicap NÃO lê a tabela USUARIO direto", lambda: como("unicap", "SELECT * FROM USUARIO"), "denied")

    print("\n[PapelAdm — conta 'admin']")
    r = tentar("admin lê toda a base", lambda: como("admin", "SELECT COUNT(*) FROM USUARIO"))
    ok("admin lê toda a base", bool(r) and r[1][0][0] == um("SELECT COUNT(*) FROM USUARIO"))
    n = tentar("admin insere", lambda: como(
        "admin", "INSERT INTO PLANO (nome, duracao_meses, data_aquisicao, espaco_por_usuario_gb) "
                 "VALUES ('Teste', 1, '2026-11-01', 1)", alterar=True))
    n = tentar("admin deleta", lambda: como("admin", "DELETE FROM PLANO WHERE nome = 'Teste'", alterar=True))
    ok("admin insere e deleta", n == 1)
    bloqueado("admin NÃO lê atividades_recentes (só root)", lambda: como(
        "admin", "SELECT * FROM ATIVIDADES_RECENTES"), "denied")

    print("\n[Função e procedures]")
    ok("Passou_100_dias(1) = não (alterado há pouco)", um("SELECT Passou_100_dias(1)") == 0)
    executar("UPDATE ARQUIVO SET data_ultima_modificacao = NOW() - INTERVAL 200 DAY WHERE id_arquivo = 1")
    ok("Passou_100_dias(1) = sim (simulando 200 dias)", um("SELECT Passou_100_dias(1)") == 1)
    tentar("Verificar_atividades", lambda: chamar_procedure("Verificar_atividades"))
    acesso = {l["id_arquivo"]: l["acesso"] for l in consultar("SELECT id_arquivo, acesso FROM ATIVIDADES_RECENTES")}
    ok("Verificar_atividades: arquivo 1 virou 'nao prioritario'", acesso.get(1) == "nao prioritario")
    r = tentar("Chavear inexistente", lambda: chamar_procedure("Chavear", (999,)))
    ok("Chavear(999): avisa que não encontrou", bool(r) and "aviso" in r[0])
    tentar("Chavear", lambda: chamar_procedure("Chavear", (1,)))
    ok("Chavear(1): virou 'prioritario'", um("SELECT acesso FROM ATIVIDADES_RECENTES WHERE id_arquivo = 1") == "prioritario")
    esperado_2 = 1 + um("SELECT COUNT(*) FROM COMPARTILHAMENTO WHERE id_arquivo = 2")
    r = tentar("Conta_usuarios", lambda: chamar_procedure("Conta_usuarios", (2,)))
    ok("Conta_usuarios(2): dono + compartilhados", bool(r) and r[0]["total_usuarios"] == esperado_2)
    n = tentar("Remover_acessos", lambda: drive.remover_acessos(ids["bruno"], 2))
    ok("Remover_acessos(2): só o dono ficou",
       chamar_procedure("Conta_usuarios", (2,))[0]["total_usuarios"] == 1, f"{n} acessos removidos")

    print("\n[Triggers e regras do drive]")
    tentar("compartilhar", lambda: drive.compartilhar(ids["bruno"], 1, ids["carla"]))
    ok("Atualizar_acesso: arquivo 1 ficou 'compartilhado'",
       um("SELECT permissoes_acesso FROM ARQUIVO WHERE id_arquivo = 1") == "compartilhado")
    bloqueado("Safe_security bloqueia .exe", lambda: drive.carregar_arquivo(
        ids["bruno"], "instalador.exe", "exe", 1000, "https://drive.exemplo/f/e1"), "Safe_security")
    executar("UPDATE PLANO SET espaco_por_usuario_gb = 0.01 WHERE id_plano = 1")  # plano da UNICAP vira 0,01 GB
    bloqueado("Limite_espaco bloqueia 20 MB num plano de 0,01 GB", lambda: drive.carregar_arquivo(
        ids["bruno"], "backup.zip", "zip", 20 * 1024 ** 2, "https://drive.exemplo/f/b1"), "Limite_espaco")
    executar("UPDATE PLANO SET espaco_por_usuario_gb = 50 WHERE id_plano = 1")    # volta a 50 GB
    novo = tentar("upload normal", lambda: drive.carregar_arquivo(
        ids["bruno"], "resumo.pdf", "pdf", 5000, "https://drive.exemplo/f/r1"))
    if novo:
        linha = consultar("SELECT ultima_versao, acesso FROM ATIVIDADES_RECENTES WHERE id_arquivo = %s", (novo,))
        ok("Registrar_operacao: upload entrou na atividades_recentes",
           bool(linha) and str(linha[0]["ultima_versao"]) == date.today().isoformat())
    bloqueado("quem não tem acesso não edita", lambda: drive.editar_arquivo(
        ids["diego"], 1, {"nome": "x.pdf"}, "tentativa"), "acesso")
    bloqueado("quem não é dono não remove", lambda: drive.remover_arquivo(ids["carla"], 1), "dono")
    tentar("comentar", lambda: drive.comentar(ids["carla"], 1, "Teste de comentário"))
    ok("comentário gravado", any(c["conteudo"] == "Teste de comentário" for c in drive.comentarios(1)))
    tentar("pedir suporte", lambda: drive.pedir_suporte(ids["diego"], "Teste de suporte"))
    ok("pedido de suporte gravado", um("SELECT COUNT(*) FROM SUPORTE WHERE descricao = 'Teste de suporte'") == 1)

    print("\n[Remover sem CASCADE: apaga o que depende antes]")
    if novo:
        n = tentar("dono remove", lambda: drive.remover_arquivo(ids["bruno"], novo))
        ok("bruno remove resumo.pdf (com operação, versão e atividade)", n == 1)
        ok("nada ficou apontando para o arquivo removido",
           um("SELECT COUNT(*) FROM OPERACAO WHERE id_arquivo = %s", (novo,)) == 0
           and um("SELECT COUNT(*) FROM ATIVIDADES_RECENTES WHERE id_arquivo = %s", (novo,)) == 0)
    n = tentar("diego remove o vídeo", lambda: drive.remover_arquivo(ids["diego"], 4))
    ok("o pedido de suporte sobre o vídeo continua, sem arquivo",
       n == 1 and um("SELECT COUNT(*) FROM SUPORTE WHERE id_usuario = %s AND id_arquivo IS NULL",
                     (ids["diego"],)) == 2)  # o do vídeo + o de teste

    total, certos = len(resultados), sum(resultados)
    print(f"\nRESULTADO: {certos} de {total} testes OK")
    print("\nRecriando a base para deixar só os exemplos...")
    criar_base()


if __name__ == "__main__":
    main()
