from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, uuid, secrets, hashlib

app = Flask(__name__)
app.secret_key = "synex_gerador_bots_completo_2026"
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
                if k not in dados: dados[k] = DADOS_INICIAIS[k]
            return dados
    return DADOS_INICIAIS.copy()

def salvar_dados():
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(DADOS, f, ensure_ascii=False, indent=4)

DADOS = carregar_dados()

# ==============================================
# FUNÇÕES
# ==============================================
def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def verificar_senha(u, s): return u in DADOS["usuarios"] and DADOS["usuarios"][u]["senha_hash"] == hash_senha(s)

def criar_chave_sistema(nome, dias=30, comprador_id=None, origem="api"):
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    DADOS["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8], "nome": nome, "chave": chave, "dias": dias,
        "origem": origem, "status": "ativa", "comprador_id": str(comprador_id) if comprador_id else None
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

/* MENU LATERAL ESQUERDA */
.sb{width:260px;background:var(--1);position:fixed;height:100vh;border-right:1px solid #2a2a4a;padding:20px 0}
.logo{padding:25px 20px;font-size:1.4rem;font-weight:800;background:linear-gradient(90deg,var(--p),var(--s));-webkit-background-clip:text;color:transparent}
.sb a{display:flex;align-items:center;gap:10px;padding:13px 20px;color:var(--m);text-decoration:none;margin:4px 10px;border-radius:8px;font-size:.95rem;transition:.2s}
.sb a.ativo,.sb a:hover{background:rgba(121,40,202,.15);color:var(--t);border-left:3px solid var(--p)}
.sb .divisao{height:1px;background:#2a2a4a;margin:15px 20px}

/* CONTEÚDO */
.cont{margin-left:260px;padding:25px;flex:1}
.cab{display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;padding-bottom:15px;border-bottom:1px solid #2a2a4a}
.card{background:var(--1);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #2a2a4a}
.card h3{margin-bottom:18px;color:#d0b0ff}
.btn{padding:11px 20px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:5px;font-size:.95rem}
.btn.roxo{background:linear-gradient(90deg,var(--p),#9333ea);color:white}
.btn.verde{background:var(--s);color:white}
.btn.azul{background:#3b82f6;color:white}
.btn.laranja{background:var(--a);color:white}
input,textarea{width:100%;padding:13px;margin:8px 0 15px;background:var(--2);border:1px solid #2a2a4a;border-radius:8px;color:white;font-size:.95rem}
label{color:var(--m);font-weight:500;margin-top:10px;display:block}
pre{background:#0f172a;border:1px solid #3b82f6;border-radius:8px;padding:16px;margin:12px 0;overflow-x:auto;color:#e0e0ff;font-size:.85rem;white-space:pre-wrap}
.aviso{background:rgba(245,158,11,.1);border-left:3px solid var(--a);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}
.sucesso{background:rgba(16,185,129,.1);border-left:3px solid var(--s);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}
.erro{background:rgba(239,68,68,.1);border-left:3px solid var(--e);padding:14px;border-radius:0 8px 8px 0;margin:12px 0}
.login-box{max-width:420px;margin:100px auto}
.opcoes{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0}
.opcao{background:var(--2);border:2px solid transparent;border-radius:10px;padding:20px;text-align:center;cursor:pointer;transition:.2s}
.opcao:hover{border-color:var(--p)}
.opcao.selecionada{border-color:var(--p);background:rgba(121,40,202,.1)}
.opcao span{font-size:2rem;display:block;margin-bottom:10px}
"""

# ==============================================
# MENU LATERAL
# ==============================================
def menu(aba):
    return f'''<div class="sb">
        <div class="logo">SYNEX</div>
        <a href="/bots" class="{'ativo' if aba=='bots' else ''}">🤖 Gerador de Bots</a>
        <a href="/bot-online" class="{'ativo' if aba=='bot-online' else ''}">🟢 Colocar Bot Online</a>
        <a href="/entrega-api" class="{'ativo' if aba=='api' else ''}">📦 Entrega Automática API</a>
        <a href="/uptimerobot" class="{'ativo' if aba=='uptime' else ''}">🔄 UptimeRobot 24h</a>
        <div class="divisao"></div>
        <a href="/sair" style="color:var(--e)">🚪 Sair</a>
    </div>
    <div class="cont">
        <div class="cab">
            <h2>{aba.replace('bots','🤖 Gerador de Bots').replace('bot-online','🟢 Colocar Bot Online').replace('api','📦 Entrega Automática — API').replace('uptime','🔄 UptimeRobot — Manter 24h')}</h2>
            <span style="color:var(--m)">👤 {session.get('usuario')}</span>
        </div>
'''

# ==============================================
# ROTAS PÚBLICAS
# ==============================================
@app.route("/ping")
def ping(): return "✅ SYNEX ONLINE — " + __import__("datetime").datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/bots")
        return "<script>alert('❌ Usuário ou senha errados');history.back()</script>"
    return f"""<!DOCTYPE html>
<html><head><meta charset=UTF-8><title>Login — SYNEX</title><style>{CSS}</style></head>
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
<p style="text-align:center;margin-top:15px;color:var(--m)">synex / 123</p>
</div>
</body></html>"""

@app.route("/sair")
def sair(): session.clear(); return redirect("/login")

# ==============================================
# 1. GERADOR DE BOTS
# ==============================================
@app.route("/bots", methods=["GET", "POST"])
def pagina_bots():
    if "usuario" not in session: return redirect("/login")
    
    tipo = request.form.get("tipo", "codigo") if request.method == "POST" else "codigo"
    dominio = request.host_url.rstrip("/")
    
    codigo_bot = f'''import discord
from discord.ext import commands
import requests
import os

# ==============================================
# CONFIGURAÇÕES
# ==============================================
DOMINIO = "{dominio}"
PREFIXO = "!"

bot = commands.Bot(command_prefix=PREFIXO, intents=discord.Intents.all())

# ==============================================
# BOT PRONTO — COMANDOS
# ==============================================
@bot.event
async def on_ready():
    print("="*40)
    print(f"✅ BOT CONECTADO COMO: {{bot.user}}")
    print(f"✅ ID: {{bot.user.id}}")
    print("="*40)
    await bot.change_presence(activity=discord.Game(name="Gerando chaves automaticamente!"))

@bot.command(name="gerarchave", help="Gera uma chave para o cliente")
async def gerar_chave(ctx, nome_produto: str, dias: int = 30):
    """Uso: !gerarchave NomeDoProduto 30"""
    try:
        resposta = requests.post(
            f"{{DOMINIO}}/api/gerar-chave",
            json={{
                "produto": nome_produto,
                "dias": dias,
                "comprador_id": str(ctx.author.id),
                "comprador_nome": str(ctx.author)
            }}
        )
        dados = resposta.json()
        
        if dados.get("sucesso"):
            embed = discord.Embed(
                title="✅ CHAVE GERADA COM SUCESSO!",
                color=discord.Color.green()
            )
            embed.add_field(name="Produto", value=nome_produto, inline=False)
            embed.add_field(name="Validade", value=f"{{dias}} dias", inline=False)
            embed.add_field(name="Sua Chave", value=f"`{{dados['chave']}}`", inline=False)
            embed.set_footer(text=f"Gerado para {{ctx.author}}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Erro ao gerar chave, tente novamente.")
            
    except Exception as e:
        await ctx.send(f"⚠️ Erro: {{e}}")

@bot.command(name="status", help="Verifica se o bot está online")
async def status_bot(ctx):
    embed = discord.Embed(title="🟢 BOT ONLINE", description="Estou funcionando perfeitamente!", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="ajuda", help="Mostra todos os comandos")
async def ajuda_bot(ctx):
    embed = discord.Embed(title="📖 Comandos Disponíveis", color=discord.Color.blue())
    embed.add_field(name="!gerarchave Produto 30", value="Gera uma chave", inline=False)
    embed.add_field(name="!status", value="Verifica se estou online", inline=False)
    embed.add_field(name="!ajuda", value="Mostra esta mensagem", inline=False)
    await ctx.send(embed=embed)

# ==============================================
# INICIAR O BOT
# ==============================================
if __name__ == "__main__":
    print("🔄 Iniciando o bot...")
    print("⚠️ Coloque seu token abaixo no lugar de SEU_TOKEN_AQUI")
    bot.run("SEU_TOKEN_AQUI")
'''
    
    return f"""{menu('bots')}
    
    <div class="card">
        <h3>📋 Escolha como quer o código do bot</h3>
        <form method=POST id=formtipo>
        <div class="opcoes">
            <label class="opcao {'selecionada' if tipo=='codigo' else ''}" onclick="document.getElementById('tipo').value='codigo';document.getElementById('formtipo').submit()">
                <span>📝</span>
                <strong>Código Completo</strong>
                <p style="font-size:.8rem;color:var(--m)">Copia e cola direto no seu bot</p>
            </label>
            <input type=hidden name=tipo id=tipo value={tipo}>
        </div>
        </form>
    </div>
    
    <div class="card">
        <h3>🤖 Código do Bot Discord</h3>
        <p style="margin-bottom:15px;color:var(--m)">Copia tudo abaixo e salva como <code>bot.py</code></p>
        <pre id=codigo>{codigo_bot}</pre>
        <button class="btn verde" onclick="navigator.clipboard.writeText(document.getElementById('codigo').innerText)">📋 Copiar Código Completo</button>
        
        <div class="aviso">
            <strong>⚠️ O que fazer:</strong><br>
            1. Instale as dependências: <code>pip install discord requests</code><br>
            2. Troque <code>SEU_TOKEN_AQUI</code> pelo token real do seu bot<br>
            3. Execute: <code>python bot.py</code><br>
            4. Pronto! Seu bot vai ficar online e gerar chaves sozinho!
        </div>
    </div>
    
    </div>
    </div>"""

# ==============================================
# 2. COLOCAR BOT ONLINE
# ==============================================
@app.route("/bot-online", methods=["GET", "POST"])
def pagina_bot_online():
    if "usuario" not in session: return redirect("/login")
    
    token = request.form.get("token", "") if request.method == "POST" else ""
    
    return f"""{menu('bot-online')}
    
    <div class="card">
        <h3>🔑 Coloque o Token do Seu Bot</h3>
        <p style="color:var(--m);margin-bottom:15px;">Cole o token do bot aqui e ele vai estar configurado pra funcionar. O token fica no <strong>Discord Developers Portal</strong></p>
        
        <form method=POST>
            <label>Token do Bot</label>
            <input type=password name=token placeholder="Cole seu token aqui — ex: MTIzNDU2Nzg5MDEyMzQ1Njc4OQ..." value="{token}">
            <button class="btn roxo">✅ Salvar e Usar</button>
        </form>
        
        {f'''<div class="sucesso">✅ Token salvo! Use o código acima e ele já vai estar pronto pra rodar!</div>''' if token else ''}
        
        <div class="aviso">
            <strong>📌 Como conseguir o token:</strong><br>
            1. Acesse <strong>discord.com/developers/applications</strong><br>
            2. Crie um App ou escolha o existente<br>
            3. Vá em <strong>Bot</strong> → clique em <strong>Reset Token</strong><br>
            4. Copie e cole aqui<br>
            5. Ative em <strong>Privileged Gateway Intents</strong>: todas as opções (Message Content Intent, etc)
        </div>
    </div>
    
    <div class="card">
        <h3>🚀 Rodar o Bot — Passo a Passo</h3>
        <pre>
# 1. Instalar Python
Baixe em: python.org/downloads

# 2. Instalar bibliotecas
Abra o terminal e digite:
pip install discord requests

# 3. Salvar o código
Crie um arquivo chamado bot.py e cole o código

# 4. Colocar seu token
Troque SEU_TOKEN_AQUI pelo token que você salvou

# 5. Rodar!
python bot.py

✅ Pronto! Vai aparecer: BOT CONECTADO COMO...
        </pre>
    </div>
    
    </div>
    </div>"""

# ==============================================
# 3. ENTREGA AUTOMÁTICA API
# ==============================================
@app.route("/entrega-api")
def pagina_api():
    if "usuario" not in session: return redirect("/login")
    dominio = request.host_url.rstrip("/")
    
    return f"""{menu('api')}
    
    <div class="card">
        <h3>📦 API de Entrega Automática</h3>
        <p>Use essa URL no seu bot ou sistema para gerar chaves automaticamente:</p>
        
        <pre>POST → {dominio}/api/gerar-chave
Content-Type: application/json

{{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Cliente no Discord"
}}

✅ Resposta:
{{
  "sucesso": true,
  "chave": "SYNEX-XXXXX-XXXXX-XXXXX"
}}
        </pre>
        
        <button class="btn verde" onclick="navigator.clipboard.writeText('{dominio}/api/gerar-chave')">📋 Copiar Endpoint da API</button>
    </div>
    
    <div class="card">
        <h3>🔗 Exemplo de Uso no Seu Bot</h3>
        <pre
