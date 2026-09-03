from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def inicio():
    return {
        "jogo": "LOBO AI BATTLE",
        "servidor": "online",
        "mensagem": "🐺 Servidor funcionando!"
    }
