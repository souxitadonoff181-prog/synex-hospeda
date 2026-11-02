from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, secrets, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "synex_final_2026"
ARQUIVO_DADOS = "synex_dados.json"

# ==============================================
# BANCO DE DADOS
# ==============================================
DADOS_INICIAIS = {
    "usuarios": {"synex": {"senha_hash": hashlib.sha256("123".encode()).hexdigest(), "nivel": "admin"}},
    "chaves": {},
    "vendas": []
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

def criar_chave(produto, dias=30, comprador_id=None, comprador_nome=None):
    chave = "SYNEX-" + secrets.token_hex(3).upper() + "-" + secrets.token_hex(3).upper() + "-" + secrets.token_hex(3).upper()
    dado = {
        "chave": chave, "produto": produto, "dias": dias,
        "comprador_id": str(comprador_id) if comprador_id else None,
        "comprador_nome": comprador_nome,
        "criada_em": datetime.now().isoformat()
    }
    DADOS["chaves"][chave] = dado
    DADOS["vendas"].append(dado)
    salvar_dados()
    return chave

# ==============================================
# ESTILO PROFISSIONAL ESCURO
# ==============================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:Segoe UI,Inter,sans-serif}
:root{
    --fundo:#0a0a0f; --menu:#11111a; --card:#181825; --borda:#2a2a3c;
    --texto:#e4e4f7; --claro:#9ca3af; --destaque:#7c3aed; --sucesso:#10b981; --erro:#ef4444
}
body{background:var(--fundo);color:var(--texto);display:flex;min-height:100vh}
.menu{width:260px;background:var(--menu);border-right:1px solid var(--borda);position:fixed;height:100vh;padding-top:0}
.logo{padding:28px 24px;font-size:1.4rem;font-weight:700;background:linear-gradient(90deg,#7c3aed,#a78bfa);-webkit-background-clip:text;color:transparent;border-bottom:1px solid var(--borda)}
.menu a{display:flex;align-items:center;gap:10px;padding:14px 24px;color:var(--claro);text-decoration:none;margin:4px 12px;border-radius:8px;transition:.2s}
.menu a:hover,.menu a.ativo{background:rgba(124,58,237,.15);color:var(--texto);border-left:3px solid var(--destaque)}
.menu .sair{margin-top:40px;color:var(--erro)}
.conteudo{margin-left:260px;padding:32px 40px;flex:1}
.cabecalho{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:15px;border-bottom:1px solid var(--borda)}
.card{background:var(--card);border:1px solid var(--borda);border-radius:12px;padding:28px;margin-bottom:24px}
.card h3{margin-bottom:16px;color:#d4c1ff}
label{display:block;margin:10px 0 5px;color:var(--claro);font-size:.9rem}
input,pre{width:100%;padding:12px 16px;background:#1f1f2e;border:1px solid var(--borda);border-radius:8px;color:var(--texto);font-size:.95rem;margin-bottom:16px}
pre{font-family:Consolas,monospace;white-space:pre-wrap}
.btn{padding:12px 24px;border:none;border-radius:8px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;transition:.2s}
.btn-roxo{background:linear-gradient(90deg,#7c3aed,#6d28d9);color:white}
.btn-verde{background:var(--sucesso);color:white}
.aviso{background:rgba(245,158,11,.1);border-left:3px solid #f59e0b;padding:16px;margin:12px 0;border-radius:0 8px 8px 0}
.sucesso{background:rgba(16,185,129,.1);border-left:3px solid var(--sucesso);padding:16px;border-radius:0 8px 8px 0;margin:12px 0}
.login{max-width:440px;margin:100px auto}
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{padding:12px 8px;text-align:left;border-bottom:1px solid var(--borda)}
th{color:var(--claro);font-size:.9rem}
"""

def menu(aba):
    titulos = {
        "api": "📦 Entrega Automática — API",
        "uptime": "🔄 UptimeRobot — 24h Online",
        "vendas": "📋 Histórico de Vendas",
        "token": "🔑 Configurar Bot"
    }
    t = titulos.get(aba, "SYNEX")
    return """<div class="menu">
    <div class="logo">SYNEX</div>
    <a href="/api" """ + ("class='ativo'" if aba=="api" else "") + """>📦 Entrega API</a>
    <a href="/uptime" """ + ("class='ativo'" if aba=="uptime" else "") + """>🔄 UptimeRobot</a>
    <a href="/vendas" """ + ("class='ativo'" if aba=="vendas" else "") + """>📋 Vendas</a>
    <a href="/token" """ + ("class='ativo'" if aba=="token" else "") + """>🔑 Bot</a>
    <a href="/sair" class="sair">🚪 Sair</a>
    </div><div class="conteudo">
    <div class="cabecalho"><h2>""" + t + """</h2><span>👤 """ + str(session.get("usuario","")) + """</span></div>"""

# ==============================================
# ROTAS
# ==============================================
@app.route("/ping")
def ping(): return "✅ ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/api")
        return "<script>alert('Erro no login');history.back()</script>"
    return """<!DOCTYPE html><html><head><meta charset=UTF-8><style>"""+CSS+"""</style></head><body>
    <div class="login card"><h2 style="text-align:center;margin-bottom:24px">🔐 Entrar</h2>
    <form method=POST>
    <label>Usuário</label><input name=usuario required>
    <label>Senha</label><input type=password name=senha required>
    <button class="btn btn-roxo" style="width:100%;margin-top:8px">Entrar</button>
    </form><p style="text-align:center;margin-top:20px;color:var(--claro)">synex / 123</p></div></body></html>"""

@app.route("/sair")
def sair(): session.clear(); return redirect("/login")
@app.route("/")
def inicio(): return redirect("/login")

# API
@app.route("/api")
def pagina_api():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("api") + """
    <div class="card">
    <h3>📦 Endpoint</h3>
    <pre>POST """+dom+"""/api/gerar-chave
Content-Type: application/json

{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID no Discord",
  "comprador_nome": "Nome do Cliente"
}

Resposta:
{
  "sucesso": true,
  "chave": "SYNEX-XXXX-XXXX-XXXX",
  "produto": "Nome",
  "dias": 30,
  "comprador_id": "123",
  "comprador_nome": "Cliente"
}</pre>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText('"""+dom+"""/api/gerar-chave')">📋 Copiar URL</button>
    </div>
    <div class="card">
    <h3>💬 Exemplo no Bot</h3>
    <pre id=ex>import requests
DOMINIO = '"""+dom+"""'

resp = requests.post(DOMINIO+'/api/gerar-chave', json={
    'produto': 'VIP',
    'dias': 30,
    'comprador_id': str(ctx.author.id),
    'comprador_nome': str(ctx.author)
})
dados = resp.json()
if dados['sucesso']:
    await ctx.send(f'Chave: {dados["chave"]}')
    await ctx.send(f'Cliente: {dados["comprador_nome"]}')
    await ctx.send(f'Validade: {dados["dias"]} dias')</pre>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('ex').innerText)">📋 Copiar Exemplo</button>
    </div></div>"""

@app.route("/api/gerar-chave", methods=["POST"])
def api_chave():
    d = request.json
    chave = criar_chave(
        d.get("produto", "Produto"),
        int(d.get("dias", 30)),
        d.get("comprador_id"),
        d.get("comprador_nome")
    )
    return jsonify({
        "sucesso": True, "chave": chave,
        "produto": d.get("produto"),
        "dias": d.get("dias"),
        "comprador_id": d.get("comprador_id"),
        "comprador_nome": d.get("comprador_nome")
    })

# UPTIME
@app.route("/uptime")
def pagina_uptime():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("uptime") + """
    <div class="card">
    <h3>🔄 Manter Online 24h</h3>
    <input id=u value='"""+dom+"""/ping' readonly>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('u').value)">📋 Copiar</button>
    <div class="aviso">
    1. uptimerobot.com → criar conta<br>
    2. New Monitor → tipo HTTP(s)<br>
    3. Colar URL acima<br>
    4. Intervalo: 5 minutos<br>
    5. Salvar ✅ Pronto!
    </div></div></div>"""

# VENDAS
@app.route("/vendas")
def pagina_vendas():
    if "usuario" not in session: return redirect("/login")
    itens = list(reversed(DADOS["vendas"][-30:]))
    linhas = ""
    for v in itens:
        linhas += "<tr><td>"+str(v.get('produto','-'))+"</td><td><code>"+str(v.get('chave','-'))+"</code></td><td>"+str(v.get('comprador_nome','-'))+"</td><td>"+str(v.get('dias','-'))+" dias</td></tr>"
    return menu("vendas") + """
    <div class="card">
    <h3>📋 Chaves Geradas — Total: """+str(len(DADOS['vendas']))+"""</h3>
    <table><tr><th>Produto</th><th>Chave</th><th>Comprador</th><th>Validade</th></tr>"""+linhas+"""</table>
    </div></div>"""

# TOKEN
@app.route("/token", methods=["GET","POST"])
def pagina_token():
    if "usuario" not in session: return redirect("/login")
    t = request.form.get("token","") if request.method=="POST" else ""
    return menu("token") + """
    <div class="card">
    <h3>🔑 Token do Bot</h3>
    <form method=POST>
    <label>Cole o token do Discord abaixo:</label>
    <input type=password name=token placeholder="Token..." value='"""+t+"""'>
    <button class="btn btn-roxo">Salvar</button>
    </form>""" + ("<div class='sucesso'>✅ Token salvo! Coloque no código do bot e execute!</div>" if t else "") + """
    <div class="aviso">
    Pegar token: discord.com/developers → Bot → Reset Token<br>
    Ative as 3 opções em Privileged Gateway Intents
    </div></div></div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
