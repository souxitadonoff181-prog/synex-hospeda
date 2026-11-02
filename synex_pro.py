from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, uuid, secrets, hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "synex_hospeda_final_completo_v1"
ARQUIVO_DADOS = "synex_dados_pro.json"

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
    "vendas": [],
    "bots": {}
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

def hash_senha(s): return hashlib.sha256(s.encode()).hexdigest()
def verificar_senha(u, s): return u in DADOS["usuarios"] and DADOS["usuarios"][u]["senha_hash"] == hash_senha(s)

def criar_chave_sistema(nome, dias=30, comprador_id=None, origem="painel"):
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    DADOS["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8], "nome": nome, "chave": chave, "dias": dias,
        "expira_em": (datetime.now() + timedelta(days=dias)).isoformat(),
        "origem": origem, "status": "ativa", "criada_em": datetime.now().isoformat(),
        "comprador_id": str(comprador_id) if comprador_id else None
    }
    salvar_dados()
    return chave

T = {
    "pt": {
        "painel": "📊 Painel", "chaves": "🔑 Criar Chaves", "vendas": "💰 Vendas & Entrega",
        "vs": "💻 Visual Studio C#", "bots": "🤖 Gerador de Bots", "usuarios": "👥 Usuários",
        "sair": "🚪 Sair", "bemvindo": "Bem-vindo", "total_chaves": "Total de Chaves",
        "ativas": "Ativas", "vs_geradas": "Pelo VS", "ow_geradas": "Owlivery",
        "criar_chave": "➕ Criar Nova Chave", "nome_produto": "Nome do Produto",
        "validade_dias": "Validade (dias)", "criar": "✅ Criar Chave", "lista_chaves": "Lista de Chaves",
        "nenhuma_chave": "Nenhuma chave criada ainda", "nome": "Nome", "chave": "Chave",
        "origem": "Origem", "status": "Status", "site": "Site", "vs_origem": "Visual Studio",
        "ow_origem": "Owlivery", "ativa": "Ativa", "inativa": "Inativa",
        "vs_titulo": "Gerador de Código — Visual Studio C#",
        "vs_desc": "Gere seu código personalizado no formato KeyAuthApp",
        "seu_nome_app": "Nome da Aplicação", "seu_owner_id": "Seu Owner ID",
        "versao": "Versão", "gerar_codigo": "🔄 Gerar Código", "copiar": "📋 Copiar Código",
        "instrucoes_uso": "Instruções de Uso", "passo1": "1. Cole no seu projeto do Visual Studio",
        "passo2": "2. Instale o pacote: Install-Package Newtonsoft.Json",
        "passo3": "3. Use KeyAuthApp.Login(\"usuario\", \"senha\") para conectar",
        "passo4": "4. Crie chaves: KeyAuthApp.CriarChave(\"Nome\", 30)",
        "gerador_bots": "🤖 Gerador de Bots Discord", "estilo_bot": "Estilo do Bot",
        "bot_entrega": "Bot de Entrega Automática", "bot_comandos": "Bot com Comandos",
        "bot_personalizado": "Personalizado", "nome_bot": "Nome do Bot",
        "gerar_bot": "🔄 Gerar Código do Bot", "token_aviso": "Coloque seu Token no lugar indicado",
        "uptime_titulo": "🔄 Manter Bot 24h Online", "uptime_desc": "Use UptimeRobot para manter acordado",
        "url_monitorar": "URL para monitorar", "copiar_url": "Copiar URL", "passos_uptime": "Passos no UptimeRobot",
        "passos_uptime1": "1. Acesse UptimeRobot.com → conta grátis",
        "passos_uptime2": "2. Add New Monitor → tipo HTTP(s)",
        "passos_uptime3": "3. Cole a URL → Intervalo: 5 min",
        "passos_uptime4": "4. Salve → ✅ Bot online 24h!",
        "criar_usuario": "➕ Criar Novo Usuário", "nome_usuario": "Nome de Usuário",
        "senha": "Senha", "confirmar_senha": "Confirmar Senha",
        "criar_usuario_btn": "✅ Criar Usuário", "lista_usuarios": "Usuários do Sistema",
        "nivel": "Nível", "data_criacao": "Criado em", "admin": "Administrador",
        "usuario_comum": "Usuário", "login_titulo": "🔐 Entrar no SYNEX",
        "erro_login": "Usuário ou senha incorretos", "entrar": "Entrar",
        "padrao_login": "Padrão: synex / 123", "idioma": "Idioma",
        "entrega_titulo": "📦 Entrega Automática — Owlivery & Bots",
        "webhook_ow": "Webhook para Owlivery", "copiar_webhook": "Copiar Webhook",
        "explicar_webhook": "Cole nas configurações de entrega da Owlivery",
        "exemplo_bot_proprio": "Exemplo — Bot Próprio",
        "codigo_bot_aviso": "Função de entrega pra usar no seu bot",
        "tudo_sincronizado": "Tudo sincronizado: cria de qualquer lado → aparece aqui",
        "usuario_criado": "Usuário criado!", "senha_nao_confere": "Senhas não conferem",
        "usuario_existe": "Nome de usuário já existe"
    },
    "en": {
        "painel": "📊 Dashboard", "chaves": "🔑 Create Keys", "vendas": "💰 Sales & Delivery",
        "vs": "💻 Visual Studio C#", "bots": "🤖 Bot Generator", "usuarios": "👥 Users",
        "sair": "🚪 Logout", "bemvindo": "Welcome", "total_chaves": "Total Keys",
        "ativas": "Active", "vs_geradas": "From VS", "ow_geradas": "Owlivery",
        "criar_chave": "➕ Create New Key", "nome_produto": "Product Name",
        "validade_dias": "Validity (days)", "criar": "✅ Create Key", "lista_chaves": "Key List",
        "nenhuma_chave": "No keys created yet", "nome": "Name", "chave": "Key",
        "origem": "Source", "status": "Status", "site": "Website", "vs_origem": "Visual Studio",
        "ow_origem": "Owlivery", "ativa": "Active", "inativa": "Inactive",
        "vs_titulo": "Code Generator — Visual Studio C#",
        "vs_desc": "Generate custom code in KeyAuthApp format",
        "seu_nome_app": "App Name", "seu_owner_id": "Your Owner ID",
        "versao": "Version", "gerar_codigo": "🔄 Generate Code", "copiar": "📋 Copy Code",
        "instrucoes_uso": "Usage Instructions", "passo1": "1. Paste into your VS project",
        "passo2": "2. Install: Install-Package Newtonsoft.Json",
        "passo3": "3. Login: KeyAuthApp.Login(\"user\", \"pass\")",
        "passo4": "4. Create keys: KeyAuthApp.CreateKey(\"Name\", 30)",
        "gerador_bots": "🤖 Discord Bot Generator", "estilo_bot": "Bot Style",
        "bot_entrega": "Auto Delivery Bot", "bot_comandos": "Commands Bot",
        "bot_personalizado": "Custom", "nome_bot": "Bot Name",
        "gerar_bot": "🔄 Generate Bot Code", "token_aviso": "Replace with your bot token",
        "uptime_titulo": "🔄 Keep Bot Online 24/7", "uptime_desc": "Use UptimeRobot to stay awake",
        "url_monitorar": "URL to Monitor", "copiar_url": "Copy URL", "passos_uptime": "UptimeRobot Steps",
        "passos_uptime1": "1. Go to UptimeRobot.com → free account",
        "passos_uptime2": "2. Add Monitor → HTTP(s)",
        "passos_uptime3": "3. Paste URL → Interval: 5 min",
        "passos_uptime4": "4. Save → ✅ Online 24/7!",
        "criar_usuario": "➕ Create New User", "nome_usuario": "Username",
        "senha": "Password", "confirmar_senha": "Confirm Password",
        "criar_usuario_btn": "✅ Create User", "lista_usuarios": "System Users",
        "nivel": "Level", "data_criacao": "Created", "admin": "Admin",
        "usuario_comum": "User", "login_titulo": "🔐 Login to SYNEX",
        "erro_login": "Invalid credentials", "entrar": "Login",
        "padrao_login": "Default: synex / 123", "idioma": "Language",
        "entrega_titulo": "📦 Auto Delivery — Owlivery & Bots",
        "webhook_ow": "Owlivery Webhook", "copiar_webhook": "Copy Webhook",
        "explicar_webhook": "Paste into Owlivery delivery settings",
        "exemplo_bot_proprio": "Example — Custom Bot",
        "codigo_bot_aviso": "Delivery function for your bot",
        "tudo_sincronizado": "Synced: create anywhere → appears here",
        "usuario_criado": "User created!", "senha_nao_confere": "Passwords do not match",
        "usuario_existe": "Username already exists"
    }
}

def L(chave):
    return T[session.get("idioma", "pt")].get(chave, chave)

CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
:root{--p:#7928ca;--s:#10b981;--a:#f59e0b;--e:#ef4444;--f:#05050a;--1:#12121f;--2:#1a1a2e;--t:#e0e0ff;--m:#8888aa}
body{background:var(--f);color:var(--t);display:flex;min-height:100vh}
.sb{width:270px;background:var(--1);position:fixed;height:100vh;border-right:1px solid #2a2a4a;padding:20px 0}
.logo{padding:25px 20px;font-size:1.5rem;font-weight:800;background:linear-gradient(90deg,var(--p),var(--s));-webkit-background-clip:text;color:transparent}
.sb a{display:flex;align-items:center;gap:10px;padding:14px 22px;color:var(--m);text-decoration:none;margin:4px 12px;border-radius:8px}
.sb a.ativo,.sb a:hover{background:rgba(121,40,202,.15);color:var(--t);border-left:3px solid var(--p)}
.cont{margin-left:270px;padding:30px;flex:1}
.cab{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid #2a2a4a}
.lang-btn{background:var(--2);border:none;color:var(--t);padding:8px 16px;border-radius:6px;cursor:pointer;margin-left:8px}
.lang-btn.ativo{background:var(--p)}
.card{background:var(--1);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #2a2a4a}
.card h3{margin-bottom:18px;color:#d0b0ff}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:20px;margin-bottom:25px}
.gcard{background:var(--2);border-radius:12px;padding:22px;text-align:center;border:1px solid #2a2a4a}
.gcard .val{font-size:2rem;font-weight:800;margin:10px 0}
.btn{padding:11px 22px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin:4px}
.btn.roxo{background:linear-gradient(90deg,var(--p),#9333ea);color:white}
.btn.verde{background:var(--s);color:white}
input,select{width:100%;padding:13px;margin:8px 0 16px;background:var(--2);border:1px solid #2a2a4a;border-radius:8px;color:white;font-size:1rem}
label{color:var(--m);font-weight:500;margin-top:10px;display:block}
.tabela{width:100%;border-collapse:collapse;margin-top:15px}
.tabela th,.tabela td{padding:14px 16px;text-align:left;border-bottom:1px solid #2a2a4a}
.tabela th{color:var(--m);font-weight:600;font-size:.85rem}
.badge{padding:5px 12px;border-radius:20px;font-size:.75rem;font-weight:bold;text-transform:uppercase}
.badge.at{background:rgba(16,185,129,.15);color:#6ee7b7}
.badge.ow{background:rgba(59,130,246,.15);color:#93c5fd}
.badge.vs{background:rgba(96,165,250,.15);color:#93c5fd}
code,pre{background:#0f172a;border:1px solid #3b82f6;border-radius:8px;padding:15px;margin:10px 0;overflow-x:auto;font-family:'Consolas',monospace;color:#e0e0ff}
"""

def gerar_menu(aba):
    lang = session.get("idioma", "pt")
    return f'''<div class="sb">
        <div class="logo">SYNEX</div>
        <a href="/" class="{'ativo' if aba=='home' else ''}">{L("painel")}</a>
        <a href="/chaves" class="{'ativo' if aba=='chaves' else ''}">{L("chaves")}</a>
        <a href="/entrega" class="{'ativo' if aba=='entrega' else ''}">{L("vendas")}</a>
        <a href="/visualstudio" class="{'ativo' if aba=='vs' else ''}">{L("vs")}</a>
        <a href="/bots" class="{'ativo' if aba=='bots' else ''}">{L("bots")}</a>
        <a href="/usuarios" class="{'ativo' if aba=='usuarios' else ''}">{L("usuarios")}</a>
        <a href="/sair">{L("sair")}</a>
    </div>
    <div class="cont">
        <div class="cab">
            <h2>{L(aba.replace('home','bemvindo').replace('chaves','criar_chave').replace('entrega','entrega_titulo').replace('vs','vs_titulo').replace('bots','gerador_bots').replace('usuarios','criar_usuario'))}</h2>
            <div>
                <button class="lang-btn {'ativo' if lang=='pt' else ''}" onclick="window.location.href='/trocar-idioma/pt'">🇧🇷 PT</button>
                <button class="lang-btn {'ativo' if lang=='en' else ''}" onclick="window.location.href='/trocar-idioma/en'">🇺🇸 EN</button>
            </div>
        </div>
'''

@app.route("/trocar-idioma/<lang>")
def trocar_idioma(lang):
    if lang in ["pt", "en"]: session["idioma"] = lang
    return redirect(request.referrer or "/")

@app.route("/ping")
def ping(): return "pong"

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    return jsonify({"sucesso": True, "usuario": d["usuario"]}) if verificar_senha(d.get("usuario"), d.get("senha")) else (jsonify({"sucesso": False}), 401)

@app.route("/api/criar-chave", methods=["POST"])
def api_criar_chave():
    d = request.json
    if not verificar_senha(d.get("usuario"), d.get("senha")): return jsonify({"sucesso": False}), 401
    chave = criar_chave_sistema(d.get("nome", L("chave")), int(d.get("dias", 30)), origem="visual_studio")
    return jsonify({"sucesso": True, "chave": chave})

@app.route("/api/listar-chaves", methods=["POST"])
def api_listar():
    d = request.json
    if not verificar_senha(d.get("usuario"), d.get("senha")): return jsonify({"sucesso": False}), 401
    return jsonify({"sucesso": True, "chaves": list(DADOS["chaves"].values())})

@app.route("/api/criar-usuario", methods=["POST"])
def api_novo_usuario():
    d = request.json
    if not verificar_senha(d.get("admin_usuario"), d.get("admin_senha")): return jsonify({"sucesso": False}), 403
    if d["novo_usuario"] in DADOS["usuarios"]: return jsonify({"sucesso": False, "erro": L("usuario_existe")}), 400
    DADOS["usuarios"][d["novo_usuario"]] = {"senha_hash": hash_senha(d["nova_senha"]), "nivel": "usuario", "criado_em": datetime.now().isoformat()}
    salvar_dados()
    return jsonify({"sucesso": True})

@app.route("/api/gerar-chave", methods=["POST"])
def api_owlivery():
    d = request.json
    chave = criar_chave_sistema(d.get("produto", "Produto"), int(d.get("dias", 30)), d.get("usuario_id"), "owlivery")
    DADOS["vendas"].append({
        "produto": d.get("produto"), "chave": chave, "comprador_id": str(d.get("usuario_id")),
        "valor": d.get("valor"), "data": datetime.now().isoformat(), "origem": "owlivery"
    })
    salvar_dados()
    return jsonify({"sucesso": True, "chave": chave})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect
