#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================
  ESTÚDIO DO CANTOR  v1.0.0
================================================================
Tudo-em-um para cantores, músicos e criadores:
  1) Separar voz × instrumental   (Demucs, IA local)
  2) Mudar o tom da música        (librosa)
  3) Gerar legendas/transcrição   (Whisper, IA local)
  +) Exportar MP3/MP4             (plano MAX+)
  +) Postar no YouTube            (plano ULTRA)

Planos: Teste 90 dias grátis -> restrito | PLUS R$70 | MAX R$100 | ULTRA R$140
Execução 100% local (offline), sem enviar áudio para nuvem.
================================================================
"""
import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
import traceback
import importlib.util

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lic_core as lic

VERSION = "1.0.0"
APP_NAME = "Estúdio do Cantor"
STORE_URL = "https://SEU-SERVIDOR.onrender.com/plans"  # <- troque pela URL do seu servidor MP (rota /plans)

C = {
    "bg":     "#0f1117",
    "panel":  "#161a24",
    "panel2": "#1c2130",
    "entry":  "#10131b",
    "text":   "#e8eaf0",
    "muted":  "#8a93a5",
    "accent": "#3ddc97",
    "accent2":"#5aa7ff",
    "warn":   "#ffb454",
    "danger": "#ff5f7e",
}

FFMPEG = shutil.which("ffmpeg")


def has_mod(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def srt_ts(sec: float) -> str:
    sec = max(0.0, float(sec))
    h = int(sec // 3600); m = int(sec % 3600 // 60); s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"🎛 {APP_NAME} v{VERSION}")
        self.geometry("1040x720")
        self.minsize(960, 660)
        self.configure(bg=C["bg"])

        self.sep_results = []
        self.pitch_result = None
        self.srt_result = None

        self._build_header()
        self._build_banner()
        self._build_tabs()
        self._build_statusbar()
        self.show_tab("sep")
        self.after(200, self.refresh_license_ui)

    # ------------------------------------------------------------ UI base
    def _build_header(self):
        h = tk.Frame(self, bg=C["panel"])
        h.pack(fill="x")
        tk.Label(h, text="🎛  ESTÚDIO DO CANTOR", font=("Segoe UI", 16, "bold"),
                 bg=C["panel"], fg=C["accent"]).pack(side="left", padx=16, pady=10)
        self.lbl_lic = tk.Label(h, text="", font=("Segoe UI", 10, "bold"),
                                bg=C["panel"], fg=C["text"])
        self.lbl_lic.pack(side="right", padx=8)
        tk.Button(h, text="⭐ Ativar licença", command=self.show_activate_dialog,
                  bg=C["panel2"], fg=C["text"], relief="flat",
                  activebackground=C["accent"], font=("Segoe UI", 9, "bold")
                  ).pack(side="right", padx=6)
        tk.Button(h, text="🛒 Comprar plano", command=lambda: self._open_url(STORE_URL),
                  bg=C["panel2"], fg=C["text"], relief="flat", font=("Segoe UI", 9, "bold")
                  ).pack(side="right", padx=6)

    def _build_banner(self):
        self.banner = tk.Label(self, text="", font=("Segoe UI", 10),
                               bg=C["warn"], fg="#1a1a1a", anchor="w", padx=12)

    def _build_tabs(self):
        bar = tk.Frame(self, bg=C["bg"])
        bar.pack(fill="x", pady=(8, 0))
        self.tab_buttons = {}
        self.tab_frames = {}
        for key, label in (("sep", "🎤 Separar voz"), ("tom", "🎹 Mudar tom"),
                           ("srt", "📝 Legendas")):
            b = tk.Button(bar, text=label, font=("Segoe UI", 11, "bold"),
                          relief="flat", bd=0, padx=18, pady=8,
                          command=lambda k=key: self.show_tab(k))
            b.pack(side="left", padx=(10, 4))
            self.tab_buttons[key] = b
        self.container = tk.Frame(self, bg=C["bg"])
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_frames["sep"] = self._build_separar(self.container)
        self.tab_frames["tom"] = self._build_tom(self.container)
        self.tab_frames["srt"] = self._build_legendas(self.container)

    def show_tab(self, key):
        for k, f in self.tab_frames.items():
            f.pack_forget() if k != key else f.pack(fill="both", expand=True)
        for k, b in self.tab_buttons.items():
            on = (k == key)
            b.configure(bg=C["panel2"] if on else C["bg"],
                        fg=C["accent"] if on else C["muted"])

    def _build_statusbar(self):
        self.status = tk.Label(self, text="Pronto. 🎵", anchor="w",
                               bg=C["panel"], fg=C["muted"], padx=12)
        self.status.pack(fill="x", side="bottom")

    def _mk_field(self, parent, label):
        row = tk.Frame(parent, bg=C["panel"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, width=22, anchor="w", bg=C["panel"],
                 fg=C["muted"], font=("Segoe UI", 9)).pack(side="left")
        var = tk.StringVar()
        e = tk.Entry(row, textvariable=var, bg=C["entry"], fg=C["text"],
                     insertbackground=C["text"], relief="flat")
        e.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        return row, var

    def _mk_btn(self, parent, text, cmd, color, fg="#10131b"):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg=fg,
                         relief="flat", font=("Segoe UI", 10, "bold"),
                         activebackground=color, cursor="hand2")

    def _mk_panel(self, parent):
        p = tk.Frame(parent, bg=C["panel"], padx=14, pady=12)
        return p

    def _mk_progress(self, parent):
        bar = ttk.Progressbar(parent, mode="indeterminate", length=300)
        lbl = tk.Label(parent, text="", bg=C["panel"], fg=C["muted"],
                       font=("Segoe UI", 9))
        return bar, lbl

    # ------------------------------------------------------------ tab: separar
    def _build_separar(self, parent):
        f = self._mk_panel(parent)
        tk.Label(f, text="🎤 SEPARAR VOZ × INSTRUMENTAL", font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", pady=(0, 8))

        _, self.sep_file = self._mk_field(f, "Música (MP3/WAV/FLAC):")
        _, self.sep_dir = self._mk_field(f, "Pasta de saída:")
        row_m = tk.Frame(f, bg=C["panel"]); row_m.pack(fill="x", pady=4)
        tk.Label(row_m, text="Modelo de IA:", width=22, anchor="w", bg=C["panel"],
                 fg=C["muted"]).pack(side="left")
        self.sep_model = ttk.Combobox(row_m, values=["htdemucs", "htdemucs_ft"],
                                      state="readonly", width=14)
        self.sep_model.current(0); self.sep_model.pack(side="left")

        self._mk_btn(f, "✨ SEPARAR AGORA", self.run_separation, C["accent"]
                     ).pack(pady=10)
        self.sep_bar, self.sep_pinfo = self._mk_progress(f)
        self.sep_bar.pack(fill="x"); self.sep_pinfo.pack(anchor="w")

        box = tk.Frame(f, bg=C["panel"]); box.pack(fill="both", expand=True, pady=8)
        self.sep_list = tk.Listbox(box, bg=C["entry"], fg=C["text"],
                                   relief="flat", height=5)
        self.sep_list.pack(side="left", fill="both", expand=True)
        self.sep_list.bind("<Double-1>", lambda e: self.open_selected_sep())
        sb = tk.Frame(box, bg=C["panel"]); sb.pack(side="right", padx=6)
        self._mk_btn(sb, "▶ Abrir", self.open_selected_sep, C["panel2"], C["text"]
                     ).pack(fill="x", pady=2)
        self.btn_sep_mp3 = self._mk_btn(sb, "💾 MP3", lambda: self.export_mp3(self.selected_sep()), C["panel2"], C["text"])
        self.btn_sep_mp3.pack(fill="x", pady=2)
        self.btn_sep_mp4 = self._mk_btn(sb, "🎬 MP4", lambda: self.export_mp4(self.selected_sep()), C["panel2"], C["text"])
        self.btn_sep_mp4.pack(fill="x", pady=2)
        self.btn_sep_yt = self._mk_btn(sb, "📺 YouTube", lambda: self.youtube_upload(self.selected_sep()), C["danger"])
        self.btn_sep_yt.pack(fill="x", pady=2)
        return f

    # ------------------------------------------------------------ tab: tom
    def _build_tom(self, parent):
        f = self._mk_panel(parent)
        tk.Label(f, text="🎹 MUDAR O TOM (mantém a velocidade)", font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", pady=(0, 8))

        _, self.tom_file = self._mk_field(f, "Música (MP3/WAV/FLAC):")
        _, self.tom_dir = self._mk_field(f, "Pasta de saída:")

        row_s = tk.Frame(f, bg=C["panel"]); row_s.pack(fill="x", pady=8)
        tk.Label(row_s, text="Semitons:", width=22, anchor="w", bg=C["panel"],
                 fg=C["muted"]).pack(side="left")
        self.tom_steps = tk.Scale(row_s, from_=-12, to=12, orient="horizontal",
                                  resolution=1, bg=C["panel"], fg=C["text"],
                                  highlightthickness=0, troughcolor=C["entry"],
                                  length=260, showvalue=True, command=self._tom_label)
        self.tom_steps.set(0); self.tom_steps.pack(side="left")

        self.tom_vinyl = tk.BooleanVar(value=False)
        tk.Checkbutton(f, text="Estilo vinil (muda a velocidade junto)",
                       variable=self.tom_vinyl, bg=C["panel"], fg=C["muted"],
                       selectcolor=C["entry"], activebackground=C["panel"]
                       ).pack(anchor="w")

        self._mk_btn(f, "🎹 APLICAR E SALVAR", self.run_pitch, C["accent"]
                     ).pack(pady=10)
        self.tom_bar, self.tom_pinfo = self._mk_progress(f)
        self.tom_bar.pack(fill="x"); self.tom_pinfo.pack(anchor="w")

        box = tk.Frame(f, bg=C["panel"]); box.pack(fill="both", expand=True, pady=8)
        self.tom_result_lbl = tk.Label(box, text="", bg=C["panel"], fg=C["text"],
                                       font=("Segoe UI", 9), justify="left")
        self.tom_result_lbl.pack(anchor="w")
        sb = tk.Frame(box, bg=C["panel"]); sb.pack(anchor="w", pady=4)
        self.btn_tom_mp3 = self._mk_btn(sb, "💾 Exportar MP3", lambda: self.export_mp3(self.pitch_result), C["panel2"], C["text"])
        self.btn_tom_mp3.pack(side="left", padx=3)
        self.btn_tom_mp4 = self._mk_btn(sb, "🎬 Exportar MP4", lambda: self.export_mp4(self.pitch_result), C["panel2"], C["text"])
        self.btn_tom_mp4.pack(side="left", padx=3)
        self.btn_tom_yt = self._mk_btn(sb, "📺 Postar no YouTube", lambda: self.youtube_upload(self.pitch_result), C["danger"])
        self.btn_tom_yt.pack(side="left", padx=3)
        return f

    def _tom_label(self, v):
        try:
            n = int(float(v))
        except Exception:
            return
        txt = "Tom original" if n == 0 else (f"Acima em {n} semitons" if n > 0 else f"Abaixo em {abs(n)} semitons")
        self.tom_steps.configure()

    # ------------------------------------------------------------ tab: legendas
    def _build_legendas(self, parent):
        f = self._mk_panel(parent)
        tk.Label(f, text="📝 GERAR LEGENDAS + TRANSCRIÇÃO (IA local)", font=("Segoe UI", 13, "bold"),
                 bg=C["panel"], fg=C["text"]).pack(anchor="w", pady=(0, 8))

        _, self.srt_file = self._mk_field(f, "Áudio ou vídeo (MP3/WAV/MP4):")
        row_m = tk.Frame(f, bg=C["panel"]); row_m.pack(fill="x", pady=4)
        tk.Label(row_m, text="Modelo:", width=22, anchor="w", bg=C["panel"],
                 fg=C["muted"]).pack(side="left")
        self.srt_model = ttk.Combobox(row_m, values=["tiny", "base", "small", "medium"],
                                      state="readonly", width=10)
        self.srt_model.current(1); self.srt_model.pack(side="left")
        tk.Label(row_m, text="   Idioma:", bg=C["panel"], fg=C["muted"]).pack(side="left")
        self.srt_lang = tk.Entry(row_m, width=5, bg=C["entry"], fg=C["text"],
                                 insertbackground=C["text"], relief="flat")
        self.srt_lang.insert(0, "pt"); self.srt_lang.pack(side="left", padx=4, ipady=3)

        self._mk_btn(f, "📝 GERAR LEGENDAS (SRT + TXT)", self.run_subtitles, C["accent"]
                     ).pack(pady=10)
        self.srt_bar, self.srt_pinfo = self._mk_progress(f)
        self.srt_bar.pack(fill="x"); self.srt_pinfo.pack(anchor="w")

        box = tk.Frame(f, bg=C["panel"]); box.pack(fill="both", expand=True, pady=8)
        self.srt_result_lbl = tk.Label(box, text="", bg=C["panel"], fg=C["text"],
                                       font=("Segoe UI", 9), justify="left")
        self.srt_result_lbl.pack(anchor="w")
        sb = tk.Frame(box, bg=C["panel"]); sb.pack(anchor="w", pady=4)
        self.btn_srt_yt = self._mk_btn(sb, "📺 Postar vídeo no YouTube", lambda: self.youtube_upload(self._pick_video_for_yt()), C["danger"])
        self.btn_srt_yt.pack(side="left", padx=3)
        return f

    def _pick_video_for_yt(self):
        p = self.srt_file.get().strip()
        if p and os.path.exists(p):
            return p
        return None

    # ------------------------------------------------------------ licenças
    def refresh_license_ui(self):
        s = lic.status()
        self.lbl_lic.configure(text=f"  {s['label']}  ", fg={
            "trial": C["accent"], "licensed": C["accent2"], "restricted": C["danger"],
        }[s["mode"]])
        if s["mode"] == "restricted":
            self.banner.configure(text=f"⚠ {s['detail']}  →  ⭐ Ativar licença ou 🛒 Comprar plano")
            self.banner.pack(fill="x")
        else:
            self.banner.pack_forget()

    def show_activate_dialog(self):
        d = tk.Toplevel(self); d.title("Ativar licença")
        d.configure(bg=C["panel"]); d.geometry("460x180")
        d.transient(self); d.grab_set()
        tk.Label(d, text="Cole sua chave de licença:", bg=C["panel"], fg=C["text"],
                 font=("Segoe UI", 11, "bold")).pack(pady=(18, 6))
        e = tk.Entry(d, width=40, bg=C["entry"], fg=C["text"], justify="center",
                     insertbackground=C["text"], relief="flat", font=("Consolas", 11))
        e.pack(ipady=6, pady=4)
        def do_activate():
            ok, msg = lic.activate(e.get())
            messagebox.showinfo("Licença", msg)
            if ok:
                d.destroy(); self.refresh_license_ui()
        self._mk_btn(d, "ATIVAR", do_activate, C["accent"]).pack(pady=10)
        tk.Label(d, text=f"Planos: PLUS 70 | MAX 100 | ULTRA 140 (R$/mês)\n{STORE_URL}",
                 bg=C["panel"], fg=C["muted"], font=("Segoe UI", 9)).pack()

    def gate(self, kind):
        s = lic.status()
        if s["mode"] == "trial":
            return True
        if kind == "export":
            if s["tier"] >= 2:
                return True
            messagebox.showinfo("Plano MAX necessário",
                                "Exportar MP3/MP4 faz parte dos planos MAX (R$ 100/mês)\nou ULTRA (R$ 140/mês).\n\n🛒 " + STORE_URL)
            return False
        if kind == "youtube":
            if s["tier"] >= 3:
                return True
            messagebox.showinfo("Plano ULTRA necessário",
                                "Postagem direta no YouTube é exclusiva do plano ULTRA (R$ 140/mês).\n\n🛒 " + STORE_URL)
            return False
        return False

    # ------------------------------------------------------------ infra
    def _open_url(self, url):
        try:
            os.startfile(url)          # Windows
        except AttributeError:
            subprocess.Popen(["xdg-open", url])       # Linux
        except Exception:
            subprocess.Popen(["open", url])           # macOS

    def cap_seconds(self):
        s = lic.status()
        return None if s["full"] else lic.RESTRICT_MAX_SECONDS

    def busy(self, bar, lbl, msg):
        lbl.configure(text="⏳ " + msg)
        bar.start(12)

    def idle(self, bar, lbl, msg="Pronto. 🎵"):
        bar.stop()
        lbl.configure(text="")
        self.status.configure(text=msg)

    def bg(self, fn, done, bar, lbl):
        def wrap():
            try:
                res = fn(); err = None
            except Exception as e:
                traceback.print_exc(); res = None; err = e
            self.after(0, lambda: done(res, err))
        threading.Thread(target=wrap, daemon=True).start()

    def need(self, mods, feature):
        """Verifica dependências. mods: lista (import_name, pip_name)."""
        for mod, pip in mods:
            if not has_mod(mod):
                messagebox.showerror(
                    "Dependência faltando",
                    f"'{feature}' precisa do pacote **{pip}**.\n\n"
                    "Abra o terminal na pasta do app e rode:\n"
                    f"    pip install {pip}\n\n"
                    "ou execute instalar.bat / install.sh")
                return False
        if not FFMPEG:
            messagebox.showerror(
                "FFmpeg não encontrado",
                "Instale o FFmpeg e deixe-o no PATH do sistema.\n"
                "Windows: winget install ffmpeg\nmacOS: brew install ffmpeg\n"
                "Linux: sudo apt install ffmpeg")
            return False
        return True

    def maybe_trim(self, path, is_audio=True):
        """No modo restrito, limita o processamento a 60s."""
        capv = self.cap_seconds()
        if capv is None:
            return path
        import numpy as np
        import librosa, soundfile as sf
        y, sr = librosa.load(path, sr=None, mono=False, duration=capv)
        if y.ndim == 1:
            y = y[None, :]
        tmp = os.path.join(tempfile.gettempdir(), f"edc_{int(time.time()*1000)}.wav")
        sf.write(tmp, y.T, sr)
        return tmp

    def default_outdir(self, src, sub):
        base = os.path.dirname(src) or os.path.expanduser("~")
        d = os.path.join(base, sub)
        os.makedirs(d, exist_ok=True)
        return d

    def pick_music(self, var):
        p = filedialog.askopenfilename(filetypes=[
            ("Áudio", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("Todos", "*.*")])
        if p:
            var.set(p)
            if hasattr(self, "sep_dir") and var is self.sep_file and not self.sep_dir.get():
                self.sep_dir.set(self.default_outdir(p, "Separados"))
            if hasattr(self, "tom_dir") and var is self.tom_file and not self.tom_dir.get():
                self.tom_dir.set(self.default_outdir(p, "ComTomAlterado"))

    # ------------------------------------------------------------ separar
    def run_separation(self):
        src = self.sep_file.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showwarning("Arquivo", "Escolha uma música primeiro."); return
        out = self.sep_dir.get().strip() or self.default_outdir(src, "Separados")
        if not self.need([("demucs", "demucs")], "Separar voz"):
            return
        self.busy(self.sep_bar, self.sep_pinfo, "Carregando IA e separando... (pode levar minutos)")

        def work():
            src_eff = self.maybe_trim(src)
            cmd = [sys.executable, "-m", "demucs",
                   "-n", self.sep_model.get(),
                   "--two-stems", "vocals",
                   "-o", out, src_eff]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError((r.stderr or r.stdout)[-1500:])
            stem = os.path.splitext(os.path.basename(src_eff))[0]
            d = os.path.join(out, self.sep_model.get(), stem)
            res = [os.path.join(d, x) for x in ("vocals.wav", "no_vocals.wav")]
            return [p for p in res if os.path.exists(p)]

        def done(res, err):
            if err:
                self.idle(self.sep_bar, self.sep_pinfo, "Erro ❌")
                messagebox.showerror("Erro ao separar", str(err)); return
            self.sep_results = res or []
            self.sep_list.delete(0, "end")
            for p in self.sep_results:
                self.sep_list.insert("end", " 🎤 " + os.path.basename(p) + "  →  " + p)
            self.idle(self.sep_bar, self.sep_pinfo,
                      f"Concluído ✅ {len(self.sep_results)} arquivo(s) em {out}")
            messagebox.showinfo("Pronto!", "Separação concluída!\n\n🎤 voz → vocals.wav\n🎼 instrumental → no_vocals.wav")
        self.bg(work, done, self.sep_bar, self.sep_pinfo)

    def selected_sep(self):
        sel = self.sep_list.curselection()
        if sel:
            return self.sep_results[sel[0]]
        if self.sep_results:
            return self.sep_results[0]
        return None

    def open_selected_sep(self):
        p = self.selected_sep()
        if p and os.path.exists(p):
            self._open_url(os.path.dirname(p))

    # ------------------------------------------------------------ tom
    def run_pitch(self):
        src = self.tom_file.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showwarning("Arquivo", "Escolha uma música primeiro."); return
        out = self.tom_dir.get().strip() or self.default_outdir(src, "ComTomAlterado")
        if not self.need([("librosa", "librosa"), ("soundfile", "soundfile")], "Mudar tom"):
            return
        steps = int(self.tom_steps.get())
        if steps == 0:
            messagebox.showwarning("Tom", "Escolha um valor diferente de 0."); return
        vinyl = self.tom_vinyl.get()
        self.busy(self.tom_bar, self.tom_pinfo, "Aplicando tom...")

        def work():
            import numpy as np
            import librosa, soundfile as sf
            capv = self.cap_seconds()
            y, sr = librosa.load(src, sr=None, mono=False,
                                 duration=capv)
            if y.ndim == 1:
                y = y[None, :]
            if vinyl:
                factor = 2 ** (steps / 12)
                n = max(2, int(y.shape[1] / factor))
                idx = np.linspace(0, y.shape[1] - 1, n)
                y2 = np.stack([np.interp(idx, np.arange(y.shape[1]), y[c])
                               for c in range(y.shape[0])])
            else:
                chans = [librosa.effects.pitch_shift(y[y.shape[0] > 1 and c or 0],
                                                     sr=sr, n_steps=steps)
                         for c in range(y.shape[0])]
                y2 = np.stack(chans)
            dst = os.path.join(out, f"{os.path.splitext(os.path.basename(src))[0]}"
                                    f"_{steps:+d}st.wav")
            sf.write(dst, y2.T, sr)
            return dst

        def done(res, err):
            if err:
                self.idle(self.tom_bar, self.tom_pinfo, "Erro ❌")
                messagebox.showerror("Erro ao aplicar tom", str(err)); return
            self.pitch_result = res
            self.tom_result_lbl.configure(text=f"✅ {res}")
            self.idle(self.tom_bar, self.tom_pinfo, f"Tom aplicado ✅ {res}")
        self.bg(work, done, self.tom_bar, self.tom_pinfo)

    # ------------------------------------------------------------ legendas
    def run_subtitles(self):
        src = self.srt_file.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showwarning("Arquivo", "Escolha um arquivo primeiro."); return
        if not self.need([("whisper", "openai-whisper")], "Legendas"):
            return
        model = self.srt_model.get()
        lang = self.srt_lang.get().strip() or None
        self.busy(self.srt_bar, self.srt_pinfo, "Transcrevendo com IA (pode demorar)...")

        def work():
            import whisper
            src_eff = src
            capv = self.cap_seconds()
            if capv and src_eff.lower().endswith((".mp4", ".mkv", ".mov", ".avi", ".webm")):
                tmp = os.path.join(tempfile.gettempdir(), f"edc_cap_{int(time.time())}.mp4")
                subprocess.run(["ffmpeg", "-y", "-i", src_eff, "-t", str(capv),
                                "-c", "copy", tmp], capture_output=True)
                if os.path.exists(tmp):
                    src_eff = tmp
            else:
                src_eff = self.maybe_trim(src)
            m = whisper.load_model(model)
            r = m.transcribe(src_eff, language=lang)
            base = os.path.splitext(src)[0]
            srt_p, txt_p = base + ".srt", base + ".txt"
            with open(srt_p, "w", encoding="utf-8") as f:
                for i, seg in enumerate(r["segments"], 1):
                    f.write(f"{i}\n{srt_ts(seg['start'])} --> {srt_ts(seg['end'])}\n"
                            f"{seg['text'].strip()}\n\n")
            with open(txt_p, "w", encoding="utf-8") as f:
                f.write("\n".join(s["text"].strip() for s in r["segments"]))
            return srt_p, txt_p

        def done(res, err):
            if err:
                self.idle(self.srt_bar, self.srt_pinfo, "Erro ❌")
                messagebox.showerror("Erro na transcrição", str(err)); return
            self.srt_result = res
            self.srt_result_lbl.configure(text=f"✅ Legenda: {res[0]}\n✅ Texto: {res[1]}")
            self.idle(self.srt_bar, self.srt_pinfo, "Legendas geradas ✅")
        self.bg(work, done, self.srt_bar, self.srt_pinfo)

    # ------------------------------------------------------------ exportar
    def export_mp3(self, wav_path):
        if not wav_path or not os.path.exists(wav_path):
            messagebox.showwarning("Exportar", "Nenhum arquivo para exportar."); return
        if not self.gate("export"):
            return
        if not self.need([("pydub", "pydub")], "Exportar MP3"):
            return
        try:
            from pydub import AudioSegment
            dst = os.path.splitext(wav_path)[0] + ".mp3"
            AudioSegment.from_wav(wav_path).export(dst, format="mp3", bitrate="192k")
            messagebox.showinfo("Pronto!", f"MP3 exportado:\n{dst}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def export_mp4(self, wav_path):
        if not wav_path or not os.path.exists(wav_path):
            messagebox.showwarning("Exportar", "Nenhum arquivo para exportar."); return
        if not self.gate("export"):
            return
        cover = filedialog.askopenfilename(
            title="Capa do vídeo (imagem) — cancele para gerar automática",
            filetypes=[("Imagem", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        try:
            if not cover:
                cover = self._auto_cover(wav_path)
            dst = os.path.splitext(wav_path)[0] + ".mp4"
            cmd = ["ffmpeg", "-y", "-loop", "1", "-i", cover, "-i", wav_path,
                   "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
                   "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", dst]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError((r.stderr or "")[-1200:])
            messagebox.showinfo("Pronto!", f"MP4 exportado:\n{dst}")
        except Exception as e:
            messagebox.showerror("Erro no MP4", str(e))

    def _auto_cover(self, wav_path):
        from PIL import Image, ImageDraw
        title = os.path.splitext(os.path.basename(wav_path))[0][:40]
        img = Image.new("RGB", (1280, 1280), (16, 18, 26))
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, 0, 1279, 1279], outline=(61, 220, 151), width=8)
        dr.text((640 - 10 * len(title) / 2, 600), title, fill=(232, 234, 240))
        p = os.path.join(tempfile.gettempdir(), "edc_cover.png")
        img.save(p)
        return p

    # ------------------------------------------------------------ youtube
    def youtube_upload(self, path):
        if not path or not os.path.exists(path):
            messagebox.showwarning("YouTube", "Nenhum arquivo de vídeo para postar.\n"
                                   "Dica: gere um MP4 primeiro."); return
        if not self.gate("youtube"):
            return
        secret = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")
        if not os.path.exists(secret):
            messagebox.showerror("YouTube",
                "Faltam credenciais do YouTube.\n\n1) Crie um projeto em console.cloud.google.com\n"
                "2) Ative a YouTube Data API v3\n3) Baixe o OAuth client (Desktop)\n"
                "4) Salve como client_secret.json na pasta do app")
            return
        if not self.need([("googleapiclient", "google-api-python-client"),
                          ("google_auth_oauthlib", "google-auth-oauthlib")], "YouTube"):
            return
        d = tk.Toplevel(self); d.title("Postar no YouTube")
        d.configure(bg=C["panel"]); d.geometry("440x260"); d.transient(self); d.grab_set()
        tk.Label(d, text="Título:", bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=14, pady=(14, 2))
        t = tk.Entry(d, bg=C["entry"], fg=C["text"], insertbackground=C["text"], relief="flat")
        t.pack(fill="x", padx=14, ipady=5)
        tk.Label(d, text="Descrição:", bg=C["panel"], fg=C["text"]).pack(anchor="w", padx=14, pady=(8, 2))
        desc = tk.Text(d, height=5, bg=C["entry"], fg=C["text"], relief="flat")
        desc.pack(fill="x", padx=14)

        def go():
            d.destroy()
            self._yt_do_upload(path, t.get().strip() or "Meu vídeo", desc.get("1.0", "end").strip())
        self._mk_btn(d, "🚀 PUBLICAR", go, C["danger"]).pack(pady=12)

    def _yt_do_upload(self, path, title, description):
        self.status.configure(text="⏳ Enviando para o YouTube...")
        def work():
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            import google.auth.transport.requests as tr
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json"),
                ["https://www.googleapis.com/auth/youtube.upload"])
            creds = flow.run_local_server(port=0)
            yt = build("youtube", "v3", credentials=creds)
            media = MediaFileUpload(path, chunksize=1024 * 1024 * 4, resumable=True)
            req = yt.videos().insert(
                part="snippet,status",
                body={"snippet": {"title": title, "description": description,
                                  "categoryId": "10"},
                      "status": {"privacyStatus": "unlisted"}},
                media_body=media)
            resp = None
            while resp is None:
                st, resp = req.next_chunk()
                if st:
                    self.after(0, lambda p=int(st.progress() * 100):
                               self.status.configure(text=f"⏳ Enviando... {p}%"))
            return resp["id"]
        def done(vid, err):
            if err:
                self.status.configure(text="Erro no upload ❌")
                messagebox.showerror("YouTube", str(err)); return
            self.status.configure(text="Publicado ✅")
            messagebox.showinfo("Publicado!",
                                f"Vídeo publicado (não listado):\nhttps://youtu.be/{vid}")
        self.bg(work, done, self.srt_bar, self.srt_pinfo)


def main():
    lic.init()
    App().mainloop()


if __name__ == "__main__":
    main()
