from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, secrets, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "synex_bonito_2026"
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
# ESTILO — TEMA ESCURO BONITO
# ==============================================
CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
:root{
    --fundo:#05050a; --menu:#0f0f1a; --card:#12121f; --borda:#23233b;
    --texto:#e5e5ff; --cinza:#8888aa; --roxo:#7c3aed; --roxo-escuro:#6d28d9;
    --verde:#10b981; --destaque:#a78bfa; --vermelho:#ef4444
}
body{background:var(--fundo);color:var(--texto);display:flex;min-height:100vh}

/* MENU LATERAL */
.menu-lateral{
    width:250px;background:var(--menu);position:fixed;height:100vh;border-right:1px solid var(--borda);
    padding:0;display:flex;flex-direction:column
}
.logo{
    padding:26px 24px;font-size:1.4rem;font-weight:700;
    background:linear-gradient(90deg,var(--roxo),var(--destaque));
    -webkit-background-clip:text;color:transparent;
    border-bottom:1px solid var(--borda)
}
.menu-lateral a{
    display:flex;align-items:center;gap:10px;padding:14px 24px;color:var(--cinza);
    text-decoration:none;margin:4px 12px;border-radius:8px;font-size:.95rem;transition:.2s
}
.menu-lateral a:hover,.menu-lateral a.ativo{
    background:rgba(124,58,237,.15);color:var(--texto);border-left:3px solid var(--roxo)
}
.menu-lateral .sair{margin-top:auto;margin-bottom:30px;color:var(--vermelho)}
.menu-lateral .sair:hover{background:rgba(239,68,68,.1);border-left-color:var(--vermelho);color:var(--vermelho)}

/* CONTEÚDO */
.conteudo{margin-left:250px;padding:30px;flex:1}
.cabecalho{
    display:flex;justify-content:space-between;align-items:center;
    margin-bottom:30px;padding-bottom:15px;border-bottom:1px solid var(--borda)
}
.cabecalho h2{font-size:1.4rem;color:var(--destaque)}
.usuario{color:var(--cinza);font-size:.9rem}

/* CARTÕES */
.card{background:var(--card);border:1px solid var(--borda);border-radius:12px;padding:25px;margin-bottom:20px}
.card h3{margin-bottom:15px;color:var(--destaque);font-size:1.1rem}

/* FORMULÁRIOS E CÓDIGO */
label{display:block;margin:10px 0 5px;color:var(--cinza);font-size:.9rem}
input,pre{
    width:100%;padding:12px 15px;background:#1a1a2e;border:1px solid var(--borda);
    border-radius:8px;color:var(--texto);font-size:.95rem;margin-bottom:15px
}
pre{font-family:'Consolas',monospace;white-space:pre-wrap;line-height:1.5}

/* BOTÕES */
.btn{
    padding:11px 22px;border:none;border-radius:8px;font-weight:600;cursor:pointer;
    text-decoration:none;display:inline-block;font-size:.95rem;transition:.2s
}
.btn-roxo{background:linear-gradient(90deg,var(--roxo),var(--roxo-escuro));color:white}
.btn-roxo:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(124,58,237,.25)}
.btn-verde{background:var(--verde);color:white}
.btn-verde:hover{background:#059669;transform:translateY(-1px)}

/* AVISOS */
.aviso{background:rgba(245,158,11,.1);border-left:3px solid #f59e0b;padding:14px;margin:12px 0;border-radius:0 8px 8px 0}
.sucesso{background:rgba(16,185,129,.1);border-left:3px solid var(--verde);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}

/* LOGIN */
.caixa-login{max-width:420px;margin:100px auto}
.caixa-login h2{text-align:center;margin-bottom:25px}

/* TABELA */
table{width:100%;border-collapse:collapse;margin-top:10px}
th,td{padding:12px 10px;text-align:left;border-bottom:1px solid var(--borda)}
th{color:var(--cinza);font-size:.9rem}
"""

# ==============================================
# MENU LATERAL
# ==============================================
def menu(aba):
    itens = {
        "api": ("📦 Entrega Automática — API", "/api"),
        "bot": ("🟢 Bot Online", "/bot"),
        "uptime": ("🔄 UptimeRobot", "/uptime"),
        "vendas": ("📋 Histórico de Vendas", "/vendas")
    }
    titulo, _ = itens.get(aba, ("SYNEX", "/"))
    
    html = '<div class="menu-lateral"><div class="logo">SYNEX</div>'
    for a, (t, l) in itens.items():
        html += f'<a href="{l}" class="{"ativo" if a==aba else ""}">{t}</a>'
    html += '<a href="/sair" class="sair">🚪 Sair</a></div>'
    html += f'<div class="conteudo"><div class="cabecalho"><h2>{titulo}</h2><span class="usuario">👤 {session.get("usuario","")}</span></div>'
    return html

# ==============================================
# ROTAS
# ==============================================
@app.route("/ping")
def ping(): return "✅ SYNEX ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/api")
        return "<script>alert('❌ Usuário ou senha incorretos');history.back()</script>"
    return f"""<!DOCTYPE html><html><head><meta charset=UTF-8><style>{CSS}</style></head><body>
    <div class="caixa-login card"><h2>🔐 Acesso SYNEX</h2>
    <form method=POST>
    <label>Usuário</label><input name=usuario required>
    <label>Senha</label><input type=password name=senha required>
    <button class="btn btn-roxo" style="width:100%;margin-top:8px">Entrar</button>
    </form><p style="text-align:center;margin-top:20px;color:var(--cinza)">synex / 123</p></div></body></html>"""

@app.route("/sair")
def sair(): session.clear(); return redirect("/login")
@app.route("/")
def inicio(): return redirect("/login")

# API
@app.route("/api")
def pagina_api():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("api") + f"""
    <div class="card">
    <h3>📦 Usar no Bot</h3>
    <p style="color:var(--cinza);margin-bottom:15px">O bot envia os dados e recebe a chave na hora.</p>
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
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText('{dom}/api/gerar-chave')">📋 Copiar URL</button>
    </div>
    <div class="card">
    <h3>💬 Código no Bot</h3>
    <pre id=cod>import requests

DOMINIO = "{dom}"

@bot.command()
async def comprar(ctx, produto: str, dias: int=30):
    resp = requests.post(DOMINIO+"/api/gerar-chave", json={{
        "produto": produto,
        "dias": dias,
        "comprador_id": str(ctx.author.id),
        "comprador_nome": str(ctx.author)
    }})
    dados = resp.json()
    if dados["sucesso"]:
        await ctx.send(f"✅ Chave: {{dados['chave']}}")
        await ctx.send(f"👤 Cliente: {{dados['comprador_nome']}}")
        await ctx.send(f"⏳ Validade: {{dados['dias']}} dias")</pre>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('cod').innerText)">📋 Copiar Código</button>
    </div></div>"""

@app.route("/api/gerar-chave", methods=["POST"])
def api_gerar():
    d = request.json
    chave = criar_chave(
        d.get("produto", "Produto"),
        int(d.get("dias", 30)),
        d.get("comprador_id"),
        d.get("comprador_nome")
    )
    return jsonify({
        "sucesso": True, "chave": chave,
        "produto": d.get("produto"), "dias": d.get("dias"),
        "comprador_id": d.get("comprador_id"), "comprador_nome": d.get("comprador_nome")
    })

# BOT ONLINE
@app.route("/bot", methods=["GET","POST"])
def pagina_bot():
    if "usuario" not in session: return redirect("/login")
    token = request.form.get("token","") if request.method=="POST" else ""
    resp = menu("bot") + f"""
    <div class="card">
    <h3>🟢 Colocar Bot Online</h3>
    <form method=POST>
    <label>Token do Bot Discord</label>
    <input type=password name=token placeholder="Cole seu token aqui..." value="{token}">
    <button class="btn btn-roxo">Salvar Token</button>
    </form>"""
    if token:
        resp += '<div class="sucesso">✅ Token salvo! Coloque no código e execute.</div>'
    resp += """
    <div class="aviso">
    <strong>📌 Pegar o token:</strong><br>
    1. discord.com/developers/applications<br>
    2. Criar App → aba Bot → Reset Token<br>
    3. Ativar as 3 opções em Privileged Gateway Intents<br>
    4. Trocar SEU_TOKEN_AQUI no código pelo token real
    </div>
    </div></div>"""
    return resp

# UPTIME
@app.route("/uptime")
def pagina_uptime():
    if "usuario" not in session: return redirect("/login")
    dom = request.host_url.rstrip("/")
    return menu("uptime") + f"""
    <div class="card">
    <h3>🔄 Manter 24h Online</h3>
    <p style="color:var(--cinza);margin-bottom:15px">Cadastre no UptimeRobot pra não cair.</p>
    <input id=urlping value="{dom}/ping" readonly>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('urlping').value)">📋 Copiar URL</button>
    <div class="aviso">
    1. uptimerobot.com → criar conta grátis<br>
    2. New Monitor → tipo HTTP(s)<br>
    3. Colar a URL acima<br>
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
        linhas += f"<tr><td>{v.get('produto','-')}</td><td><code>{v.get('chave','-')}</code></td><td>{v.get('comprador_nome','-')}</td><td>{v.get('dias','-')} dias</td></tr>"
    return menu("vendas") + f"""
    <div class="card">
    <h3>📋 Chaves Geradas — Total: {len(DADOS['vendas'])}</h3>
    <table><tr><th>Produto</th><th>Chave</th><th>Comprador</th><th>Validade</th></tr>{linhas}</table>
    </div></div>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
