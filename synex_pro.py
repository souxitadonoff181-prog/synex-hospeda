import os
import re
import io
import json
import threading
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

# ==============================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "config.json"

# ==============================================
# CONFIGURAÇÕES PADRÃO
# ==============================================
DEFAULT = {
    "panel_title": "Central de Atendimento",
    "panel_description": "🎟️ **CENTRAL DE ATENDIMENTO — TICKET**\n\nOlá! Seja bem-vindo(a) ao nosso suporte! 👋\n\n📩 **Abra um ticket para receber atendimento personalizado.**\nNossa equipe está pronta para ajudar com dúvidas, compras, suporte técnico e muito mais.\n\n⚠️ **Regras:**\n• Explique sua solicitação com clareza.\n• Envie prints ou comprovantes quando necessário.\n• Aguarde nossa resposta com paciência.\n\n✅ Estamos aqui para ajudar!\nObrigado pela confiança! 💙\n\n🔒 Mantenha o ticket aberto até resolver tudo.",
    "confirm_title": "Antes de abrir...",
    "confirm_description": "Confira os termos e informações acima.\nSe ainda tem dúvida, é só confirmar abaixo que atendemos.",
    "ticket_title": "Suporte",
    "ticket_description": "Olá {user}, bem-vindo(a) ao seu atendimento!\n\nAvisamos a equipe, em breve alguém vai responder.\nDescreva o que precisa com detalhes.\n\n🔒 Mantenha este canal aberto até resolver.",
    "redeem_title": "Resgate de Item",
    "redeem_description": "Olá {user}, este é seu ticket de resgate!\n\nInforme o código ou detalhes do item para verificarmos.",
    "categories": {"suporte": None, "resgatar": None},
    "staff_roles": [],
    "log_channel": None,
    "welcome_channel": None,
    "welcome_role": None,
    "welcome_message": "Salve {mention}! Bem-vindo(a) à **Synex Store**! 💙",
    "ticket_count": 0
}

def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT, f, ensure_ascii=False, indent=4)
        return DEFAULT
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    final = DEFAULT.copy()
    final.update(cfg)
    final["categories"] = {**DEFAULT["categories"], **cfg.get("categories", {})}
    return final

cfg = carregar_config()

def salvar_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)

# ==============================================
# FUNÇÕES AUXILIARES
# ==============================================
def e_equipe(membro: discord.Member) -> bool:
    if membro.guild_permissions.administrator or membro.guild_permissions.manage_channels:
        return True
    return any(role.id in cfg["staff_roles"] for role in membro.roles)

def dono_do_ticket(canal):
    if canal.topic:
        m = re.search(r"usuario_id=(\d+)", canal.topic)
        return int(m.group(1)) if m else None
    return None

def tipo_do_ticket(canal):
    if canal.topic:
        m = re.search(r"tipo=(\w+)", canal.topic)
        return m.group(1) if m else None
    return None

def atualizar_topico(canal, **kwargs):
    partes = {}
    if canal.topic:
        for p in canal.topic.split(";"):
            if "=" in p:
                k, v = p.split("=", 1)
                partes[k] = v
    for k, v in kwargs.items():
        partes[k] = str(v)
    return ";".join(f"{k}={v}" for k, v in partes.items())

async def registrar_log(guild, texto):
    if not cfg["log_channel"]:
        return
    canal = guild.get_channel(cfg["log_channel"])
    if canal:
        try:
            await canal.send(texto)
        except:
            pass

async def arquivo_transcricao(canal):
    linhas = []
    async for msg in canal.history(limit=None, oldest_first=True):
        data = msg.created_at.strftime("%d/%m/%Y %H:%M")
        linhas.append(f"[{data}] {msg.author}:\n{msg.content}\n")
    texto = "\n".join(linhas) or "Sem mensagens."
    return discord.File(io.StringIO(texto), filename=f"transcricao-{canal.name}.txt")

# ==============================================
# VIEWS E BOTÕES
# ==============================================
class PainelEscolha(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Suporte", style=discord.ButtonStyle.blurple, emoji="📩", custom_id="ticket:suporte")
    async def suporte(self, interaction: discord.Interaction, botao: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(title=cfg["confirm_title"], description=cfg["confirm_description"], color=discord.Color.blurple()),
            view=ConfirmarAbertura("suporte"),
            ephemeral=True
        )

    @discord.ui.button(label="Resgatar Item", style=discord.ButtonStyle.green, emoji="🎁", custom_id="ticket:resgatar")
    async def resgatar(self, interaction: discord.Interaction, botao: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(title=cfg["confirm_title"], description=cfg["confirm_description"], color=discord.Color.blurple()),
            view=ConfirmarAbertura("resgatar"),
            ephemeral=True
        )

class ConfirmarAbertura(discord.ui.View):
    def __init__(self, tipo):
        super().__init__(timeout=120)
        self.tipo = tipo

    @discord.ui.button(label="Confirmar Abertura", style=discord.ButtonStyle.green, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, botao: discord.ui.Button):
        if not interaction.guild:
            return

        # Verifica se já tem aberto
        ja_aberto = any(
            c for c in interaction.guild.text_channels
            if dono_do_ticket(c) == interaction.user.id and tipo_do_ticket(c) == self.tipo
        )
        if ja_aberto:
            await interaction.response.send_message("Você já tem um ticket aberto!", ephemeral=True)
            return

        categoria_id = cfg["categories"].get(self.tipo)
        categoria = interaction.guild.get_channel(categoria_id) if categoria_id else None

        cfg["ticket_count"] += 1
        salvar_config()
        prefixo = "suporte" if self.tipo == "suporte" else "resgate"
        nome = f"{prefixo}-{interaction.user.name}-{cfg['ticket_count']}"

        # Permissões
        perm = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        for rid in cfg["staff_roles"]:
            r = interaction.guild.get_role(rid)
            if r:
                perm[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        canal = await interaction.guild.create_text_channel(
            nome,
            category=categoria,
            topic=f"usuario_id={interaction.user.id};tipo={self.tipo};status=aberto",
            overwrites=perm
        )

        # Mensagem inicial
        if self.tipo == "suporte":
            titulo, desc = cfg["ticket_title"], cfg["ticket_description"].replace("{user}", interaction.user.mention)
        else:
            titulo, desc = cfg["redeem_title"], cfg["redeem_description"].replace("{user}", interaction.user.mention)

        embed = discord.Embed(title=titulo, description=desc, color=discord.Color.blurple())
        await canal.send(embed=embed, view=PainelControle())
        await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)
        await registrar_log(interaction.guild, f"📩 Ticket aberto: {canal.mention} por {interaction.user}")
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, botao: discord.ui.Button):
        await interaction.response.send_message("Abertura cancelada.", ephemeral=True)
        self.stop()

class PainelControle(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="controle:fechar")
    async def fechar(self, interaction: discord.Interaction, botao: discord.ui.Button):
        if not e_equipe(interaction.user) and dono_do_ticket(interaction.channel) != interaction.user.id:
            await interaction.response.send_message("Apenas a equipe ou o dono pode fechar.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Fechando ticket...")
        arq = await arquivo_transcricao(interaction.channel)
        await registrar_log(
            interaction.guild,
            f"🔒 Ticket fechado: {interaction.channel.name} por {interaction.user}",
        )
        if cfg["log_channel"]:
            log = interaction.guild.get_channel(cfg["log_channel"])
            if log:
                await log.send(file=arq)
        await interaction.channel.delete()

    @discord.ui.button(label="Marcar Resolvido", style=discord.ButtonStyle.green, emoji="✅", custom_id="controle:resolvido")
    async def resolvido(self, interaction: discord.Interaction, botao: discord.ui.Button):
        if not e_equipe(interaction.user):
            await interaction.response.send_message("Apenas a equipe pode usar isso.", ephemeral=True)
            return
        await interaction.response.send_message(f"✅ Ticket marcado como resolvido por {interaction.user.mention}")
        novo_topico = atualizar_topico(interaction.channel, status="resolvido")
        await interaction.channel.edit(topic=novo_topico)

# ==============================================
# BOT
# ==============================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    bot.add_view(PainelEscolha())
    bot.add_view(PainelControle())
    try:
        synced = await bot.tree.sync()
        print(f"✅ {bot.user} online! | {len(synced)} comandos sincronizados")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")

@bot.tree.command(name="painel", description="Envia o painel de abertura de tickets")
async def painel(interaction: discord.Interaction):
    if not e_equipe(interaction.user):
        await interaction.response.send_message("Sem permissão.", ephemeral=True)
        return
    embed = discord.Embed(
        title=cfg["panel_title"],
        description=cfg["panel_description"],
        color=discord.Color.blurple()
    )
    await interaction.channel.send(embed=embed, view=PainelEscolha())
    await interaction.response.send_message("Painel enviado!", ephemeral=True)

@bot.tree.command(name="configurar", description="Configurações do sistema")
@app_commands.describe(
    categoria_suporte="Categoria ID",
    categoria_resgate="Categoria ID",
    cargo_equipe="ID do cargo da equipe",
    canal_logs="ID do canal de logs"
)
async def configurar(
    interaction: discord.Interaction,
    categoria_suporte: str = None,
    categoria_resgate: str = None,
    cargo_equipe: str = None,
    canal_logs: str = None
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Apenas administradores.", ephemeral=True)
        return

    if categoria_suporte:
        cfg["categories"]["suporte"] = int(categoria_suporte)
    if categoria_resgate:
        cfg["categories"]["resgatar"] = int(categoria_resgate)
    if cargo_equipe:
        if int(cargo_equipe) not in cfg["staff_roles"]:
            cfg["staff_roles"].append(int(cargo_equipe))
    if canal_logs:
        cfg["log_channel"] = int(canal_logs)

    salvar_config()
    await interaction.response.send_message("✅ Configurações salvas!", ephemeral=True)

@bot.event
async def on_member_join(membro):
    if cfg["welcome_channel"]:
        canal = membro.guild.get_channel(cfg["welcome_channel"])
        if canal:
            msg = cfg["welcome_message"].replace("{mention}", membro.mention)
            await canal.send(msg)
    if cfg["welcome_role"]:
        cargo = membro.guild.get_role(cfg["welcome_role"])
        if cargo:
            await membro.add_roles(cargo)

if __name__ == "__main__":
    if not TOKEN:
        print("ERRO: TOKEN não encontrado! Verifique o arquivo .env")
    else:
        bot.run(TOKEN)