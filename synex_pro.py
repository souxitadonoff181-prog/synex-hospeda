from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, secrets, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "synex_final_2026"
ARQUIVO_DADOS = "dados.json"

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

def cabecalho():
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SYNEX</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
        body{background:#05050a;color:#e5e5ff;display:flex;min-height:100vh}
        .menu{width:250px;background:#0f0f1a;position:fixed;height:100vh;border-right:1px solid #23233b;padding-top:20px}
        .menu h1{padding:0 24px 25px;font-size:1.4rem;color:#a78bfa}
        .menu a{display:block;padding:14px 24px;color:#8888aa;text-decoration:none;margin:5px 15px;border-radius:8px}
        .menu a.ativo,.menu a:hover{background:rgba(124,58,237,0.15);color:#fff;border-left:3px solid #7c3aed}
        .menu .sair{margin-top:40px;color:#ef4444}
        .conteudo{margin-left:250px;padding:30px;width:100%}
        .card{background:#12121f;border:1px solid #23233b;border-radius:12px;padding:25px;margin-bottom:20px}
        h2{margin-bottom:20px;color:#a78bfa}
        h3{margin-bottom:15px;color:#d4c1ff}
        label{display:block;margin:12px 0 5px;color:#8888aa}
        input,pre{width:100%;padding:12px;background:#1a1a2e;border:1px solid #23233b;border-radius:8px;color:#fff;margin-bottom:15px;font-size:14px}
        pre{padding:15px;white-space:pre-wrap}
        button{padding:10px 20px;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
        .btn-roxo{background:linear-gradient(90deg,#7c3aed,#6d28d9);color:white}
        .btn-verde{background:#10b981;color:white}
        .aviso{background:rgba(245,158,11,0.1);border-left:3px solid #f59e0b;padding:15px;margin:10px 0;border-radius:0 8px 8px 0}
        .sucesso{background:rgba(16,185,129,0.1);border-left:3px solid #10b981;padding:15px;border-radius:0 8px 8px 0;margin:10px 0}
        table{width:100%;border-collapse:collapse;margin-top:10px}
        th,td{padding:12px 10px;text-align:left;border-bottom:1px solid #23233b}
        th{color:#8888aa}
        .login{max-width:420px;margin:80px auto}
    </style>
</head>
<body>"""

def rodape():
    return "</body></html>"

def menu_esquerdo(aba):
    itens = [
        ("api", "📦 Entrega API", "/api"),
        ("bot", "🟢 Bot Online", "/bot"),
        ("uptime", "🔄 UptimeRobot", "/uptime"),
        ("vendas", "📋 Histórico de Vendas", "/vendas"),
    ]
    html = '<div class="menu"><h1>SYNEX</h1>'
    for a, texto, link in itens:
        html += f'<a href="{link}" class="{"ativo" if a==aba else ""}">{texto}</a>'
    html += '<a href="/sair" class="sair">🚪 Sair</a></div><div class="conteudo">'
    return html

@app.route("/ping")
def ping(): return "✅ ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/api")
        return "<script>alert('Erro no login');history.back()</script>"
    return cabecalho() + """
    <div class="login card">
        <h2 style="text-align:center">🔐 Entrar</h2>
        <form method="POST">
            <label>Usuário</label>
            <input name="usuario" required>
            <label>Senha</label>
            <input type="password" name="senha" required>
            <button class="btn-roxo" style="width:100%;margin-top:10px">Entrar</button>
        </form>
        <p style="text-align:center;margin-top:20px;color:#8888aa">synex / 123</p>
    </div>
    """ + rodape()

@app.route("/sair")
def sair(): session.clear(); return redirect("/login")
@app.route("/")
def inicio(): return redirect("/login")

@app.route("/api")
def pagina_api():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return cabecalho() + menu_esquerdo("api") + f"""
    <h2>📦 Entrega Automática — API</h2>
    <div class="card">
        <h3>Endpoint</h3>
        <pre>POST {dom}/api/gerar-chave
Content-Type: application/json

{{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Cliente",
  "comprador_nome": "Nome do Cliente"
}}

Resposta:
{{
  "sucesso": true,
  "chave": "SYNEX-XXXX-XXXX-XXXX",
  "produto": "Nome",
  "dias": 30,
  "comprador_id": "123",
  "comprador_nome": "Cliente"
}}</pre>
        <button class="btn-verde" onclick="navigator.clipboard.writeText('{dom}/api/gerar-chave')">📋 Copiar URL</button>
    </div>
    <div class="card">
        <h3>Código no Bot</h3>
        <pre id="cod">import requests

DOMINIO = "{dom}"

resp = requests.post(DOMINIO+"/api/gerar-chave", json={{
    "produto": "VIP",
    "dias": 30,
    "comprador_id": str(ctx.author.id),
    "comprador_nome": str(ctx.author)
}})
dados = resp.json()
if dados["sucesso"]:
    await ctx.send(f"Chave: {{dados['chave']}}")
    await ctx.send(f"Cliente: {{dados['comprador_nome']}}")
    await ctx.send(f"Validade: {{dados['dias']}} dias")</pre>
        <button class="btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('cod').innerText)">📋 Copiar</button>
    </div>
    </div>
    """ + rodape()

@app.route("/api/gerar-chave", methods=["POST"])
def api_gerar():
    d = request.json
    chave = criar_chave(d.get("produto"), int(d.get("dias",30)), d.get("comprador_id"), d.get("comprador_nome"))
    return jsonify({"sucesso":True,"chave":chave,"produto":d.get("produto"),"dias":d.get("dias"),"comprador_id":d.get("comprador_id"),"comprador_nome":d.get("comprador_nome")})

@app.route("/bot", methods=["GET","POST"])
def pagina_bot():
    if "usuario" not in session: return redirect("/login")
    t = request.form.get("token","") if request.method=="POST" else ""
    resp = cabecalho() + menu_esquerdo("bot") + """
    <h2>🟢 Bot Online</h2>
    <div class="card">
        <h3>Configurar Token</h3>
        <form method="POST">
            <label>Token do Discord</label>
            <input type="password" name="token" placeholder="Cole seu token aqui..." value="""+t+""">
            <button class="btn-roxo">Salvar</button>
        </form>"""
    if t: resp += '<div class="sucesso">✅ Salvo! Coloque no código e ligue o bot.</div>'
    resp += """
        <div class="aviso">
            Pegar token: discord.com/developers → Bot → Reset Token<br>
            Ative as 3 opções em Privileged Gateway Intents
        </div>
    </div>
    </div>
    """ + rodape()
    return resp

@app.route("/uptime")
def pagina_uptime():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return cabecalho() + menu_esquerdo("uptime") + f"""
    <h2>🔄 UptimeRobot — 24h</h2>
    <div class="card">
        <h3>URL de Monitoramento</h3>
        <input id="u" value="{dom}/ping" readonly>
        <button class="btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('u').value)">📋 Copiar</button>
        <div class="aviso">
            1. uptimerobot.com → conta grátis<br>
            2. New Monitor → HTTP(s)<br>
            3. Colar URL acima<br>
            4. Intervalo: 5 min<br>
            5. Salvar ✅
        </div>
    </div>
    </div>
    """ + rodape()

@app.route("/vendas")
def pagina_vendas():
    if "usuario" not in session: return redirect("/login")
    itens = list(reversed(DADOS["vendas"][-30:]))
    linhas = ""
    for v in itens:
        linhas += f"<tr><td>{v.get('produto','-')}</td><td><code>{v.get('chave','-')}</code></td><td>{v.get('comprador_nome','-')}</td><td>{v.get('dias','-')} dias</td></tr>"
    return cabecalho() + menu_esquerdo("vendas") + f"""
    <h2>📋 Histórico de Vendas — {len(DADOS['vendas'])} chaves</h2>
    <div class="card">
        <table>
            <tr><th>Produto</th><th>Chave</th><th>Comprador</th><th>Validade</th></tr>
            {linhas}
        </table>
    </div>
    </div>
    """ + rodape()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
