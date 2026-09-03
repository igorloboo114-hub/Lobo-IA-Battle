from fastapi import FastAPI
import sqlite3
import hashlib
import secrets

app = FastAPI(title="LOBO AI BATTLE")

BANCO = "lobo_ai_battle.db"


# ==========================================
# 🐺 BANCO DE DADOS
# ==========================================

def conectar():
    return sqlite3.connect(BANCO)


def criar_banco():

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    banco.commit()
    banco.close()


criar_banco()


# ==========================================
# 🔐 SENHA
# ==========================================

def criar_hash_senha(senha):

    salt = secrets.token_hex(16)

    hash_senha = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode(),
        salt.encode(),
        100000
    ).hex()

    return salt + ":" + hash_senha


def verificar_senha(senha, senha_salva):

    salt, hash_salvo = senha_salva.split(":")

    hash_nova = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode(),
        salt.encode(),
        100000
    ).hex()

    return secrets.compare_digest(hash_nova, hash_salvo)


# ==========================================
# 🎮 DADOS TEMPORÁRIOS DA PARTIDA
# ==========================================

salas = {}

jogadores_online = set()


# ==========================================
# 🏠 SERVIDOR
# ==========================================

@app.get("/")
def inicio():

    return {
        "jogo": "LOBO AI BATTLE",
        "servidor": "online",
        "mensagem": "🐺 Servidor funcionando!",
        "documentacao": "/docs"
    }


# ==========================================
# 📝 CADASTRO
# ==========================================

@app.post("/cadastro")
def cadastro(email: str, senha: str):

    email = email.strip().lower()

    if len(senha) < 8:
        return {
            "sucesso": False,
            "mensagem": "A senha precisa ter pelo menos 8 caracteres."
        }

    tem_numero = any(
        caractere.isdigit()
        for caractere in senha
    )

    tem_especial = any(
        caractere in "@#$!%&*"
        for caractere in senha
    )

    if not tem_numero:
        return {
            "sucesso": False,
            "mensagem": "A senha precisa ter pelo menos 1 número."
        }

    if not tem_especial:
        return {
            "sucesso": False,
            "mensagem": "A senha precisa ter pelo menos 1 caractere especial."
        }

    senha_hash = criar_hash_senha(senha)

    banco = conectar()
    cursor = banco.cursor()

    try:

        cursor.execute(
            "INSERT INTO jogadores (email, senha) VALUES (?, ?)",
            (email, senha_hash)
        )

        banco.commit()

    except sqlite3.IntegrityError:

        banco.close()

        return {
            "sucesso": False,
            "mensagem": "Esse email já está cadastrado."
        }

    banco.close()

    return {
        "sucesso": True,
        "mensagem": "🐺 Conta criada com sucesso!",
        "email": email
    }


# ==========================================
# 🔑 LOGIN
# ==========================================

@app.post("/login")
def login(email: str, senha: str):

    email = email.strip().lower()

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute(
        "SELECT id, senha FROM jogadores WHERE email = ?",
        (email,)
    )

    jogador = cursor.fetchone()

    banco.close()

    if jogador is None:

        return {
            "sucesso": False,
            "mensagem": "Email ou senha inválidos."
        }

    jogador_id = jogador[0]
    senha_salva = jogador[1]

    if not verificar_senha(senha, senha_salva):

        return {
            "sucesso": False,
            "mensagem": "Email ou senha inválidos."
        }

    jogadores_online.add(jogador_id)

    return {
        "sucesso": True,
        "mensagem": "🐺 Login realizado!",
        "jogador_id": jogador_id,
        "email": email
    }


# ==========================================
# 🚪 LOGOUT
# ==========================================

@app.post("/logout")
def logout(jogador_id: int):

    jogadores_online.discard(jogador_id)

    return {
        "sucesso": True,
        "mensagem": "Jogador saiu da conta."
    }


# ==========================================
# 👥 JOGADORES ONLINE
# ==========================================

@app.get("/jogadores-online")
def jogadores_online_lista():

    return {
        "total": len(jogadores_online),
        "jogadores": list(jogadores_online)
    }


# ==========================================
# 🎮 ENTRAR NA SALA
# ==========================================

@app.post("/sala/entrar")
def entrar_sala(jogador_id: int):

    if jogador_id not in jogadores_online:

        return {
            "sucesso": False,
            "mensagem": "Faça login primeiro."
        }

    sala_id = "sala_1"

    if sala_id not in salas:

        salas[sala_id] = {
            "jogadores": {},
            "iniciada": False
        }

    sala = salas[sala_id]

    if jogador_id in sala["jogadores"]:

        return {
            "sucesso": True,
            "mensagem": "Você já está na sala.",
            "sala": sala_id
        }

    sala["jogadores"][jogador_id] = {
        "vida": 100,
        "municao": 30
    }

    if len(sala["jogadores"]) >= 2:

        sala["iniciada"] = True

    return {
        "sucesso": True,
        "mensagem": "🐺 Você entrou na sala!",
        "sala": sala_id,
        "jogadores": len(sala["jogadores"]),
        "partida_iniciada": sala["iniciada"]
    }


# ==========================================
# 👥 VER SALA
# ==========================================

@app.get("/sala")
def ver_sala():

    sala = salas.get(
        "sala_1",
        {
            "jogadores": {},
            "iniciada": False
        }
    )

    return {
        "sala": "sala_1",
        "total_jogadores": len(sala["jogadores"]),
        "partida_iniciada": sala["iniciada"],
        "jogadores": list(sala["jogadores"].keys())
    }


# ==========================================
# 🔫 ATIRAR
# ==========================================

@app.post("/partida/atirar")
def atirar(jogador_id: int):

    sala = salas.get("sala_1")

    if not sala:

        return {
            "sucesso": False,
            "mensagem": "Sala não encontrada."
        }

    jogador = sala["jogadores"].get(jogador_id)

    if not jogador:

        return {
            "sucesso": False,
            "mensagem": "Você não está na sala."
        }

    if not sala["iniciada"]:

        return {
            "sucesso": False,
            "mensagem": "Aguardando outro jogador."
        }

    if jogador["municao"] <= 0:

        return {
            "sucesso": False,
            "mensagem": "❌ Sem munição!"
        }

    jogador["municao"] -= 1

    return {
        "sucesso": True,
        "mensagem": "🔫 Você atirou!",
        "municao": jogador["municao"]
    }


# ==========================================
# ❤️ STATUS
# ==========================================

@app.get("/partida/status/{jogador_id}")
def status(jogador_id: int):

    sala = salas.get("sala_1")

    if not sala:

        return {
            "sucesso": False,
            "mensagem": "Sala não encontrada."
        }

    jogador = sala["jogadores"].get(jogador_id)

    if not jogador:

        return {
            "sucesso": False,
            "mensagem": "Jogador não encontrado."
        }

    return {
        "sucesso": True,
        "vida": jogador["vida"],
        "municao": jogador["municao"]
    }


# ==========================================
# 💊 KIT MÉDICO
# ==========================================

@app.post("/partida/kit-medico")
def kit_medico(jogador_id: int):

    sala = salas.get("sala_1")

    if not sala:

        return {
            "sucesso": False,
            "mensagem": "Sala não encontrada."
        }

    jogador = sala["jogadores"].get(jogador_id)

    if not jogador:

        return {
            "sucesso": False,
            "mensagem": "Jogador não encontrado."
        }

    if jogador["vida"] >= 100:

        return {
            "sucesso": False,
            "mensagem": "❤️ Sua vida já está cheia."
        }

    jogador["vida"] += 20

    if jogador["vida"] > 100:
        jogador["vida"] = 100

    return {
        "sucesso": True,
        "mensagem": "💊 Kit médico usado!",
        "vida": jogador["vida"]
    }


# ==========================================
# 🚪 SAIR DA SALA
# ==========================================

@app.post("/sala/sair")
def sair_sala(jogador_id: int):

    sala = salas.get("sala_1")

    if not sala:

        return {
            "sucesso": False,
            "mensagem": "Sala não encontrada."
        }

    if jogador_id in sala["jogadores"]:

        del sala["jogadores"][jogador_id]

    if len(sala["jogadores"]) < 2:

        sala["iniciada"] = False

    return {
        "sucesso": True,
        "mensagem": "🚪 Você saiu da sala."
    }
