from database.db import connect


def add_paciente(nome, observacoes=""):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pacientes (nome, observacoes) VALUES (?, ?)",
        (nome, observacoes)
    )
    conn.commit()
    conn.close()


def add_aluno(nome, observacoes=""):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO alunos (nome, observacoes) VALUES (?, ?)",
        (nome, observacoes)
    )
    conn.commit()
    conn.close()


def add_tarefa(user_id, tarefa):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tarefas (user_id, tarefa) VALUES (?, ?)",
        (str(user_id), tarefa)
    )
    conn.commit()
    conn.close()


def listar_pacientes():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, observacoes FROM pacientes ORDER BY id DESC LIMIT 20")
    dados = cur.fetchall()
    conn.close()
    return dados


def listar_alunos():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, observacoes FROM alunos ORDER BY id DESC LIMIT 20")
    dados = cur.fetchall()
    conn.close()
    return dados


def listar_tarefas():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, tarefa, status FROM tarefas ORDER BY id DESC LIMIT 20")
    dados = cur.fetchall()
    conn.close()
    return dados


def resumo_geral():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM pacientes")
    pacientes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alunos")
    alunos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tarefas WHERE status='pendente'")
    tarefas = cur.fetchone()[0]

    conn.close()

    return {
        "pacientes": pacientes,
        "alunos": alunos,
        "tarefas": tarefas
    }