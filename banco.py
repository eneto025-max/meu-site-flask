import sqlite3


def conectar():
    banco = sqlite3.connect("banco.db")
    return banco


banco = conectar()

cursor = banco.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    senha TEXT NOT NULL,
    saldo REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    valor REAL NOT NULL,
    data_hora TEXT NOT NULL,
    FOREIGN KEY (conta_id) REFERENCES contas(id)
)
""")

banco.commit()
banco.close()
