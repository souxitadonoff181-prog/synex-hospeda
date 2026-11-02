import os
import re
import io
import json
import threading
from datetime import datetime
from flask import Flask, render_template_string
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# ==============================================
# INICIALIZAÇÃO
# ==============================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_PATH = "config.json"

app = Flask(__name__)
app.secret_key = "synex_site_2026"
bot = None
bot_rodando = False

# ==============================================
# SEU CÓDIGO ORIGINAL — TUDO EXATAMENTE COMO VOCÊ ENVIOU
# ==============================================
DEFAULT = {
    "panel_title": "Central de Atendimento",
    "panel_description": "🎟️ **CENTRAL DE ATENDIMENTO — TICKET**\n\nOlá! Seja bem-vindo(a) ao nosso suporte! 👋\n\n📩 **Abra um ticket para receber atendimento personalizado.**\nNossa equipe está pronta para ajudar você com dúvidas, compras, suporte técnico ou qualquer outro assunto relacionado aos nossos serviços.\n\n⚠️ **Regras de atendimento:**\n• Explique sua solicitação com clareza.\n• Envie prints ou comprovantes, se necessário.\n• Aguarde um membro da equipe responder.\n• Evite marcar a equipe repetidamente.\n\n✅ Estamos aqui para ajudar!\nObrigado pela preferência e pela confiança. 💙\n\n🔒 Mantenha o ticket aberto até que seu atendimento seja concluído.",
    "confirm_title": "Antes de abrir um ticket...",
    "confirm_description": "Antes de continuar, confira os termos da loja e as informações do produto.\nGeralmente elas já trazem tudo o que você precisa saber.\n\nSe ainda ficou com alguma dúvida, é só confirmar abaixo que a equipe te atende.",
    "ticket_title": "Suporte global",
    "ticket_description": "Olá {user}, seja bem-vindo(a) ao seu atendimento!\n\nNossa equipe foi notificada e irá atendê-lo em breve.\nExplique sua solicitação com detalhes e envie imagens, se necessário.\n\n🔒 **Mantenha este ticket aberto até a conclusão do atendimento.**",
    "redeem_title": "Resgatar item",
    "redeem_description": "Olá {user}, este é seu ticket para resgate de item!\n\nInforme qual item deseja resgatar e envie as informações necessárias.\nNossa equipe irá verificar sua solicitação.",
    "categories": {"suporte": None, "resgatar": None},
    "staff_roles": [],
    "log_channel": None,
    "welcome_channel": None,
    "welcome_role": None,
    "welcome_message": "Salve {mention}! Seja muito bem-vindo(a) à **Synex Store**. Aproveite tudo o que temos a oferecer! 💙",
    "ticket_count": 0
}

def load_config():
    if not os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT, f, ensure_ascii=False, indent=4)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, json.JSONDecodeError):
        saved = {}
    data = DEFAULT.copy()
    data.update(saved)
    data["categories"] = {**DEFAULT["categories"], **saved.get("categories", {})}
    return data

cfg = load_config()

def save_config():
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)

def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_channels:
        return True
    allowed = set(cfg.get("staff_roles", []))
    return any(role.id in allowed for role in getattr(member, "roles", []))

def ticket_owner(channel):
    match = re.search(r"owner=(\d+)", channel.topic or "")
    return int(match.group(1)) if match else None

def ticket_kind(channel):
    match = re.search(r"kind=(suporte|resgatar)", channel.topic or "")
    return match.group(1) if match else None

def topic_value(channel, key, default="0"):
    match = re.search(rf"(?:^|;){re.escape(key)}=([^;]+)", channel.topic or "")
    return match.group(1) if match else default

def update_topic(channel, **values):
    parts = {}
    for item in (channel.topic or "").split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            parts[k] = v
    parts.update({k: str(v) for k, v in values.items()})
    return ";".join(f"{k}={v}" for k, v in parts.items())

async def send_log(guild, text):
    channel_id = cfg.get("log_channel")
    channel = guild.get_channel(channel_id) if channel_id else None
    if channel:
        try:
            await channel.send(text)
        except discord.HTTPException:
            pass

async def transcript_file(channel: discord.TextChannel):
    rows = []
    async for msg in channel.history(limit=None, oldest_first=True):
        stamp = msg.created_at.strftime("%d/%m/%Y %H:%M:%S UTC")
        content = msg.clean_content or ""
        if msg.attachments:
            content += " | Anexos: " + ", ".join(a.url for a in msg.attachments)
        if msg.embeds:
            content += " | [Mensagem com embed]"
        rows.append(f"[{stamp}] {msg.author} ({msg.author.id}): {content}")
    text = "\n".join(rows) if rows else "Nenhuma mensagem registrada."
    return discord.File(io.BytesIO(text.encode("utf-8")), filename=f"transcript-{channel.name}.txt")

async def get_user(user_id):
    try:
        return await bot.fetch_user(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None

async def dm_user(user_id, text):
    try:
        user = await get_user(user_id)
        if user:
            await user.send(text)
            return True
    except:
        return False

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte global", value="suporte",
                                 description="Dúvidas, compras e suporte técnico", emoji="📩"),
            discord.SelectOption(label="Resgatar item", value="resgatar",
                                 description="Solicitar o resgate de um item", emoji="🎁")
        ]
        super().__init__(placeholder="Selecione uma opção de atendimento",
                         min_values=1, max_values=1, options=options,
                         custom_id="synex:panel:select")

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title=cfg["confirm_title"],
                              description=cfg["confirm_description"],
                              color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed,
                                                view=ConfirmView(self.values[0]),
                                                ephemeral=True)

class ConfirmView(discord.ui.View):
    def __init__(self, kind):
        super().__init__(timeout=300)
        self.kind = kind

    @discord.ui.button(label="Abrir ticket mesmo assim", style=discord.ButtonStyle.success,
                       emoji="✔", custom_id="synex:confirm:open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("Use este botão em um servidor.", ephemeral=True)

        already = next((c for c in guild.text_channels
                        if ticket_owner(c) == interaction.user.id and ticket_kind(c) == self.kind), None)
        if already:
            return await interaction.response.send_message(
                f"Você já tem um ticket aberto: {already.mention}", ephemeral=True)

        category_id = cfg["categories"].get(self.kind)
        category = guild.get_channel(category_id) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            category = None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True)
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True,
                read_message_history=True, manage_channels=True)
        for role_id in cfg.get("staff_roles", []):
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True,
                    read_message_history=True, manage_channels=True)

        cfg["ticket_count"] = int(cfg.get("ticket_count", 0)) + 1
        save_config()
        prefix = "suporte" if self.kind == "suporte" else "resgate"
        safe_user = re.sub(r"[^a-z0-9-]", "-", interaction.user.name.lower()).strip("-")[:35] or "usuario"
        name = f"{prefix}-{safe_user}-{cfg['ticket_count']:04d}"
        topic = f"owner={interaction.user.id};kind={self.kind};claimed=0;invalid=0"
        try:
            channel = await guild.create_text_channel(name=name, category=category,
                overwrites=overwrites, topic=topic, reason=f"Ticket aberto por {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "Não consegui criar o canal. Dê ao bot a permissão **Gerenciar canais**.", ephemeral=True)

        if self.kind == "suporte":
            title, description = cfg["ticket_title"], cfg["ticket_description"]
        else:
            title, description = cfg["redeem_title"], cfg["redeem_description"]
        description = description.replace("{user}", interaction.user.mention)
        embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
        embed.set_footer(text=f"Synex Store • Ticket #{cfg['ticket_count']}")
        staff_tags = " ".join(f"<@&{rid}>" for rid in cfg["staff_roles"] if guild.get_role(rid))
        await channel.send(content=f"{interaction.user.mention} {staff_tags}".strip(),
                           embed=embed, view=TicketActionsView())
        await interaction.response.edit_message(content=f"✅ Ticket criado: {channel.mention}",
                                                embed=None, view=None)
        await send_log(guild, f"🎫 Ticket aberto: {channel.mention} • {interaction.user.mention} • {self.kind}")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary, custom_id="synex:confirm:cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Abertura cancelada.", embed=None, view=None)

class TicketActionsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketActionSelect())

class TicketActionSelect(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label="Assumir ticket", description="Você passa a atender este ticket", value="claim", emoji="✅"),
            discord.SelectOption(label="Assumir e remover outros staff", description="Assume e oculta dos demais", value="claim_exclusive", emoji="👥"),
            discord.SelectOption(label="Notificar usuário", description="Envia mensagem privada", value="notify", emoji="💬"),
            discord.SelectOption(label="Renomear ticket", description="Altera o nome do canal", value="rename", emoji="📋"),
            discord.SelectOption(label="Adicionar membro", description="Adiciona alguém ao atendimento", value="add", emoji="➕"),
            discord.SelectOption(label="Remover membro", description="Remove alguém do atendimento", value="remove", emoji="🗑️"),
            discord.SelectOption(label="Invalidar valor do ticket", description="Marca sem pagamento", value="invalidate", emoji="🧾"),
            discord.SelectOption(label="Fechar ticket", description="Encerra e envia transcript", value="close", emoji="❌")
        ]
        super().__init__(placeholder="Selecione uma ação", min_values=1, max_values=1,
                         options=opts, custom_id="synex:ticket:actions")

    async def callback(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or ticket_owner(channel) is None:
            return await interaction.response.send_message("Este canal não é um ticket.", ephemeral=True)
        action = self.values[0]
        staff = is_staff(interaction.user)
        if action in {"claim", "claim_exclusive", "notify", "rename", "add", "remove", "invalidate", "close"} and not staff:
            return await interaction.response.send_message("Somente a equipe pode usar esta ação.", ephemeral=True)

        owner_id = ticket_owner(channel)
        if action in {"claim", "claim_exclusive"}:
            if topic_value(channel, "claimed") != "0":
                return await interaction.response.send_message("Este ticket já foi assumido.", ephemeral=True)
            await channel.edit(topic=update_topic(channel, claimed=interaction.user.id))
            if action == "claim_exclusive":
                for rid in cfg["staff_roles"]:
                    role = interaction.guild.get_role(rid)
                    if role and role not in interaction.user.roles:
                        await channel.set_permissions(role, view_channel=False)
            await interaction.response.send_message(f"✅ {interaction.user.mention} assumiu este ticket.")
            sent = await dm_user(owner_id, f"👋 Seu ticket **{channel.name}** foi assumido por **{interaction.user}**.")
            if not sent:
                await channel.send("⚠️ Não foi possível enviar DM ao usuário.")
            await send_log(interaction.guild, f"🙋 {interaction.user.mention} assumiu {channel.mention}")
        elif action == "notify":
            sent = await dm_user(owner_id, f"💬 Atualização no ticket: {channel.jump_url}")
            await interaction.response.send_message("✅ Usuário notificado." if sent else "Não consegui enviar DM.", ephemeral=True)
        elif action == "rename":
            await interaction.response.send_modal(RenameModal())
        elif action in {"add", "remove"}:
            await interaction.response.send_modal(MemberModal(action == "add"))
        elif action == "invalidate":
            new_val = "0" if topic_value(channel, "invalid") == "1" else "1"
            await channel.edit(topic=update_topic(channel, invalid=new_val))
            await interaction.response.send_message(
                "🧾 Marcado como sem pagamento." if new_val == "1" else "🧾 Marcação removida.", ephemeral=True)
        elif action == "
