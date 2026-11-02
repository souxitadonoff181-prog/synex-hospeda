import os
import re
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

BASE_DIR = Path(__file__).parent
BOT_FILE = BASE_DIR / "synex_pro.py"
ENV_FILE = BASE_DIR / ".env"

app = Flask(__name__)
app.secret_key = "synex_panel_2026"

bot_process = None
bot_lock = threading.Lock()

# ========== PEGAR TOKEN ==========
def get_token():
    if not ENV_FILE.exists():
        return None
    text = ENV_FILE.read_text(encoding="utf-8")
    match = re.search(r"DISCORD_TOKEN\s*=\s*([^\n]+)", text)
    return match.group(1).strip() if match else None

# ========== VERIFICAR BOT ==========
def verificar_bot():
    erros = []
    avisos = []

    if not BOT_FILE.exists():
        erros.append(f"❌ Arquivo do bot não encontrado: {BOT_FILE.name}")
        return erros, avisos
    avisos.append(f"✅ Arquivo {BOT_FILE.name} encontrado")

    codigo = BOT_FILE.read_text(encoding="utf-8")
    if codigo.count("(") != codigo.count(")"):
        erros.append("❌ Erro: parênteses não fechados no código do bot")
    elif codigo.count('"') % 2 != 0 or codigo.count("'") % 2 != 0:
        erros.append("❌ Erro: aspas não fechadas no código do bot")
    else:
        avisos.append("✅ Código do bot sem erros de sintaxe")

    token = get_token()
    if not token:
        erros.append("❌ Token não configurado — adicione a variável DISCORD_TOKEN no Render")
    elif len(token) < 30:
        erros.append("⚠️ Token muito curto — verifique se está correto")
    else:
        avisos.append("✅ Token configurado")

    try:
        import flask, discord
        avisos.append("✅ Dependências instaladas")
    except ImportError as e:
        erros.append(f"❌ Falta instalar: {e.name}")

    return erros, avisos

# ========== CONTROLE DO BOT ==========
def rodar_bot():
    global bot_process
    with bot_lock:
        parar_bot()
        bot_process = subprocess.Popen(
            ["python", str(BOT_FILE)],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

def parar_bot():
    global bot_process
    with bot_lock:
        if bot_process and bot_process.poll() is None:
            bot_process.terminate()
            try:
                bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bot_process.kill()
        bot_process = None

def status_bot():
    with bot_lock:
        if not bot_process:
            return "parado"
        return "rodando" if bot_process.poll() is None else "parado"

def ler_logs():
    linhas = []
    if bot_process and bot_process.stdout:
        for _ in range(25):
            linha = bot_process.stdout.readline()
            if not linha: break
            linhas.append(linha.strip())
    return linhas

# ========== ROTAS DO SITE ==========
@app.route("/")
def index():
    erros, avisos = verificar_bot()
    token = get_token()
    status_atual = status_bot()
    return render_template_string(PAGINA_HTML,
        erros=erros,
        avisos=avisos,
        token_configurado=bool(token),
        token_tamanho=len(token or ""),
        status_atual=status_atual)

@app.route("/api/start", methods=["POST"])
def api_start():
    erros, avisos = verificar_bot()
    if erros:
        return jsonify({"ok": False, "erros": erros})
    threading.Thread(target=rodar_bot, daemon=True).start()
    return jsonify({"ok": True, "msg": "Bot iniciado! Verifique os logs abaixo."})

@app.route("/api/restart", methods=["POST"])
def api_restart():
    erros, _ = verificar_bot()
    if erros:
        return jsonify({"ok": False, "erros": erros})
    threading.Thread(target=rodar_bot, daemon=True).start()
    return jsonify({"ok": True, "msg": "Reiniciando..."})

@app.route("/api/kill", methods=["POST"])
def api_kill():
    parar_bot()
    return jsonify({"ok": True, "msg": "Bot parado"})

@app.route("/api/status")
def api_status():
    return jsonify({"status": status_bot(), "logs": ler_logs()})

@app.route("/api/salvar-token", methods=["POST"])
def salvar_token():
    token = request.json.get("token", "").strip()
    if not token:
        return jsonify({"ok": False, "msg": "Token vazio!"})
    ENV_FILE.write_text(f"DISCORD_TOKEN={token}\n", encoding="utf-8")
    return jsonify({"ok": True, "msg": "Token salvo ✅"})

# ========== INTERFACE ==========
PAGINA_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel — Seu Bot</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
        body{display:flex;background:#0b0e17;color:#e6e6e6;min-height:100vh}
        aside{width:250px;background:#141828;border-right:1px solid #252a41;padding:20px 0;position:fixed;height:100vh}
        aside h2{font-size:19px;padding:0 20px 25px;color:#7289da}
        .btn-menu{display:block;width:100%;text-align:left;background:transparent;border:none;color:#a0a0b5;padding:15px 20px;cursor:pointer;font-size:15px;transition:.2s}
        .btn-menu:hover,.btn-menu.ativo{background:#1e2338;color:#fff;border-left:3px solid #7289da}
        .conteudo{margin-left:250px;flex:1;padding:30px}
        .card{background:#141828;border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid #252a41}
        .status{display:inline-flex;align-items:center;gap:8px;padding:7px 18px;border-radius:25px;font-weight:bold;margin-bottom:15px}
        .status.rodando{background:rgba(67,181,129,.15);color:#43b581}
        .status.parado{background:rgba(240,71,71,.15);color:#f04747}
        .ok{color:#43b581;margin:6px 0}
        .erro{color:#f04747;margin:6px 0}
        .caixa-logs{background:#0b0e17;border:1px solid #252a41;border-radius:8px;padding:15px;font-family:monospace;font-size:13px;max-height:320px;overflow-y:auto;margin-top:15px}
        .botoes{display:flex;gap:12px;margin:20px 0}
        button{padding:12px 22px;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
        .btn-start{background:#43b581;color:#fff}
        .btn-restart{background:#faa61a;color:#111}
        .btn-kill{background:#f04747;color:#fff}
        input{width:100%;padding:14px;background:#0b0e17;border:1px solid #252a41;border-radius:8px;color:#fff;margin:12px 0}
        .oculto{display:none}
    </style>
</head>
<body>
    <aside>
        <h2>⚙️ Painel</h2>
        <button class="btn-menu ativo" onclick="trocarAba('status')">📊 Verificar Bot</button>
        <button class="btn-menu" onclick="trocarAba('console')">💻 Console</button>
    </aside>

    <div class="conteudo">
        <div id="aba-status">
            <div class="card">
                <h2>🔍 Verificação da Pasta</h2>
                <div class="status {{ status_atual }}">{{ status_atual.upper() }}</div>
                {% if erros %}
                    <h3 class="erro">❌ Precisa arrumar:</h3>
                    {% for e in erros %}<p class="erro">{{ e }}</p>{% endfor %}
                {% endif %}
                {% if avisos %}
                    <h3 class="ok">✅ Tudo certo:</h3>
                    {% for a in avisos %}<p class="ok">{{ a }}</p>{% endfor %}
                {% endif %}
                <br>
                <h3>🔑 Token</h3>
                <input type="password" id="token-input" placeholder="Seu token do bot" value="{{ '•' * token_tamanho if token_configurado else '' }}">
                <button onclick="salvarToken()">Salvar Token</button>
                <p id="token-msg"></p>
            </div>
        </div>

        <div id="aba-console" class="oculto">
            <div class="card">
                <h2>💻 Controle</h2>
                <div class="status" id="console-status">{{ status_atual.upper() }}</div>
                <div class="botoes">
                    <button class="btn-start" onclick="startBot()">▶ Start</button>
                    <button class="btn-restart" onclick="restartBot()">🔄 Restart</button>
                    <button class="btn-kill" onclick="killBot()">⬛ Kill</button>
                </div>
                <h3>📋 Logs do Bot</h3>
                <div class="caixa-logs" id="logs">Aguardando Start...</div>
            </div>
        </div>
    </div>

<script>
function trocarAba(nome){
    document.querySelectorAll('.btn-menu').forEach(b=>b.classList.remove('ativo'));
    event.target.classList.add('ativo');
    document.querySelectorAll('[id^=aba-]').forEach(d=>d.classList.add('oculto'));
    document.getElementById('aba-'+nome).classList.remove('oculto');
}

async function salvarToken(){
    const res = await fetch('/api/salvar-token', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token:document.getElementById('token-input').value})
    });
    const d = await res.json();
    document.getElementById('token-msg').textContent = d.msg;
    document.getElementById('token-msg').className = d.ok ? 'ok' : 'erro';
    setTimeout(()=>location.reload(), 1000);
}

async function startBot(){
    const res = await fetch('/api/start', {method:'POST'});
    const d = await res.json();
    if(!d.ok) return alert('CORRIJA PRIMEIRO:\\n' + d.erros.join('\\n'));
    atualizar();
}

async function restartBot(){ await fetch('/api/restart'); atualizar(); }
async function killBot(){ await fetch('/api/kill'); atualizar(); }

async function atualizar(){
    const d = await (await fetch('/api/status')).json();
    const el = document.getElementById('console-status');
    el.textContent = d.status.toUpperCase();
    el.className = 'status ' + d.status;
    if(d.logs.length) document.getElementById('logs').innerHTML = d.logs.map(l=>`<div>${l}</div>`).join('');
}

setInterval(atualizar, 2500);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("🚀 Painel rodando — acesse no navegador")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
