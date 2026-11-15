# -*- coding: utf-8 -*-
"""
keygen.py — GERADOR DE CHAVES (USO EXCLUSIVO DO VENDEDOR)

Fluxo de venda:
1. Cliente paga na Kiwify/Hotmart (R$ 70 / R$ 100 / R$ 140)
2. Você roda este programa e gera a chave do plano + prazo
3. Envia a chave pro cliente, que cola em "⭐ Ativar licença"

Uso:
    python keygen.py                -> modo interativo
    python keygen.py -t 3 -m 1      -> ULTRA válido por 1 mês
    python keygen.py -t 2 -m 12     -> MAX válido por 12 meses
"""
import argparse
import sys

import lic_core as lic


def main():
    ap = argparse.ArgumentParser(description="Gerador de chaves — Estúdio do Cantor")
    ap.add_argument("-t", "--tier", type=int, choices=[1, 2, 3],
                    help="1=PLUS(70) 2=MAX(100) 3=ULTRA(140)")
    ap.add_argument("-m", "--months", type=int, default=1,
                    help="Validade em meses (padrão: 1)")
    args = ap.parse_args()

    tier, months = args.tier, args.months
    if tier is None:
        print("=== GERADOR DE CHAVES — ESTÚDIO DO CANTOR ===")
        print(" 1) PLUS  - R$ 70/mês  (sem limites)")
        print(" 2) MAX   - R$ 100/mês (+ exportação/conversão)")
        print(" 3) ULTRA - R$ 140/mês (+ postagem no YouTube)")
        tier = int(input("Plano [1/2/3]: "))
        months = int(input("Validade em meses [1]: ") or "1")

    key = lic.renew(tier, months)
    exp = lic.validate_key(key)["expiry"]
    br = f"{exp[6:8]}/{exp[4:6]}/{exp[:4]}"
    print("\n--------------------------------------------------")
    print(f" Plano: {lic.TIER_NAMES[tier]}   |   Validade: {br}")
    print(f" CHAVE: {key}")
    print("--------------------------------------------------")
    print("Envie esta chave ao cliente após confirmar o pagamento.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
