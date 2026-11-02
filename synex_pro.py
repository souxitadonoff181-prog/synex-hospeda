from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, uuid, secrets, hashlib

app = Flask(__name__)
app.secret_key = "synex_correto_sem_erro_2026"
ARQUIVO_DADOS = "synex_dados.json"

# ==============================================
# BANCO DE DADOS
# ==============================================
DADOS_INICIAIS = {
    "config": {"idioma": "pt"},
    "usuarios": {
        "synex": {
            "senha_hash": hashlib.sha256("123".encode()).hexdigest(),
            "nivel": "admin"
        }
    },
    "chaves": {},
    "vendas": []
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

# ==============================================
# FUNÇÕES
# ==============================================
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def verificar_senha(u, s):
    return u in DADOS["usuarios"] and DADOS["usuarios"][u]["senha_hash"] == hash_senha(s)

def criar_chave_sistema(nome, dias=30, comprador_id=None, origem="api"):
    chave = "SYNEX-" + secrets.token_hex(3).upper() + "-" + secrets.token_hex(3).upper() + "-" + secrets.token_hex(3).upper()
    DADOS["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "chave": chave,
        "dias": dias,
        "origem": origem,
        "status": "ativa",
        "comprador_id": str(comprador_id) if comprador_id else None
    }
    salvar_dados()
    return chave

# ==============================================
# ESTILOS
# ==============================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
:root{--p:#7928ca;--s:#10b981;--a:#f59e0b;--f:#05050a;--1:#12121f;--2:#1a1a2e;--t:#e0e0ff;--m:#8888aa;--e:#ef4444}
body{background:var(--f);color:var(--t);display:flex;min-height:100vh}
.sb{width:260px;background:var(--1);position:fixed;height:100vh;border-right:1px solid #2a2a4a;padding:20px 0}
.logo{padding:25px 20px;font-size:1.4rem;font-weight:800;background:linear-gradient(90deg,var(--p),var(--s));-webkit-background-clip:text;color:transparent}
.sb a{display:flex;align-items:center;gap:10px;padding:13px 20px;color:var(--m);text-decoration:none;margin:4px 10px;border-radius:8px;font-size:.95rem}
.sb a.ativo,.sb a:hover{background:rgba(121,40,202,.15);color:var(--t);border-left:3px solid var(--p)}
.sb .divisao{height:1px;background:#2a2a4a;margin:15px 20px}
.cont{margin-left:260px;padding:25px;flex:1}
.cab{display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;padding-bottom:15px;border-bottom:1px solid #2a2a4a}
.card{background:var(--1);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #2a2a4a}
.card h3{margin-bottom:18px;color:#d0b0ff}
.btn{padding:11px 20px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:5px;font-size:.95rem}
.btn.roxo{background:linear-gradient(90deg,var(--p),#9333ea);color:white}
.btn.verde{background:var(--s);color:white}
.btn.azul{background:#3b82f6;color:white}
input,textarea{width:100%;padding:13px;margin:8px 0 15px;background:var(--2);border:1px solid #2a2a4a;border-radius:8px;color:white;font-size:.95rem}
label{color:var(--m);font-weight:500;margin-top:10px;display:block}
pre{background:#0f172a;border:1px solid #3b82f6;border-radius:8px;padding:16px;margin:12px 0;overflow-x:auto;color:#e0e0ff;font-size:.85rem;white-space:pre-wrap}
.aviso{background:rgba(245,158,11,.1);border-left:3px solid var(--a);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}
.sucesso{background:rgba(16,185,129,.1);border-left:3px solid var(--s);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}
.login-box{max-width:420px;margin:100px auto}
"""

# ==============================================
# MENU
# ==============================================
def menu(aba):
    itens = {
        "bots": ("🤖 Gerador de Bots", "/bots"),
        "bot-online": ("🟢 Colocar Bot Online", "/bot-online"),
        "api": ("📦 Entrega Automática API", "/entrega-api"),
        "uptime": ("🔄 UptimeRobot 24h", "/uptimerobot")
    }
    titulo = itens.get(aba, ("SYNEX", "/"))[0]
    return """<div class="sb">
        <div class="logo">SYNEX</div>
        <a href="/bots" class='""" + ("ativo" if aba=="bots" else "") + """'>🤖 Gerador de Bots</a>
        <a href="/bot-online" class='""" + ("ativo" if aba=="bot-online" else "") + """'>🟢 Colocar Bot Online</a>
        <a href="/entrega-api" class='""" + ("ativo" if aba=="api" else "") + """'>📦 Entrega Automática API</a>
        <a href="/uptimerobot" class='""" + ("ativo" if aba=="uptime" else "") + """'>🔄 UptimeRobot 24h</a>
        <div class="divisao"></div>
        <a href="/sair" style="color:var(--e)">🚪 Sair</a>
    </div>
    <div class="cont">
        <div class="cab">
            <h2>""" + titulo + """</h2>
            <span style="color:var(--m)">👤 """ + str(session.get("usuario", "")) + """</span>
        </div>"""

# ==============================================
# ROTAS PÚBLICAS
# ==============================================
@app.route("/ping")
def ping():
    from datetime import datetime
    return "✅ SYNEX ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/bots")
        return "<script>alert('❌ Usuário ou senha incorretos');history.back()</script>"
    return """<!DOCTYPE html>
<html><head><meta charset=UTF-8><title>Login — SYNEX</title><style>""" + CSS + """</style></head>
<body>
<div class="login-box card">
<h2 style="text-align:center;margin-bottom:25px">🔐 Acesso SYNEX</h2>
<form method=POST>
<label>Usuário</label>
<input type=text name=usuario required>
<label>Senha</label>
<input type=password name=senha required>
<button class="btn roxo" style="width:100%">Entrar</button>
</form>
<p style="text-align:center;margin-top:15px;color:var(--m)">Padrão: synex / 123</p>
</div>
</body></html>"""

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/login")

# ==============================================
# GERADOR DE BOTS
# ==============================================
@app.route("/bots")
def pagina_bots():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    
    codigo_bot = 'import discord\nfrom discord.ext import commands\nimport requests\n\nDOMINIO = "' + dominio + '"\nPREFIXO = "!"\n\nbot = commands.Bot(command_prefix=PREFIXO, intents=discord.Intents.all())\n\n@bot.event\nasync def on_ready():\n    print("✅ BOT CONECTADO COMO:", bot.user)\n    await bot.change_presence(activity=discord.Game(name="Gerando chaves!"))\n\n@bot.command()\nasync def gerarchave(ctx, produto: str, dias: int=30):\n    resp = requests.post(DOMINIO + "/api/gerar-chave", json={"produto":produto,"dias":dias,"comprador_id":str(ctx.author.id)})\n    dados = resp.json()\n    if dados.get("sucesso"):\n        await ctx.send(f"✅ Chave: `{dados[\'chave\']}`")\n    else:\n        await ctx.send("❌ Erro ao gerar")\n\n@bot.command()\nasync def status(ctx):\n    await ctx.send("🟢 Estou ONLINE!")\n\nif __name__ == "__main__":\n    bot.run("SEU_TOKEN_AQUI")'
    
    return menu("bots") + """
    <div class="card">
        <h3>🤖 Código do Bot Discord</h3>
        <p>Copia tudo abaixo, salva como <code>bot.py</code> e troca o token:</p>
        <pre id="codigo">""" + codigo_bot + """</pre>
        <button class="btn verde" onclick="navigator.clipboard.writeText(document.getElementById('codigo').innerText)">📋 Copiar Código</button>
        <div class="aviso">
            <strong>📌 Usar:</strong><br>
            1. Instalar: <code>pip install discord requests</code><br>
            2. Trocar <code>SEU_TOKEN_AQUI</code> pelo token real<br>
            3. Rodar: <code>python bot.py</code>
        </div>
    </div>
    </div>"""

# ==============================================
# COLOCAR BOT ONLINE
# ==============================================
@app.route("/bot-online", methods=["GET", "POST"])
def pagina_bot_online():
    if "usuario" not in session:
        return redirect("/login")
    token = request.form.get("token", "") if request.method == "POST" else ""
    
    conteudo = menu("bot-online") + """
    <div class="card">
        <h3>🔑 Coloque o Token do Seu Bot</h3>
        <form method=POST>
            <label>Token do Bot</label>
            <input type=password name=token placeholder="Cole seu token aqui..." value='""" + token + """'>
            <button class="btn roxo">✅ Salvar</button>
        </form>"""
    if token:
        conteudo += '<div class="sucesso">✅ Token recebido! Agora coloque no código e execute!</div>'
    conteudo += """
        <div class="aviso">
            <strong>📌 Pegar o token:</strong><br>
            1. discord.com/developers/applications<br>
            2. Criar app → aba Bot → Reset Token → Copiar<br>
            3. Ativar as 3 Intents em Privileged Gateway Intents
        </div>
    </div>
    <div class="card">
        <h3>🚀 Passo a Passo</h3>
        <pre>pip install discord requests
# Salvar código como bot.py
# Trocar SEU_TOKEN_AQUI
python bot.py</pre>
    </div>
    </div>"""
    return conteudo

# ==============================================
# API DE ENTREGA
# ==============================================
@app.route("/entrega-api")
def pagina_api():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    return menu("api") + """
    <div class="card">
        <h3>📦 API de Entrega Automática</h3>
        <pre>POST -> """ + dominio + """/api/gerar-chave
Content-Type: application/json

{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Cliente"
}

Resposta:
{
  "sucesso": true,
  "chave": "SYNEX-XXXXX-XXXXX-XXXXX"
}</pre>
        <button class="btn verde" onclick="navigator.clipboard.writeText('""" + dominio + """/api/gerar-chave')">📋 Copiar URL da API</button>
    </div>
    </div>"""

@app.route("/api/gerar-chave", methods=["POST"])
def api_gerar_chave():
    d = request.json
    chave = criar_chave_sistema(
        d.get("produto", "Produto"),
        int(d.get("dias", 30)),
        d.get("comprador_id")
    )
    return jsonify({"sucesso": True, "chave": chave})

# ==============================================
# UPTIMEROBOT
# ==============================================
@app.route("/uptimerobot")
def pagina_uptime():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    return menu("uptime") + """
    <div class="card">
        <h3>🔄 Manter Bot 24h Online — UptimeRobot</h3>
        <p>Cadastre essa URL no UptimeRobot pra não cair:</p>
        <input type=text value='""" + dominio + """/ping' id=urlping readonly>
        <button class="btn verde" onclick="navigator.clipboard.writeText(document.getElementById('urlping').value)">📋 Copiar URL</button>
        <ul style="margin:15px 0 0 25px;color:var(--m)">
            <li>Criar conta em <strong>uptimerobot.com</strong> (grátis)</li>
            <li>New Monitor → tipo <strong>HTTP(s)</strong></li>
            <li>Colar a URL acima</li>
            <li>Intervalo: <strong>5 minutos</strong></li>
            <li>Salvar ✅ Pronto!</li>
        </ul>
    </div>
    </div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
