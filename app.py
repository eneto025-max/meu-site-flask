from flask import Flask, render_template, request

app = Flask(__name__)

# rotas


@app.route("/", methods=["GET", "POST"])
def inicio():

    nome = None

    if request.method == "POST":
        nome = request.form["nome"]

    return render_template("index.html", nome=nome)


@app.route("/sobre")
def sobre():
    return render_template("sobre.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
