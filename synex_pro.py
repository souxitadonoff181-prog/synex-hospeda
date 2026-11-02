
from flask import Flask, request, redirect, session
import os
import json
import uuid
import threading
import subprocess
import time
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    secrets.token_hex(32)
)

USUARIO = os.environ.get("PAINEL_USUARIO", "synex")
SENHA = os.environ.get("PAINEL_SENHA", "123")

ARQUIVO_DADOS = "synex_dados_pro.json"

DADOS = {
    "projetos": {},
    "chaves": {},
    "config": {
        "nome_sistema": "SYNEX HOSPEDA",
        "cor_primaria": "#7928ca",
        "cor_secundaria": "#10b981"
    }
}


def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                dados = json.load(f)

            return dados

        except (json.JSONDecodeError, OSError):
            return DADOS.copy()

    return DADOS.copy()


def salvar_dados():
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(DADOS, f, ensure_ascii=False, indent=4)


DADOS.update(carregar_dados())


class GerenciadorBots:

    def __init__(self):
        self.processos = {}
        self.logs = {}
        self.lock = threading.RLock()

        threading.Thread(
            target=self._monitorar,
            daemon=True
        ).start()

    def _monitorar(self):
        while True:
            with self.lock:
                processos = list(self.processos.items())

            for pid, info in processos:
                proc = info["proc"]

                if proc.poll() is not None and info.get("auto_restart", True):
                    self._adicionar_log(
                        pid,
                        "🔴 Caiu — reiniciando..."
                    )

                    info["auto_restart"] = False

                    threading.Thread(
                        target=self._reiniciar,
                        args=(pid,),
                        daemon=True
                    ).start()

            time.sleep(5)

    def _reiniciar(self, pid):
        if pid not in DADOS["projetos"]:
            return

        time.sleep(3)

        proj = DADOS["projetos"][pid]

        self.iniciar(
            pid,
            proj["pasta"],
            proj["comando"]
        )

    def _adicionar_log(self, pid, msg):
        with self.lock:
            if pid not in self.logs:
                self.logs[pid] = []

            self.logs[pid].append(
                f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
            )

            if len(self.logs[pid]) > 300:
                self.logs[pid].pop(0)

    def _ler_saida(self, pid, proc):
        try:
            for linha in proc.stdout:
                linha = linha.rstrip()

                if linha:
                    self._adicionar_log(pid, linha)

        except Exception as e:
            self._adicionar_log(
                pid,
                f"Erro ao ler logs: {str(e)}"
            )

    def iniciar(self, pid, pasta, comando):
        with self.lock:
            if (
                pid in self.processos
                and self.processos[pid]["proc"].poll() is None
            ):
                return False

        try:
            os.makedirs(pasta, exist_ok=True)

            proc = subprocess.Popen(
                comando.split(),
                cwd=pasta,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            with self.lock:
                self.processos[pid] = {
                    "proc": proc,
                    "auto_restart": True
                }

            self._adicionar_log(pid, "✅ BOT ONLINE")

            threading.Thread(
                target=self._ler_saida,
                args=(pid, proc),
                daemon=True
            ).start()

            return True

        except Exception as e:
            self._adicionar_log(
                pid,
                f"❌ Erro: {str(e)}"
            )

            return False

    def parar(self, pid):
        with self.lock:
            if pid not in self.processos:
                return False

            info = self.processos[pid]
            info["auto_restart"] = False
            proc = info["proc"]

        if proc.poll() is None:
            proc.terminate()

        self._adicionar_log(pid, "⏹️ BOT DESLIGADO")

        return True

    def esta_ativo(self, pid):
        with self.lock:
            return (
                pid in self.processos
                and self.processos[pid]["proc"].poll() is None
            )


gerenciador = GerenciadorBots()


def criar_chave(
    nome,
    duracao_valor,
    duracao_tipo,
    limite_usos=1,
    usar_hwid=False,
    comprador_id=None
):
    chave = (
        f"SYNEX-{secrets.token_hex(3).upper()}-"
        f"{secrets.token_hex(3).upper()}-"
        f"{secrets.token_hex(3).upper()}"
    )

    if duracao_tipo == "minutos":
        expira = datetime.now() + timedelta(
            minutes=duracao_valor
        )

    elif duracao_tipo == "anos":
        expira = datetime.now() + timedelta(
            days=duracao_valor * 365
        )

    else:
        expira = datetime.now() + timedelta(
            days=duracao_valor
        )

    DADOS["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome,
        "chave": chave,
        "duracao_valor": duracao_valor,
        "duracao_tipo": duracao_tipo,
        "expira_em": expira.isoformat(),
        "usos_maximo": limite_usos,
        "usos_feitos": 0,
        "usar_hwid": usar_hwid,
        "hwid_registrado": None,
        "comprador_discord_id": comprador_id,
        "status": "ativa",
        "criada_em": datetime.now().isoformat()
    }

    salvar_dados()

    return chave


CSS = """
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
:root{--primaria:#7928ca;--secundaria:#10b981;--aviso:#f59e0b;--erro:#ef4444;--fundo:#05050a;--painel:#0f0f1f;--card:#15152a;--borda:#2a2a4a;--texto:#e0e0ff;--texto-fraco:#8888aa}
body{background:var(--fundo);color:var(--texto);display:flex;min-height:100vh}
.sidebar{width:270px;background:var(--painel);position:fixed;height:100vh;border-right:1px solid var(--borda);padding:20px 0}
.logo{padding:25px 20px;font-size:1.5rem;font-weight:800}
.logo span{background:linear-gradient(90deg,var(--primaria),var(--secundaria));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.sidebar a{display:flex;align-items:center;padding:14px 22px;color:var(--texto-fraco);text-decoration:none;margin:4px 12px;border-radius:8px;border-left:3px solid transparent}
.sidebar a.ativo,.sidebar a:hover{background:rgba(121,40,202,0.1);color:var(--texto);border-left-color:var(--primaria)}
.sidebar a i{margin-right:12px}
.divisor{height:1px;background:var(--borda);margin:20px 25px}
.conteudo{margin-left:270px;padding:30px;flex:1}
.cabecalho{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid var(--borda)}
.cabecalho h2{font-size:1.8rem}
.status-bolha{display:inline-flex;align-items:center;gap:8px;padding:8px 16px;border-radius:20px;font-weight:bold;background:rgba(16,185,129,0.15);color:var(--secundaria)}
.card{background:var(--card);border-radius:12px;padding:25px;margin-bottom:20px;border:1px solid var(--borda)}
.card h3{margin-bottom:18px;color:#d0b0ff;display:flex;align-items:center;gap:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:20px;margin-bottom:25px}
.grid-card{background:var(--card);border-radius:12px;padding:22px;border:1px solid var(--borda);text-align:center}
.grid-card .valor{font-size:2.2rem;font-weight:bold;margin:10px 0}
.btn{padding:11px 22px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:8px;transition:0.2s}
.btn:hover{transform:translateY(-2px)}
.btn.roxo{background:linear-gradient(90deg,var(--primaria),#9333ea);color:white}
.btn.verde{background:var(--secundaria);color:white}
.btn.vermelho{background:var(--erro);color:white}
input,select{width:100%;padding:13px;margin:8px 0 16px;background:rgba(0,0,0,0.3);border:1px solid var(--borda);border-radius:8px;color:white;font-size:0.95rem}
input:focus,select:focus{outline:none;border-color:var(--primaria);box-shadow:0 0 0 3px rgba(121,40,202,0.15)}
label{color:var(--texto-fraco);font-weight:500;margin-top:10px;display:block}
.badge{padding:5px 12px;border-radius:20px;font-size:0.75rem;font-weight:bold;text-transform:uppercase}
.ativa{background:rgba(16,185,129,0.15);color:var(--secundaria)}
.tabela{width:100%;border-collapse:collapse;margin-top:15px}
.tabela th,.tabela td{padding:14px 16px;text-align:left;border-bottom:1px solid var(--borda)}
.tabela th{color:var(--texto-fraco);font-weight:600;font-size:0.85rem}
"""


def menu(aba_atual):

    def ativo(pag):
        return "ativo" if aba_atual == pag else ""

    return f'''<div class="sidebar">
        <div class="logo"><span>SYNEX</span> HOSPEDA</div>
        <a href="/" class="{ativo("home")}"><i>📊</i> Painel</a>
        <a href="/bots" class="{ativo("bots")}"><i>🤖</i> Meus Bots</a>
        <a href="/chaves" class="{ativo("chaves")}"><i>🔑</i> Gerenciar Chaves</a>
        <a href="/sair" style="color:var(--erro)"><i>🚪</i> Sair</a>
    </div>'''


def pagina(corpo, aba="home"):
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SYNEX HOSPEDA</title>
    <style>{CSS}</style>
</head>
<body>
    {menu(aba)}
    <div class="conteudo">{corpo}</div>
</body>
</html>'''


def logado():
    return 'logado' in session and session['logado']


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        if (
            request.form.get('usuario') == USUARIO
            and request.form.get('senha') == SENHA
        ):
            session['logado'] = True
            return redirect('/')

        return '''
        <p style="color:#ef4444;text-align:center;margin-top:40px">
            ❌ Usuário ou senha incorretos
        </p>
        '''

    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Login — SYNEX</title>
    <style>
        body{background:#05050a;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif}
        .caixa{background:#0f0f1f;padding:50px;border-radius:16px;border:1px solid rgba(121,40,202,0.3);width:100%;max-width:420px}
        h1 span{background:linear-gradient(90deg,#7928ca,#10b981);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        input{width:100%;padding:15px;margin:10px 0;background:rgba(0,0,0,0.4);border:1px solid #2a2a4a;border-radius:8px;color:white;font-size:1rem}
        button{width:100%;padding:15px;background:linear-gradient(90deg,#7928ca,#10b981);color:white;border:none;border-radius:8px;font-weight:bold;font-size:1.1rem;margin-top:15px;cursor:pointer}
        label{color:#8888aa}
    </style>
</head>
<body>
<div class="caixa">
    <h1><span>SYNEX</span> HOSPEDA</h1>
    <form method="POST">
        <label>Usuário</label>
        <input name="usuario" value="synex">
        <label>Senha</label>
        <input type="password" name="senha">
        <button>ENTRAR</button>
    </form>
</div>
</body>
</html>'''


@app.route('/sair')
def sair():
    session.clear()
    return redirect('/login')


@app.route('/')
def home():

    if not logado():
        return redirect('/login')

    total_chaves = len(DADOS["chaves"])

    ativas = sum(
        1 for c in DADOS["chaves"].values()
        if c["status"] == "ativa"
    )

    total_bots = len(DADOS["projetos"])

    bots_on = sum(
        1 for p in DADOS["projetos"]
        if gerenciador.esta_ativo(p)
    )

    corpo = f'''
        <div class="cabecalho">
            <h2>📊 PAINEL DE CONTROLE</h2>
            <span class="status-bolha">● SISTEMA ONLINE</span>
        </div>

        <div class="grid">
            <div class="grid-card">
                <h4>🔑 Chaves Criadas</h4>
                <div class="valor">{total_chaves}</div>
            </div>

            <div class="grid-card">
                <h4>✅ Ativas</h4>
                <div class="valor" style="color:var(--secundaria)">
                    {ativas}
                </div>
            </div>

            <div class="grid-card">
                <h4>🤖 Bots</h4>
                <div class="valor">{total_bots}</div>
            </div>

            <div class="grid-card">
                <h4>🟢 Online</h4>
                <div class="valor" style="color:var(--secundaria)">
                    {bots_on}
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Bem-vindo!</h3>
            <p style="color:var(--texto-fraco);line-height:1.8">
                Use o menu para gerenciar seus bots e gerar chaves de acesso.
            </p>
        </div>
    '''

    return pagina(corpo, "home")


@app.route('/bots', methods=['GET', 'POST'])
def bots():

    if not logado():
        return redirect('/login')

    if request.method == 'POST':

        pid = str(uuid.uuid4())[:8]

        nome = request.form.get(
            'nome',
            'Bot Sem Nome'
        )

        DADOS["projetos"][pid] = {
            "nome": nome,
            "pasta": f"projetos/{pid}",
            "comando": "python bot.py"
        }

        salvar_dados()

        return redirect('/bots')

    lista = ""

    for pid, b in DADOS["projetos"].items():

        on = gerenciador.esta_ativo(pid)

        status = "✅ ONLINE" if on else "⏹️ DESLIGADO"

        acao = (
            f'<a href="/bot/desligar/{pid}" class="btn vermelho">Desligar</a>'
            if on else
            f'<a href="/bot/ligar/{pid}" class="btn verde">Ligar</a>'
        )

        lista += f'''<div style="padding:15px;background:rgba(0,0,0,0.3);border-radius:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center">
            <div>
                <strong>{b["nome"]}</strong><br>
                <small style="color:var(--texto-fraco)">{pid}</small>
            </div>
            <div style="text-align:right">
                {status}<br>
                {acao}
            </div>
        </div>'''

    corpo = f'''
        <div class="cabecalho">
            <h2>🤖 MEUS BOTS</h2>
        </div>

        <div class="card">
            <h3>Adicionar Novo Bot</h3>

            <form method="POST">
                <label>Nome do Bot:</label>
                <input name="nome" placeholder="Bot de Vendas" required>

                <button class="btn roxo">Adicionar</button>
            </form>
        </div>

        <div class="card">
            <h3>Lista ({len(DADOS["projetos"])})</h3>
            {lista if lista else '<p>Nenhum bot cadastrado.</p>'}
        </div>
    '''

    return pagina(corpo, "bots")


@app.route('/bot/ligar/<pid>')
def ligar_bot(pid):

    if not logado():
        return redirect('/login')

    if pid in DADOS["projetos"]:

        projeto = DADOS["projetos"][pid]

        gerenciador.iniciar(
            pid,
            projeto["pasta"],
            projeto["comando"]
        )

    return redirect('/bots')


@app.route('/bot/desligar/<pid>')
def desligar_bot(pid):

    if not logado():
        return redirect('/login')

    gerenciador.parar(pid)

    return redirect('/bots')


@app.route('/chaves', methods=['GET', 'POST'])
def chaves():

    if not logado():
        return redirect('/login')

    if request.method == 'POST':

        try:
            nome = request.form.get('nome', '').strip()
            duracao_valor = int(request.form.get('duracao_valor'))
            duracao_tipo = request.form.get('duracao_tipo')
            limite_usos = int(request.form.get('limite_usos', 1))

            if not nome:
                return redirect('/chaves')

            if duracao_valor < 1 or limite_usos < 1:
                return redirect('/chaves')

            if duracao_tipo not in ["dias", "minutos", "anos"]:
                return redirect('/chaves')

            criar_chave(
                nome=nome,
                duracao_valor=duracao_valor,
                duracao_tipo=duracao_tipo,
                limite_usos=limite_usos,
                usar_hwid=request.form.get('usar_hwid') == 'on'
            )

            return redirect('/chaves')

        except (ValueError, TypeError):
            return redirect('/chaves')

    linhas = ""

    for chave, dados in DADOS["chaves"].items():

        linhas += f'''<tr>
            <td>{dados["nome"]}</td>
            <td><code>{chave[:15]}...</code></td>
            <td>{dados["duracao_valor"]} {dados["duracao_tipo"]}</td>
            <td>{dados["usos_feitos"]}/{dados["usos_maximo"]}</td>
            <td><span class="badge ativa">{dados["status"]}</span></td>
        </tr>'''

    corpo = f'''
        <div class="cabecalho">
            <h2>🔑 GERENCIAR CHAVES</h2>
        </div>

        <div class="card">
            <h3>Criar Nova Chave</h3>

            <form method="POST">
                <label>Nome:</label>
                <input name="nome" placeholder="Plano Premium" required>

                <label>Duração (valor):</label>
                <input type="number" name="duracao_valor" value="30" min="1" required>

                <label>Tipo:</label>
                <select name="duracao_tipo">
                    <option value="dias">Dias</option>
                    <option value="minutos">Minutos</option>
                    <option value="anos">Anos</option>
                </select>

                <label>Limite de usos:</label>
                <input type="number" name="limite_usos" value="1" min="1" required>

                <label>
                    <input type="checkbox" name="usar_hwid">
                    Bloquear por HWID
                </label>

                <button class="btn roxo">Gerar Chave</button>
            </form>
        </div>

        <div class="card">
            <h3>Chaves cadastradas ({len(DADOS["chaves"])})</h3>

            <table class="tabela">
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Chave</th>
                        <th>Duração</th>
                        <th>Usos</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    {linhas if linhas else '<tr><td colspan="5">Nenhuma chave cadastrada.</td></tr>'}
                </tbody>
            </table>
        </div>
    '''

    return pagina(corpo, "chaves")


@app.route('/health')
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )
