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


def add_evolucao(nome, texto):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO evolucoes (nome, texto) VALUES (?, ?)",
        (nome, texto)
    )
    conn.commit()
    conn.close()


def add_agenda(nome, data, horario, observacao=""):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO agenda (nome, data, horario, observacao) VALUES (?, ?, ?, ?)",
        (nome, data, horario, observacao)
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


def listar_evolucoes(nome):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, texto, created_at
        FROM evolucoes
        WHERE LOWER(nome) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 10
        """,
        (f"%{nome}%",)
    )
    dados = cur.fetchall()
    conn.close()
    return dados


def listar_agenda():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, nome, data, horario, observacao
        FROM agenda
        ORDER BY id DESC
        LIMIT 20
        """
    )
    dados = cur.fetchall()
    conn.close()
    return dados


def buscar_historico(nome):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT nome, observacoes, created_at
        FROM pacientes
        WHERE LOWER(nome) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"%{nome}%",)
    )
    paciente = cur.fetchone()

    cur.execute(
        """
        SELECT texto, created_at
        FROM evolucoes
        WHERE LOWER(nome) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 10
        """,
        (f"%{nome}%",)
    )
    evolucoes = cur.fetchall()

    cur.execute(
        """
        SELECT data, horario, observacao
        FROM agenda
        WHERE LOWER(nome) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 10
        """,
        (f"%{nome}%",)
    )
    agenda = cur.fetchall()

    conn.close()

    if not paciente and not evolucoes and not agenda:
        return ""

    texto = ""

    if paciente:
        texto += f"👤 Cadastro: {paciente[0]}\n"
        texto += f"📝 Observações: {paciente[1] or 'Sem observações'}\n"
        texto += f"📅 Criado em: {paciente[2]}\n\n"

    if evolucoes:
        texto += "🧾 Evoluções recentes:\n"
        for evo, data in evolucoes:
            texto += f"• {data}: {evo}\n"
        texto += "\n"

    if agenda:
        texto += "🗓 Agenda:\n"
        for data, horario, obs in agenda:
            texto += f"• {data} às {horario}: {obs or 'Sem observação'}\n"

    return texto.strip()


def gerar_relatorio(nome):
    historico = buscar_historico(nome)

    if not historico:
        return f"📄 Relatório de {nome}\n\nNenhum dado encontrado."

    return (
        f"📄 RELATÓRIO — {nome}\n\n"
        f"{historico}\n\n"
        "Síntese clínica inicial:\n"
        "O paciente apresenta registros de acompanhamento no sistema. "
        "Recomenda-se observar evolução da atenção, engajamento, resposta aos estímulos sonoros, "
        "comunicação, autonomia e participação nas atividades propostas.\n\n"
        "Observação: este relatório é uma base automática e deve ser revisado pelo profissional."
    )


def gerar_plano(nome):
    historico = buscar_historico(nome)

    if not historico:
        return f"🧩 Plano terapêutico de {nome}\n\nNenhum histórico encontrado."

    return (
        f"🧩 PLANO TERAPÊUTICO — {nome}\n\n"
        "Objetivos sugeridos:\n"
        "1. Estimular atenção compartilhada.\n"
        "2. Desenvolver atenção sustentada.\n"
        "3. Favorecer expressão comunicativa.\n"
        "4. Trabalhar percepção auditiva e resposta rítmica.\n"
        "5. Estimular interação social por meio da música.\n\n"
        "Estratégias:\n"
        "• Uso de instrumentos de fácil resposta sonora.\n"
        "• Atividades de imitação rítmica.\n"
        "• Canções de comando simples.\n"
        "• Alternância entre escuta, execução e pausa.\n"
        "• Reforço positivo durante participação funcional.\n\n"
        "Base considerada:\n"
        f"{historico[:1200]}\n\n"
        "Observação: plano automático inicial. Ajuste conforme avaliação clínica."
    )


def resumo_geral():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM pacientes")
    pacientes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alunos")
    alunos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tarefas WHERE status='pendente'")
    tarefas = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evolucoes")
    evolucoes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM agenda")
    agenda = cur.fetchone()[0]

    conn.close()

    return {
        "pacientes": pacientes,
        "alunos": alunos,
        "tarefas": tarefas,
        "evolucoes": evolucoes,
        "agenda": agenda,
    }
    
    def buscar_historico(nome):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT texto, created_at
        FROM evolucoes
        WHERE LOWER(nome) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 20
        """,
        (f"%{nome}%",)
    )

    dados = cur.fetchall()
    conn.close()

    if not dados:
        return ""

    texto = ""
    for evolucao, data in dados:
        texto += f"• {data}: {evolucao}\n"

    return texto.strip()