import os
import threading
from flask import Flask
from dotenv import load_dotenv
import discord
from discord.ext import commands

# ==============================================
# CONFIGURAÇÃO
# ==============================================
load_dotenv()
app = Flask(__name__)
TOKEN = os.getenv("DISCORD_TOKEN")
bot_online = False

# ==============================================
# INICIALIZAÇÃO MÍNIMA — SÓ CONEXÃO
# ==============================================
intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    global bot_online
    bot_online = True
    print(f"✅ BOT CONECTADO — {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Comandos carregados")
    except Exception as e:
        print(f"Status: {e}")

def rodar_bot():
    if not TOKEN:
        print("❌ Token não encontrado no .env")
        return
    bot.run(TOKEN)

# ==============================================
# PÁGINA DO SITE
# ==============================================
@app.route("/")
def painel():
    status = "🟢 ONLINE" if bot_online else "🔴 DESLIGADO"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Synex — Controle do Bot</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box;font-family:system-ui}}
            body{{background:#0f1014;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}}
            .card{{background:#1a1b23;padding:40px;border-radius:16px;text-align:center;min-width:320px}}
            h1{{font-size:22px;margin-bottom:10px}}
            .status{{font-size:18px;margin:20px 0;padding:12px;border-radius:10px;background:#272933}}
            .ligar{{background:#23a559;color:#fff;border:none;padding:12px 30px;border-radius:10px;font-size:16px;cursor:pointer}}
            .ligar:hover{{background:#1d8c4c}}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Synex Store — Bot</h1>
            <div class="status">{status}</div>
            <form action="/ligar" method="post">
                <button class="ligar" type="submit">🔌 Ligar Bot</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/ligar", methods=["POST"])
def ligar():
    global bot_online
    if not bot_online:
        threading.Thread(target=rodar_bot, daemon=True).start()
    return "/ ligado"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
