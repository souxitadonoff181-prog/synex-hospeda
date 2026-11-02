from flask import Flask, request, redirect, url_for, session, jsonify
import os, json, secrets, hashlib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "synex_profissional_2026"
ARQUIVO_DADOS = "synex_dados.json"

# ==============================================
# BANCO DE DADOS
# ==============================================
DADOS_INICIAIS = {
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
            d = json.load(f)
            for k in DADOS_INICIAIS:
                if k not in d:
                    d[k] = DADOS_INICIAIS[k]
            return d
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

def criar_chave_sistema(produto, dias=30, comprador_id=None, comprador_nome=None):
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    dados_chave = {
        "chave": chave,
        "produto": produto,
        "dias": dias,
        "comprador_id": str(comprador_id) if comprador_id else None,
        "comprador_nome": comprador_nome,
        "status": "ativa",
        "criada_em": datetime.now().isoformat()
    }
    DADOS["chaves"][chave] = dados_chave
    DADOS["vendas"].append(dados_chave)
    salvar_dados()
    return chave

# ==============================================
# ESTILOS — TEMA ESCURO PROFISSIONAL
# ==============================================
CSS = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

:root {
    --fundo: #0a0a0f;
    --fundo-menu: #11111a;
    --fundo-card: #181825;
    --borda: #2a2a3c;
    --texto: #e4e4f7;
    --texto-claro: #9ca3af;
    --destaque: #7c3aed;
    --destaque-escuro: #6d28d9;
    --sucesso: #10b981;
    --aviso: #f59e0b;
    --erro: #ef4444;
}

body {
    background-color: var(--fundo);
    color: var(--texto);
    display: flex;
    min-height: 100vh;
    line-height: 1.6;
}

/* MENU LATERAL */
.menu-lateral {
    width: 260px;
    background-color: var(--fundo-menu);
    border-right: 1px solid var(--borda);
    position: fixed;
    height: 100vh;
    padding: 0;
    display: flex;
    flex-direction: column;
}

.logo {
    padding: 28px 24px;
    font-size: 1.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, var(--destaque), #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    border-bottom: 1px solid var(--borda);
}

.menu-lateral a {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 24px;
    color: var(--texto-claro);
    text-decoration: none;
    margin: 4px 12px;
    border-radius: 8px;
    font-size: 0.95rem;
    transition: all 0.2s ease;
}

.menu-lateral a:hover,
.menu-lateral a.ativo {
    background-color: rgba(124, 58, 237, 0.15);
    color: var(--texto);
    border-left: 3px solid var(--destaque);
}

.menu-lateral .sair {
    margin-top: auto;
    margin-bottom: 24px;
    color: var(--erro);
}

.menu-lateral .sair:hover {
    background-color: rgba(239, 68, 68, 0.1);
    border-left-color: var(--erro);
    color: var(--erro);
}

/* CONTEÚDO PRINCIPAL */
.conteudo {
    margin-left: 260px;
    padding: 32px 40px;
    flex: 1;
    width: 100%;
}

.cabecalho {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--borda);
}

.cabecalho h2 {
    font-size: 1.5rem;
    font-weight: 600;
}

.usuario {
    color: var(--texto-claro);
    font-size: 0.9rem;
}

/* CARTÕES */
.card {
    background-color: var(--fundo-card);
    border: 1px solid var(--borda);
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 24px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.card h3 {
    font-size: 1.1rem;
    margin-bottom: 16px;
    color: #d4c1ff;
}

/* FORMULÁRIOS */
label {
    display: block;
    margin-bottom: 6px;
    color: var(--texto-claro);
    font-weight: 500;
    font-size: 0.9rem;
}

input, textarea, pre {
    width: 100%;
    padding: 12px 16px;
    margin-bottom: 16px;
    background-color: #1f1f2e;
    border: 1px solid var(--borda);
    border-radius: 8px;
    color: var(--texto);
    font-size: 0.95rem;
}

input:focus, textarea:focus {
    outline: none;
    border-color: var(--destaque);
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
}

pre {
    font-family: 'Consolas', 'Monaco', monospace;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 12px 0;
}

/* BOTÕES */
.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    display: inline-block;
}

.btn-roxo {
    background: linear-gradient(90deg, var(--destaque), var(--destaque-escuro));
    color: white;
}

.btn-roxo:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.btn-verde {
    background-color: var(--sucesso);
    color: white;
}

.btn-verde:hover {
    background-color: #059669;
    transform: translateY(-1px);
}

/* CAIXAS DE AVISO */
.aviso {
    background-color: rgba(245, 158, 11, 0.1);
    border-left: 3px solid var(--aviso);
    padding: 16px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
}

.sucesso {
    background-color: rgba(16, 185, 129, 0.1);
    border-left: 3px solid var(--sucesso);
    padding: 16px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
}

/* LOGIN */
.caixa-login {
    max-width: 440px;
    margin: 100px auto;
}

.caixa-login h2 {
    text-align: center;
    margin-bottom: 24px;
    font-size: 1.4rem;
}

/* RESPONSIVO */
@media (max-width: 768px) {
    .menu-lateral { width: 200px; }
    .conteudo { margin-left: 200px; padding: 20px; }
}
"""

# ==============================================
# COMPONENTE MENU LATERAL
# ==============================================
def menu(aba_atual):
    def item_menu(aba, icone, texto, link):
        ativo = "ativo" if aba_atual == aba else ""
        return f'<a href="{link}" class="{ativo}">{icone} {texto}</a>'
    
    return f'''
<div class="menu-lateral">
    <div class="logo">SYNEX</div>
    {item_menu("api", "📦", "Entrega Automática API", "/api")}
    {item_menu("uptime", "🔄", "UptimeRobot 24h", "/uptime")}
    {item_menu("vendas", "📋", "Histórico de Vendas", "/vendas")}
    {item_menu("token", "🔑", "Configurar Bot", "/token")}
    <a href="/sair" class="sair">🚪 Sair</a>
</div>
<div class="conteudo">
    <div class="cabecalho">
        <h2>{{ "Entrega Automática — API" if aba_atual=="api" else "UptimeRobot — Manter Online" if aba_atual=="uptime" else "Histórico de Vendas" if aba_atual=="vendas" else "Configurar Bot" if aba_atual=="token" else "SYNEX" }}</h2>
        <span class="usuario">👤 {session.get("usuario", "")}</span>
    </div>
'''

# ==============================================
# ROTAS PÚBLICAS
# ==============================================
@app.route("/ping")
def ping():
    return "✅ SYNEX ONLINE — " + datetime.now().strftime("%d/%m/%Y %H:%M:%S")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if verificar_senha(request.form["usuario"], request.form["senha"]):
            session["usuario"] = request.form["usuario"]
            return redirect("/api")
        return '<script>alert("❌ Usuário ou senha incorretos");history.back()</script>'
    
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — SYNEX</title>
    <style>{CSS}</style>
</head>
<body>
    <div class="caixa-login card">
        <h2>🔐 Acesso ao Sistema</h2>
        <form method="POST">
            <label>Usuário</label>
            <input type="text" name="usuario" required placeholder="Digite seu usuário">
            
            <label>Senha</label>
            <input type="password" name="senha" required placeholder="Digite sua senha">
            
            <button type="submit" class="btn btn-roxo" style="width: 100%; margin-top: 8px;">Entrar</button>
        </form>
        <p style="text-align: center; margin-top: 20px; color: var(--texto-claro); font-size: 0.9rem;">
            Padrão: <code>synex</code> / <code>123</code>
        </p>
    </div>
</body>
</html>"""

@app.route("/sair")
def sair():
    session.clear()
    return redirect("/login")

@app.route("/")
def inicio():
    return redirect("/login")

# ==============================================
# 1. ENTREGA AUTOMÁTICA — API COMPLETA
# ==============================================
@app.route("/api")
def pagina_api():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    
    return menu("api") + f"""
<div class="card">
    <h3>📦 API de Entrega Automática</h3>
    <p style="color: var(--texto-claro); margin-bottom: 16px;">
        Use esse endpoint no seu bot para gerar chaves e receber os dados do comprador.
    </p>

    <h4 style="margin-bottom: 8px; color: #a78bfa;">Requisição:</h4>
    <pre>POST → {dominio}/api/gerar-chave
Content-Type: application/json

{{
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Usuário no Discord",
  "comprador_nome": "Nome do Cliente"
}}</pre>

    <h4 style="margin: 20px 0 8px; color: var(--sucesso);">Resposta:</h4>
    <pre>{{
  "sucesso": true,
  "chave": "SYNEX-XXXX-XXXX-XXXX",
  "produto": "Nome do Produto",
  "dias": 30,
  "comprador_id": "ID do Usuário",
  "comprador_nome": "Nome do Cliente"
}}</pre>

    <button class="btn btn-verde" onclick="navigator.clipboard.writeText('{dominio}/api/gerar-chave')">
        📋 Copiar URL da API
    </button>
</div>

<div class="card">
    <h3>💬 Exemplo de Código no Bot</h3>
    <pre id="exemplo">import requests

DOMINIO = "{dominio}"

def gerar_chave_para_cliente(produto, dias, comprador_id, comprador_nome):
    resposta = requests.post(
        f"{{DOMINIO}}/api/gerar-chave",
        json={{
            "produto": produto,
            "dias": dias,
            "comprador_id": comprador_id,
            "comprador_nome": comprador_nome
        }}
    )
    dados = resposta.json()
    
    if dados["sucesso"]:
        print(f"✅ Chave gerada!")
        print(f"Cliente: {{dados['comprador_nome']}}")
        print(f"Produto: {{dados['produto']}}")
        print(f"Validade: {{dados['dias']}} dias")
        print(f"Chave: {{dados['chave']}}")
        return dados
    return None</pre>
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('exemplo').innerText)">
        📋 Copiar Exemplo
    </button>
</div>
</div>"""

@app.route("/api/gerar-chave", methods=["POST"])
def endpoint_api_gerar_chave():
    dados = request.json
    produto = dados.get("produto", "Produto")
    dias = int(dados.get("dias", 30))
    comprador_id = dados.get("comprador_id")
    comprador_nome = dados.get("comprador_nome")
    
    chave = criar_chave_sistema(produto, dias, comprador_id, comprador_nome)
    
    return jsonify({
        "sucesso": True,
        "chave": chave,
        "produto": produto,
        "dias": dias,
        "comprador_id": comprador_id,
        "comprador_nome": comprador_nome
    })

# ==============================================
# 2. UPTIMEROBOT
# ==============================================
@app.route("/uptime")
def pagina_uptime():
    if "usuario" not in session:
        return redirect("/login")
    dominio = request.host_url.rstrip("/")
    
    return menu("uptime") + f"""
<div class="card">
    <h3>🔄 Manter Bot 24h Online</h3>
    <p style="color: var(--texto-claro); margin-bottom: 16px;">
        Cadastre essa URL no UptimeRobot para o sistema nunca cair.
    </p>

    <input type="text" value="{dominio}/ping" id="url_ping" readonly>
    
    <button class="btn btn-verde" onclick="navigator.clipboard.writeText(document.getElementById('url_ping').value)">
        📋 Copiar URL de Monitoramento
    </button>

    <div class="aviso">
        <strong>📌 Passo a passo:</strong><br>
        1. Acesse <strong>uptimerobot.com</strong> e crie uma conta grátis<br>
        2. Clique em <strong>Add New Monitor</strong><br>
        3. Tipo: <strong>HTTP(s)</strong><br>
        4. Cole a URL acima<br>
        5. Intervalo: <strong>5 minutos</strong><br>
        6. Salvar ✅ Pronto! Vai ficar sempre online
    </div>
</div>
</div>"""

# ==============================================
# 3. HISTÓRICO DE VENDAS
# ==============================================
@app.route("/vendas")
def pagina_vendas():
    if "usuario" not in session:
        return redirect("/login")
    
    lista = list(DADOS["vendas"].__reversed__()) if hasattr(DADOS["vendas"], "__reversed__") else list(reversed(DADOS["vendas"]))
    
    linhas = ""
    for v in lista[:30]:
        linhas += f"""<tr style="border-bottom: 1px solid var(--borda);">
            <td style="padding: 12px 8px;">{v.get('produto', '-')}</td>
            <td style="padding: 12px 8px;"><code style="padding: 4px 8px; margin: 0; font-size: 0.85rem;">{v.get('chave', '-')}</code></td>
            <td style="padding: 12px 8px;">{v.get('comprador_nome', '-')}</td>
            <td style="padding: 12px 8px;">{v.get('dias', '-')} dias</td>
            <td style="padding: 12px 8px; color: var(--sucesso);">✅ Ativa</td>
        </tr>"""
    
    return menu("vendas") + f"""
<div class="card">
    <h3>📋 Últimas Chaves Geradas</h3>
    <p style="color: var(--texto-claro); margin-bottom: 16px;">Total: {len(DADOS['vendas'])} chaves</p>
    
    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="color: var(--texto-claro); font-size: 0.9rem;">
                    <th style="padding: 10px 8px; text-align: left;">Produto</th>
                    <th style="padding: 10px 8px; text-align: left;">Chave</th>
                    <th style="padding: 10px 8px; text-align: left;">Comprador
