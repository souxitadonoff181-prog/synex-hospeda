import json
import os
import uuid
import secrets
from datetime import datetime, timedelta

ARQUIVO_DADOS = "synex_dados_pro.json"

def _inicializar_arquivo():
    if not os.path.exists(ARQUIVO_DADOS):
        dados_padrao = {
            "chaves": {},
            "vendas": [],
            "config": {"nome_sistema": "SYNEX HOSPEDA"}
        }
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados_padrao, f, ensure_ascii=False, indent=4)

def gerar_chave_owlivery(nome_produto, comprador_discord_id, dias_duracao=30, valor_pago=None):
    _inicializar_arquivo()
    chave = f"SYNEX-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
    expira = datetime.now() + timedelta(days=dias_duracao)
    
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados = json.load(f)
    
    dados["chaves"][chave] = {
        "id": str(uuid.uuid4())[:8],
        "nome": f"Compra: {nome_produto}",
        "chave": chave,
        "duracao_valor": dias_duracao,
        "duracao_tipo": "dias",
        "expira_em": expira.isoformat(),
        "usos_maximo": 1,
        "usos_feitos": 0,
        "usar_hwid": False,
        "hwid_registrado": None,
        "comprador_discord_id": comprador_discord_id,
        "status": "ativa",
        "origem": "owlivery",
        "criada_em": datetime.now().isoformat()
    }
    
    venda = {
        "id": str(uuid.uuid4())[:8],
        "produto": nome_produto,
        "comprador_id": comprador_discord_id,
        "chave": chave,
        "valor": valor_pago,
        "data": datetime.now().isoformat(),
        "plataforma": "Owlivery"
    }
    dados["vendas"].append(venda)
    
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Chave gerada: {chave} | Cliente: {comprador_discord_id}")
    return chave

def verificar_chave(chave):
    _inicializar_arquivo()
    if not os.path.exists(ARQUIVO_DADOS):
        return {"valida": False, "motivo": "sem_dados"}
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        dados = json.load(f)
    if chave not in dados.get("chaves", {}):
        return {"valida": False, "motivo": "nao_existe"}
    info = dados["chaves"][chave]
    return {"valida": info["status"] == "ativa", "nome": info["nome"], "expira_em": info["expira_em"]}
