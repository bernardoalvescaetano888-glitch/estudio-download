# 🌐 Estúdio do Cantor — Site de Downloads

Repositório de distribuição: **site de download + código fonte + instaladores e versões portáteis** para Windows, macOS e Linux.

## 📥 Downloads

A página `index.html` é o site de download. Os arquivos vêm da aba **Releases**:

| Sistema | Instalador | Portátil |
|---|---|---|
| 🪟 Windows | `EstudioDoCantor-Setup.exe` | `EstudioDoCantor-Portable-Windows.zip` |
| 🍎 macOS | `EstudioDoCantor.dmg` | — |
| 🐧 Linux | `estudiodocantor.deb` | `EstudioDoCantor-Portable-Linux.tar.gz` |

Os executáveis são gerados automaticamente pelo GitHub Actions a cada tag:
```bash
git tag v1.0.0 && git push origin v1.0.0
```
 (~15–30 min, aparecem em **Releases**)

## 🔒 Este repositório é PRIVADO — atenção

**Downloads de repo privado exigem login** na conta autorizada. Para os CLIENTES baixarem, escolha:

1. **Recomendado:** deixar este repo **público** quando for vender
   (Settings → Danger Zone → Change visibility → Public)
2. Alternativa: hospedar `index.html` no Render/Netlify e subir os binários
   da Release em outro lugar (ex.: Netlify Drop)

O código comercial (keygen, licenças) fica no repo privado `estudio-do-cantor`;
aqui vai só o necessário para instalar e rodar.

## 📁 Conteúdo

- `index.html` — site de download
- `app.py`, `lic_core.py`, `requirements.txt` — fonte do app
- `installer.iss` — instalador Windows (Inno Setup)
- `.github/workflows/installers.yml` — build automático dos instaladores

## 🔑 Ativação da licença

Cliente paga (Pix) → recebe a chave por e-mail/Página de pagamento → cola em
"⭐ Ativar licença" no app. Fluxo completo documentado no repo `estudio-do-cantor`.
