# -*- coding: utf-8 -*-
"""
lic_core.py — Sistema de licenças do Estúdio do Cantor
- Teste gratuito de 90 dias (todas as funções)
- Depois do teste: modo RESTRITO (só funções simples, áudio limitado a 60s)
- Planos pagos mensais, ativados por chave:
    1 = PLUS  (R$ 70/mês)  -> sem limites
    2 = MAX   (R$ 100/mês) -> + exportação/conversão (MP3/MP4)
    3 = ULTRA (R$ 140/mês) -> + postagem direta no YouTube
"""
import os
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta

SECRET = b"EDC-2026-ESTUDIO-DO-CANTOR-SECRET-v1-TROQUE-ESTA-CHAVE"
TRIAL_DAYS = 90
RESTRICT_MAX_SECONDS = 60

TIER_NAMES = {1: "PLUS", 2: "MAX", 3: "ULTRA"}
TIER_PRICES = {1: "R$ 70/mês", 2: "R$ 100/mês", 3: "R$ 140/mês"}


def _dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    d = os.path.join(base, "EstudioDoCantor")
    os.makedirs(d, exist_ok=True)
    return d


def _path():
    return os.path.join(_dir(), "license.json")


def init():
    """Cria o registro do teste na primeira execução."""
    if not os.path.exists(_path()):
        save({"created": time.time(), "key": None})


def load():
    try:
        with open(_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"created": time.time(), "key": None}


def save(data):
    with open(_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ------------------------------------------------------------------ chaves
def make_key(tier: int, expiry: str) -> str:
    """Gera chave: EDC{tier}-{YYYYMMDD}-{assinatura}. Uso exclusivo do vendedor (keygen.py)."""
    payload = f"{tier}|{expiry}"
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    return f"EDC{tier}-{expiry}-{sig}"


def validate_key(key: str):
    """Valida formato + assinatura + validade. Retorna dict ou None."""
    try:
        key = key.strip().upper()
        parts = key.split("-")
        if len(parts) != 3 or not parts[0].startswith("EDC"):
            return None
        tier = int(parts[0][3:])
        expiry = parts[1]
        payload = f"{tier}|{expiry}"
        sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
        if sig != parts[2]:
            return None
        if datetime.strptime(expiry, "%Y%m%d") < datetime.now():
            return None
        if tier not in TIER_NAMES:
            return None
        return {"tier": tier, "expiry": expiry}
    except Exception:
        return None


def activate(key: str):
    """Ativa a licença. Retorna (ok, mensagem)."""
    v = validate_key(key)
    if not v:
        return False, "Chave inválida ou expirada."
    d = load()
    d["key"] = key
    save(d)
    return True, f"Licença {TIER_NAMES[v['tier']]} ativada até {v['expiry'][6:8]}/{v['expiry'][4:6]}/{v['expiry'][:4]}."


# ------------------------------------------------------------------ status
def status():
    """Retorna dict com o plano atual:
    {'mode': 'trial'|'licensed'|'restricted', 'tier': 0..3, 'label': str,
     'detail': str, 'full': bool, 'max_seconds': None|60}
    """
    init()
    d = load()
    key = d.get("key")
    if key:
        v = validate_key(key)
        if v:
            t = v["tier"]
            e = v["expiry"]
            br = f"{e[6:8]}/{e[4:6]}/{e[:4]}"
            return {
                "mode": "licensed", "tier": t, "full": True, "max_seconds": None,
                "label": f"{TIER_NAMES[t]} ({TIER_PRICES[t]})",
                "detail": f"Válida até {br}",
            }
        return {
            "mode": "restricted", "tier": 0, "full": False,
            "max_seconds": RESTRICT_MAX_SECONDS,
            "label": "LICENÇA EXPIRADA",
            "detail": "Sua licença venceu. Renove para liberar tudo.",
        }
    created = d.get("created", time.time())
    days_left = TRIAL_DAYS - int((time.time() - created) / 86400)
    if days_left > 0:
        return {
            "mode": "trial", "tier": 3, "full": True, "max_seconds": None,
            "label": f"TESTE GRATUITO — {days_left} dia(s) restante(s)",
            "detail": "Após o teste, ative uma licença para continuar com tudo.",
        }
    return {
        "mode": "restricted", "tier": 0, "full": False,
        "max_seconds": RESTRICT_MAX_SECONDS,
        "label": "VERSÃO RESTRITA",
        "detail": f"Teste encerrado. Funções simples apenas ({RESTRICT_MAX_SECONDS}s de áudio).",
    }


# ------------------------------------------------------------------ permissões
def can_export(st=None):
    """Exportação/conversão MP3-MP4: teste, MAX e ULTRA."""
    s = st or status()
    return s["tier"] >= 2 or s["mode"] == "trial"


def can_youtube(st=None):
    """Postar no YouTube: teste, ULTRA."""
    s = st or status()
    return s["tier"] >= 3 or s["mode"] == "trial"


def renew(tier: int, months: int) -> str:
    """Gera chave de renovação a partir de hoje + X meses (uso do vendedor)."""
    exp = (datetime.now() + timedelta(days=30 * months)).strftime("%Y%m%d")
    return make_key(tier, exp)


if __name__ == "__main__":
    print(status())
