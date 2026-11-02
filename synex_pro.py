from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, uuid, secrets, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "synex_completo_sem_erro_2026"
ARQUIVO_DADOS = "synex_dados.json"

DADOS_INICIAIS = {
    "config": {"idioma": "pt"},
    "usuarios": {
        "synex": {
            "senha_hash": hashlib.sha256("123".encode()).hexdigest(),
            "nivel": "admin",
            "criado_em": datetime.now().isoformat()
        }
    },
    "chaves": {},
    "vendas": {}
}

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
            for k in DADOS_INICIAIS:
                if k not in dados:
                    dados[k] = DADOS_INICIAIS[k]
            return dados
    return DADOS_INICIAIS.copy()

def salvar_dados():
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(DADOS, f, ensure_ascii=False, indent=4)

DADOS = carregar_dados()

def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def verificar_senha(u, s):
    return u in DADOS["usuarios"] and DADOS["usuarios"][u]["senha_hash"] == hash_senha(s)

def criar_chave_sistema(nome, dias=30, comprador_id=None, origem="bot"):
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    DADOS["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "chave": chave,
        "dias": dias,
        "expira_em": (datetime.now() + timedelta(days=dias)).isoformat(),
        "origem": origem,
        "status": "ativa",
        "criada_em": datetime.now().isoformat(),
        "comprador_id": str(comprador_id) if comprador_id else None
    }
    salvar_dados()
    return chave

CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
:root{--p:#7928ca;--s:#10b981;--a:#f59e0b;--f:#05050a;--1:#12121f;--2:#1a1a2e;--t:#e0e0ff;--m:#8888aa}
body{background:var(--f);color:var(--t);min-height:100vh;padding:20px}
.container{max-width:900px;margin:0 auto}
h1,h2,h3{margin-bottom:20px;color:#d0b0ff}
.card{background:var(--1);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #2a2a4a}
pre{background:#0f172a;border:1px solid #3b82f6;border-radius:8px;padding:15px;overflow-x:auto;color:#e0e0ff;margin:10px 0}
input{width:100%;padding:12px;margin:8px 0;background:var(--2);border:1px solid #2a2a4a;border-radius:6px;color:white}
button{padding:10px 20px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;margin:5px 0}
.btn-roxo{background:linear-gradient(90deg,var(--p),#9333ea);color:white}
.btn-verde{background:var(--s);color:white}
.aviso{background:rgba(245,158,11,.1);border-left:3px solid var(--a);padding:12px;border-radius:0 6px 6px 0;margin:10px 0}
.login-box{max-width:400px;margin:80px auto}
"""

@app.route("/ping")
def ping():
    return "pong ✅ online"

@app.route("/api/gerar-chave", methods=["POST"])
def api_gerar_chave():
    d = request.json
    chave = criar_chave_sistema(
        d.get("produto", "Produto"),
        int(d.get("dias", 30)),
        d.get("comprador_id"),
        "bot_proprio"
    )
    return jsonify({"sucesso": True, "chave": chave})

@app.route("/api/criar-chave-auth", methods=["POST"])
def api_criar_chave_auth():
    d = request.json
    if not verificar_senha(d.get("usuario"), d.get("senha")):
        return jsonify({"sucesso": False, "erro": "login invalido"}), 401
    chave = criar_chave_sistema(
        d.get("nome", "Chave"),
        int(d.get("dias", 30)),
        origem="painel"
    )
    return jsonify({"sucesso": True, "chave": chave})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/")
        return """<script>alert('Usuário ou senha errados');history.back()</script>"""
    return f"""<!DOCTYPE html>
<html><head><meta charset=UTF-8><title>Login</title><style>{CSS}</style></head>
<body>
<div class="login-box card">
<h2 style="text-align:center">🔐 Entrar</h2>
<form method=POST>
<label>Usuário</label>
<input type=text name=usuario required>
<label>Senha</label>
<input type=password name=senha required>
<button class=btn-roxo style=width:100%;margin-top:10px>Entrar</button>
</form>
<p style="text-align:center;margin-top:15px;color:var(--m)">Padrão: synex / 123</p>
</div>
</body></html>"""

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/login")

@app.route("/")
def painel():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    return f"""<!DOCTYPE html>
<html><head><meta charset=UTF-8><title>SYNEX — Gerador de Chaves</title><style>{CSS}</style></head>
<body>
<div class="container">
<h1>🚀 SYNEX — Gerador de Chaves</h1>
<p style="margin-bottom:20px">Olá, <strong>{session['usuario']}</strong> — <a href="/sair" style="color:var(--a)">Sair</a></p>

<div class="card">
<h2>🤖 Gerador de Bot — Código Pronto</h2>
<p>Copia e cola no seu bot do Discord:</p>
<pre>import discord
from discord.ext import commands
import requests
import os

DOMINIO = "{dominio}"
USUARIO_SISTEMA = "synex"
SENHA_SISTEMA = "123"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"✅ Bot {{bot.user}} está ONLINE e funcionando!")

@bot.command()
async def gerarchave(ctx, nome_produto: str, dias: int = 30):
    resposta = requests.post(
        DOMINIO + "/api/gerar-chave",
        json={{"produto": nome_produto, "dias": dias, "comprador_id": ctx.author.id}}
    )
    dados = resposta.json()
    if dados["sucesso"]:
        await ctx.send(f"✅ Chave gerada:\\n`{{dados['chave']}}`")
    else:
        await ctx.send("❌ Erro ao criar chave")

@bot.command()
async def statusbot(ctx):
    await ctx.send("✅ Estou ONLINE e funcionando perfeitamente!")

bot.run("SEU_TOKEN_AQUI")</pre>
<div class="aviso">⚠️ Troque <code>SEU_TOKEN_AQUI</code> pelo token real do seu bot no Discord</div>
</div>

<div class="card">
<h2>🔄 Manter Bot 24h Online — UptimeRobot</h2>
<p>Para o bot não cair, cadastre essa URL no UptimeRobot:</p>
<input type="text" value="{dominio}/ping" id=urlping readonly>
<button class=btn-verde onclick="navigator.clipboard.writeText(document.getElementById('urlping').value)">📋 Copiar URL</button>
<ul style="margin:15px 0 0 25px">
<li>Cria conta no <strong>UptimeRobot.com</strong> (grátis)</li>
<li>Clica em <strong>Add New Monitor</strong></li>
<li>Escolhe <strong>HTTP(s)</strong></li>
<li>Cola a URL acima</li>
<li>Intervalo: <strong>5 minutos</strong></li>
<li>Salva ✅ Pronto, vai ficar online sempre</li>
</ul>
</div>

<div class="card">
<h2>🔌 Entrega Automática — API para Seu Bot</h2>
<p>Seu bot chama essa API direto para gerar chaves automaticamente:</p>
<pre>POST → {dominio}/api/gerar-chave
Content-Type: application/json

{{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Cliente"
}}

Resposta:
{{
  "sucesso": true,
  "chave": "SYNEX-XXXXX-XXXXX-XXXXX"
}}</pre>
<p style="margin-top:10px">Use isso no seu sistema de entrega automática e chaves vão ser criadas na hora!</p>
</div>

</div>
</body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
