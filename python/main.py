# Webdriver — programa principal. Rodar dentro da pasta python/:  python3.15 main.py
# Explicações e navegação completa no README.md

from areas import tela_cadastro, tela_login, menu_root
from conexao import pedir_senha_root


def main():
    print("===== WEBDRIVER — drive de arquivos para instituições =====")
    print("O programa usa o MySQL. Primeiro, a senha do dono do banco (root).")
    while True:                                      # repete até a senha do root dar certo
        try:
            pedir_senha_root()
            break
        except Exception as erro:
            print(f"ERRO: {erro}")

    opcoes = {"1": "Entrar (login e senha)", "2": "Cadastrar novo usuário",
              "3": "Área do dono do banco (root)", "0": "Sair"}
    acoes = {"1": tela_login, "2": tela_cadastro, "3": menu_root}
    while True:                                      # menu inicial
        print("\n===== WEBDRIVER =====")
        for k, v in opcoes.items():
            print(f" {k} - {v}")
        op = input("Opção: ").strip()
        if op == "0":
            print("Até logo!")
            break
        if op not in acoes:
            print("Opção inválida.")
            continue
        try:
            acoes[op]()                              # abre a tela escolhida
        except Exception as erro:                    # mostra o erro e volta ao menu
            print(f"ERRO: {erro}")


if __name__ == "__main__":                           # só roda se o arquivo for executado
    main()
