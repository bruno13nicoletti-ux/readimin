from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Chave da sessão
app.secret_key = "ecohelper123"


# ==========================
# BANCO DE DADOS
# ==========================

def criar_banco():
    banco = sqlite3.connect("ecohelper.db")
    cursor = banco.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            pontos INTEGER DEFAULT 0,
            arvores INTEGER DEFAULT 0
        )
    """)

    banco.commit()
    banco.close()


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    mensagem = ""

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        banco = sqlite3.connect("ecohelper.db")
        cursor = banco.cursor()

        cursor.execute(
            "SELECT id, nome, senha FROM usuarios WHERE email = ?",
            (email,)
        )

        usuario = cursor.fetchone()

        banco.close()

        if usuario and check_password_hash(usuario[2], senha):

            session["usuario_id"] = usuario[0]
            session["nome"] = usuario[1]

            return redirect(url_for("inicio"))

        else:

            mensagem = "Email ou senha incorretos."

    return render_template(
        "login.html",
        mensagem=mensagem
    )


# ==========================
# CADASTRO
# ==========================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    mensagem = ""

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        senha_hash = generate_password_hash(senha)

        try:

            banco = sqlite3.connect("ecohelper.db")
            cursor = banco.cursor()

            cursor.execute("""
                INSERT INTO usuarios
                (nome, email, senha)
                VALUES (?, ?, ?)
            """, (nome, email, senha_hash))

            banco.commit()
            banco.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            mensagem = "Esse email já está cadastrado."

    return render_template(
        "cadastro.html",
        mensagem=mensagem
    )


# ==========================
# PÁGINA PRINCIPAL
# ==========================

@app.route("/", methods=["GET", "POST"])
def inicio():

    # Se não estiver logado
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    resultado = ""

    if request.method == "POST":

        opcao = request.form.get("opcao")

        banco = sqlite3.connect("ecohelper.db")
        cursor = banco.cursor()

        # ==========================
        # CARBONO
        # ==========================

        if opcao == "carbono":

            try:

                km = float(request.form.get("km", 0))

                if km < 0:

                    resultado = "Digite um número válido."

                else:

                    carbono = km * 0.192

                    resultado = (
                        f"Você percorre {km:.1f} km por semana. "
                        f"A emissão estimada é de "
                        f"{carbono:.2f} kg de CO₂ por semana."
                    )

                    cursor.execute("""
                        UPDATE usuarios
                        SET pontos = pontos + 5
                        WHERE id = ?
                    """, (usuario_id,))

            except ValueError:

                resultado = "Digite apenas números."

        # ==========================
        # RECICLAGEM
        # ==========================

        elif opcao == "reciclagem":

            lixo = request.form.get("lixo")

            dicas = {

                "papel":
                "Papel: mantenha limpo e seco e coloque na coleta seletiva.",

                "plastico":
                "Plástico: lave a embalagem quando necessário e coloque na coleta seletiva.",

                "vidro":
                "Vidro: separe dos outros materiais e descarte com cuidado.",

                "metal":
                "Metal: latas de alumínio e aço podem ser recicladas.",

                "organico":
                "Orgânico: restos de alimentos podem ser usados para compostagem."
            }

            resultado = dicas.get(
                lixo,
                "Material não encontrado."
            )

            cursor.execute("""
                UPDATE usuarios
                SET pontos = pontos + 2
                WHERE id = ?
            """, (usuario_id,))

        # ==========================
        # ENERGIA
        # ==========================

        elif opcao == "energia":

            resultado = (
                "Dica de economia: desligue as luzes ao sair "
                "do ambiente e retire aparelhos da tomada "
                "quando não estiverem sendo utilizados."
            )

            cursor.execute("""
                UPDATE usuarios
                SET pontos = pontos + 2
                WHERE id = ?
            """, (usuario_id,))

        # ==========================
        # ÁRVORE
        # ==========================

        elif opcao == "arvore":

            arvore = request.form.get("arvore")

            if arvore:

                cursor.execute("""
                    UPDATE usuarios
                    SET pontos = pontos + 20,
                        arvores = arvores + 1
                    WHERE id = ?
                """, (usuario_id,))

                resultado = (
                    f"Árvore '{arvore}' registrada! "
                    "Você ganhou 20 pontos."
                )

            else:

                resultado = "Digite o nome da árvore."

        # ==========================
        # PONTOS
        # ==========================

        elif opcao == "pontos":

            cursor.execute("""
                SELECT pontos, arvores
                FROM usuarios
                WHERE id = ?
            """, (usuario_id,))

            dados = cursor.fetchone()

            resultado = (
                f"Você possui {dados[0]} pontos ecológicos "
                f"e registrou {dados[1]} árvore(s)."
            )

        banco.commit()
        banco.close()

    # Buscar dados atualizados
    banco = sqlite3.connect("ecohelper.db")
    cursor = banco.cursor()

    cursor.execute("""
        SELECT nome, pontos, arvores
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    usuario = cursor.fetchone()

    banco.close()

    return render_template(
        "index.html",
        resultado=resultado,
        nome=usuario[0],
        pontos=usuario[1],
        arvores=usuario[2]
    )


# ==========================
# SAIR
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==========================
# INICIAR
# ==========================

if __name__ == "__main__":

    criar_banco()

    app.run(debug=True)