from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, secrets, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "simples_funciona_2026"
ARQUIVO_DADOS = "dados.json"

DADOS_INICIAIS = {
    "usuarios": {"synex": {"senha_hash": hashlib.sha256("123".encode()).hexdigest(), "nivel": "admin"}},
    "chaves": {}
}

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k in DADOS_INICIAIS:
                if k not in d: d[k] = DADOS_INICIAIS[k]
            return d
    return DADOS_INICIAIS.copy()

def salvar_dados():
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(DADOS, f, ensure_ascii=False, indent=4)

DADOS = carregar_dados()

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def verificar_senha(u, s): return u in DADOS["usuarios"] and DADOS["usuarios"][u]["senha_hash"] == hash_senha(s)

def criar_chave(nome, dias=30, comprador_id=None):
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    DADOS["chaves"][chave] = {
        "nome": nome, "chave": chave, "dias": dias,
        "comprador_id": str(comprador_id) if comprador_id else None,
        "criada_em": datetime.now().isoformat()
    }
    salvar_dados()
    return chave

CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,sans-serif}
:root{--p:#7928ca;--s:#10b981;--f:#05050a;--1:#12121f;--2:#1a1a2e;--t:#e0e0ff;--m:#8888aa;--e:#ef4444}
body{background:var(--f);color:var(--t);display:flex;min-height:100vh}
.menu{width:240px;background:var(--1);position:fixed;height:100vh;border-right:1px solid #2a2a4a;padding-top:20px}
.menu h1{padding:0 20px 20px;color:var(--p);font-size:1.3rem}
.menu a{display:block;padding:12px 20px;color:var(--m);text-decoration:none;margin:4px 10px;border-radius:8px}
.menu a.ativo,.menu a:hover{background:rgba(121,40,202,.15);color:var(--t)}
.conteudo{margin-left:240px;padding:30px;flex:1}
.card{background:var(--1);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #2a2a4a}
h2{color:#d0b0ff;margin-bottom:15px}
button,input{padding:10px 14px;border-radius:6px;border:none;font-size:.95rem;margin:5px 0}
input{background:var(--2);border:1px solid #2a2a4a;color:white;width:100%}
.btn-roxo{background:linear-gradient(90deg,var(--p),#9333ea);color:white}
.btn-verde{background:var(--s);color:white}
pre{background:#0f172a;border:1px solid #3b82f6;border-radius:8px;padding:15px;overflow-x:auto;color:#e0e0ff;margin:10px 0}
.aviso{background:rgba(245,158,11,.1);border-left:3px solid #f59e0b;padding:12px;margin:10px 0}
.login{max-width:400px;margin:80px auto}
"""

def menu(aba):
    return f"""<div class="menu">
    <h1>SYNEX</h1>
    <a href="/bots" {'class="ativo"' if aba=="bots" else ""}>🤖 Gerador de Bots</a>
    <a href="/token" {'class="ativo"' if aba=="token" else ""}>🔑 Colocar Bot Online</a>
    <a href="/api" {'class="ativo"' if aba=="api" else ""}>📦 Entrega API</a>
    <a href="/uptime" {'class="ativo"' if aba=="uptime" else ""}>🔄 UptimeRobot</a>
    <a href="/sair" style="color:var(--e);margin-top:20px">🚪 Sair</a>
    </div><div class="conteudo">"""

@app.route("/ping")
def ping(): return "✅ ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/bots")
        return "<script>alert('Erro no login');history.back()</script>"
    return f"""<!DOCTYPE html><html><head><meta charset=UTF-8><style>{CSS}</style></head><body>
    <div class="login card"><h2 style="text-align:center">🔐 Entrar</h2>
    <form method=POST>
    <label>Usuário</label><input name=usuario required>
    <label>Senha</label><input type=password name=senha required>
    <button class="btn-roxo" style="width:100%;margin-top:10px">Entrar</button>
    </form><p style="text-align:center;color:var(--m);margin-top:10px">synex / 123</p></div></body></html>"""

@app.route("/sair")
def sair(): session.clear(); return redirect("/login")

@app.route("/")
def inicio(): return redirect("/login")

@app.route("/bots")
def pagina_bots():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    cod = f'''import discord
from discord.ext import commands
import requests

DOMINIO = "{dom}"
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"✅ ONLINE: {{bot.user}}")

@bot.command()
async def gerarchave(ctx, produto: str, dias: int=30):
    r = requests.post(DOMINIO+"/api/gerar-chave", json={{"produto":produto,"dias":dias,"comprador_id":str(ctx.author.id)}})
    d = r.json()
    if d["sucesso"]:
        await ctx.send(f"✅ Sua chave: `{{d['chave']}}`")
    else:
        await ctx.send("❌ Erro")

@bot.command()
async def status(ctx):
    await ctx.send("🟢 Estou ONLINE!")

bot.run("SEU_TOKEN_AQUI")'''
    return menu("bots") + f"""
    <h2>🤖 Gerador de Bots</h2>
    <p>Copia o código abaixo:</p>
    <pre id=c>{cod}</pre>
    <button class="btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('c').innerText)">📋 Copiar</button>
    <div class="aviso">
    1. Instale: <code>pip install discord requests</code><br>
    2. Troque <code>SEU_TOKEN_AQUI</code> pelo token real<br>
    3. Salve como bot.py → execute: <code>python bot.py</code>
    </div></div>"""

@app.route("/token", methods=["GET","POST"])
def pagina_token():
    if "usuario" not in session: return redirect("/login")
    t = request.form.get("token","") if request.method=="POST" else ""
    return menu("token") + f"""
    <h2>🔑 Colocar Bot Online</h2>
    <form method=POST>
    <label>Cole seu token aqui:</label>
    <input type=password name=token placeholder="Token do Discord" value="{t}">
    <button class="btn-roxo">Salvar</button>
    </form>
    {f'<p style="color:var(--s)">✅ Salvo! Coloque no código e rode!</p>' if t else ''}
    <div class="aviso">
    Pegar token: discord.com/developers → Bot → Reset Token<br>
    Ative as 3 opções em Privileged Gateway Intents
    </div></div>"""

@app.route("/api")
def pagina_api():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("api") + f"""
    <h2>📦 Entrega Automática — API</h2>
    <pre>POST {dom}/api/gerar-chave
Content-Type: application/json

{{"produto":"Nome","dias":30,"comprador_id":"123"}}

Resposta:
{{"sucesso":true,"chave":"SYNEX-XXXX-XXXX-XXXX"}}</pre>
    <button class="btn-verde" onclick="navigator.clipboard.writeText('{dom}/api/gerar-chave')">📋 Copiar URL</button>
    </div>"""

@app.route("/api/gerar-chave", methods=["POST"])
def api_chave():
    d = request.json
    c = criar_chave(d.get("produto","Produto"), int(d.get("dias",30)), d.get("comprador_id"))
    return jsonify({"sucesso":True,"chave":c})

@app.route("/uptime")
def pagina_uptime():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("uptime") + f"""
    <h2>🔄 UptimeRobot — 24h Online</h2>
    <input id=u value="{dom}/ping" readonly>
    <button class="btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('u').value)">📋 Copiar</button>
    <ul style="margin:15px 0 0 25px;color:var(--m)">
    <li>Acesse uptimerobot.com → crie conta grátis</li>
    <li>Add New Monitor → tipo HTTP(s)</li>
    <li>Cole a URL acima</li>
    <li>Intervalo: 5 minutos</li>
    <li>Salvar ✅ Pronto!</li>
    </ul></div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
