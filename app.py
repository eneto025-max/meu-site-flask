from flask import Flask, render_template, request, session, redirect
from banco import conectar
from datetime import datetime


app = Flask(__name__)

app.secret_key = "chave-secreta-banco-python"

# rotas


@app.route("/", methods=["GET", "POST"])
def inicio():

    nome = None

    if request.method == "POST":
        nome = request.form["nome"]

    return render_template("index.html", nome=nome)


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"]
        senha = request.form["senha"]

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute(
            "SELECT id FROM contas WHERE nome = ?",
            (nome,)
        )

        conta_existente = cursor.fetchone()

        if conta_existente:
            banco.close()

            return render_template(
                "cadastro.html",
                erro="❌ Esse nome já está sendo usado!"
            )

        cursor.execute(
            "INSERT INTO contas (nome, senha) VALUES (?, ?)",
            (nome, senha)
        )

        banco.commit()
        banco.close()

        return render_template(
            "sucesso.html",
            nome=nome
        )

    return render_template("cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        nome = request.form["nome"]
        senha = request.form["senha"]

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute(
            "SELECT * FROM contas WHERE nome = ? AND senha = ?",
            (nome, senha)
        )

        conta = cursor.fetchone()

        banco.close()

        if conta:

            session["usuario_id"] = conta[0]
            session["usuario_nome"] = conta[1]

            saldo = conta[3]

            return render_template(
                "conta.html",
                nome=conta[1],
                saldo=saldo
            )

        else:
            return render_template(
                "login.html",
                erro="Nome ou senha incorretos!"
            )

    return render_template("login.html")


@app.route("/deposito", methods=["GET", "POST"])
def deposito():

    if "usuario_id" not in session:
        return "Você precisa fazer login."

    if request.method == "POST":

        valor = float(request.form["valor"])

        banco = conectar()
        cursor = banco.cursor()

        cursor.execute(
            "UPDATE contas SET saldo = saldo + ? WHERE id = ?",
            (valor, session["usuario_id"])
        )

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO historico (conta_id, tipo, valor, data_hora)
            VALUES (?, ?, ?, ?)
            """,
            (session["usuario_id"], "Depósito", valor, data_hora)
        )

        banco.commit()
        banco.close()

        return redirect("/conta")

    return render_template("deposito.html")


@app.route("/saque", methods=["GET", "POST"])
def saque():

    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        valor = float(request.form["valor"])

        banco = conectar()
        cursor = banco.cursor()

        # Buscar o saldo atual
        cursor.execute(
            "SELECT saldo FROM contas WHERE id = ?",
            (session["usuario_id"],)
        )

        saldo = cursor.fetchone()[0]

        # Verificar se tem saldo suficiente
        if valor > saldo:
            banco.close()
            return render_template(
                "transferencia.html",
                erro="❌ Saldo insuficiente!"
            )

        # Retirar o dinheiro
        cursor.execute(
            "UPDATE contas SET saldo = saldo - ? WHERE id = ?",
            (valor, session["usuario_id"])
        )

        # Registrar no histórico
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO historico (conta_id, tipo, valor, data_hora)
            VALUES (?, ?, ?, ?)
            """,
            (session["usuario_id"], "Saque", valor, data_hora)
        )

        banco.commit()
        banco.close()

        return redirect("/conta")

    return render_template("saque.html")


@app.route("/transferencia", methods=["GET", "POST"])
def transferencia():

    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        destinatario = request.form["destinatario"]
        valor = float(request.form["valor"])

        banco = conectar()
        cursor = banco.cursor()

        # Buscar a conta de destino
        cursor.execute(
            "SELECT id, saldo FROM contas WHERE nome = ?",
            (destinatario,)
        )

        conta_destino = cursor.fetchone()

        if not conta_destino:
            banco.close()
            return render_template(
                "transferencia.html",
                erro="❌ Conta do destinatário não encontrada!"
            )

        # Buscar o saldo de quem está transferindo
        cursor.execute(
            "SELECT saldo FROM contas WHERE id = ?",
            (session["usuario_id"],)
        )

        saldo = cursor.fetchone()[0]

        # Verificar saldo
        if valor > saldo:
            banco.close()
            return render_template(
                "transferencia.html",
                erro="❌ Saldo insuficiente!"
            )

        # Retirar dinheiro da conta de origem
        cursor.execute(
            "UPDATE contas SET saldo = saldo - ? WHERE id = ?",
            (valor, session["usuario_id"])
        )

        # Adicionar dinheiro na conta de destino
        cursor.execute(
            "UPDATE contas SET saldo = saldo + ? WHERE id = ?",
            (valor, conta_destino[0])
        )

        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Histórico de quem enviou
        cursor.execute(
            """
            INSERT INTO historico (conta_id, tipo, valor, data_hora)
            VALUES (?, ?, ?, ?)
            """,
            (
                session["usuario_id"],
                f"Transferência para {destinatario}",
                valor,
                data_hora
            )
        )

        # Histórico de quem recebeu
        cursor.execute(
            """
            INSERT INTO historico (conta_id, tipo, valor, data_hora)
            VALUES (?, ?, ?, ?)
            """,
            (
                conta_destino[0],
                f"Transferência recebida de {session['usuario_nome']}",
                valor,
                data_hora
            )
        )

        banco.commit()
        banco.close()

        return redirect("/conta")

    return render_template("transferencia.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/historico")
def historico():

    if "usuario_id" not in session:
        return redirect("/login")

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        """
        SELECT tipo, valor, data_hora
        FROM historico
        WHERE conta_id = ?
        ORDER BY id DESC
        """,
        (session["usuario_id"],)
    )

    movimentacoes = cursor.fetchall()

    banco.close()

    return render_template(
        "historico.html",
        movimentacoes=movimentacoes
    )


@app.route("/conta")
def conta():

    if "usuario_id" not in session:
        return redirect("/login")

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "SELECT nome, saldo FROM contas WHERE id = ?",
        (session["usuario_id"],)
    )

    usuario = cursor.fetchone()

    banco.close()

    return render_template(
        "conta.html",
        nome=usuario[0],
        saldo=usuario[1]
    )


@app.route("/admin")
def admin():

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "SELECT id, nome, saldo FROM contas"
    )

    contas = cursor.fetchall()

    banco.close()

    return render_template(
        "admin.html",
        contas=contas
    )


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
