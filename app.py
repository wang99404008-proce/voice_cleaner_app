import os
import sys
import shutil
import threading
import subprocess
import tempfile
import soundfile as sf
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox

# 拖曳功能支援
try:
    from TkinterDnD2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from df.enhance import enhance, init_df, load_audio, save_audio
from pedalboard import Pedalboard, HighpassFilter, Compressor, PeakFilter

def get_ffmpeg_path():
    """優先尋找打包目錄內的 ffmpeg，其次尋找系統 PATH"""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        ext = ".exe" if sys.platform.startswith("win") else ""
        local_ffmpeg = os.path.join(base_dir, f"ffmpeg{ext}")
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
    return shutil.which("ffmpeg") or "ffmpeg"

FFMPEG_BIN = get_ffmpeg_path()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AudioProcessor:
    def __init__(self):
        self.model, self.df_state, _ = init_df()
        self.dsp_board = Pedalboard([
            HighpassFilter(cutoff_frequency_hz=80.0),
            PeakFilter(cutoff_frequency_hz=3200.0, gain_db=2.5, q=1.0),
            Compressor(threshold_db=-18.0, ratio=2.5, attack_ms=10.0, release_ms=100.0)
        ])

    def process(self, input_path: str, output_path: str, update_status_fn=None):
        base, ext = os.path.splitext(input_path)
        ext = ext.lower()
        is_video = ext in ['.mp4', '.mov', '.mkv', '.avi']

        with tempfile.TemporaryDirectory() as tmpdir:
            extracted_wav = os.path.join(tmpdir, "extracted.wav")
            enhanced_wav = os.path.join(tmpdir, "enhanced.wav")

            if update_status_fn:
                update_status_fn("正在解析音訊串流...")
            cmd_extract = [
                FFMPEG_BIN, "-y", "-i", input_path,
                "-vn", "-ar", "48000", "-ac", "1", extracted_wav
            ]
            subprocess.run(cmd_extract, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            if update_status_fn:
                update_status_fn("AI 深度去噪與去混響處理中...")
            audio, _ = load_audio(extracted_wav, sr=self.df_state.sr())
            enhanced = enhance(self.model, self.df_state, audio)

            if update_status_fn:
                update_status_fn("套用人聲動態與 EQ 優化...")
            audio_np = enhanced.cpu().numpy()
            processed_audio = self.dsp_board(audio_np, self.df_state.sr())
            save_audio(enhanced_wav, processed_audio, self.df_state.sr())

            if update_status_fn:
                update_status_fn("正在匯出成品檔案...")
            if is_video:
                cmd_merge = [
                    FFMPEG_BIN, "-y", "-i", input_path, "-i", enhanced_wav,
                    "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
                    "-c:a", "aac", "-b:a", "192k", output_path
                ]
            else:
                cmd_merge = [
                    FFMPEG_BIN, "-y", "-i", enhanced_wav,
                    "-c:a", "libmp3lame" if output_path.endswith(".mp3") else "pcm_s16le",
                    output_path
                ]
            subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

BaseClass = TkinterDnD.DnDWrapper if HAS_DND else object

class VoiceEnhancerApp(ctk.CTk, BaseClass):
    def __init__(self):
        super().__init__()
        if HAS_DND:
            self.TkdndVersion = TkinterDnD._require(self)

        self.title("Voice Clarity Studio - 人聲清晰化工具")
        self.geometry("640x450")
        self.resizable(False, False)

        self.input_file = None
        self.processor = None

        self._build_ui()
        threading.Thread(target=self._init_backend, daemon=True).start()

    def _init_backend(self):
        self.status_label.configure(text="載入 AI 語音引擎中...")
        self.processor = AudioProcessor()
        self.status_label.configure(text="系統就緒，請匯入檔案")
        self.btn_select.configure(state="normal")

    def _build_ui(self):
        self.header = ctk.CTkLabel(self, text="AI 人聲清晰與降噪處理器", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.pack(pady=(20, 5))

        self.sub_header = ctk.CTkLabel(self, text="支援 MP3, WAV, M4A, MP4, MOV 影片自動無損替換音軌", text_color="gray")
        self.sub_header.pack(pady=(0, 20))

        self.drop_frame = ctk.CTkFrame(self, width=540, height=140, corner_radius=12, border_width=2, border_color="#3A3D40")
        self.drop_frame.pack(padx=20, pady=10)
        self.drop_frame.pack_propagate(False)

        self.lbl_drop = ctk.CTkLabel(self.drop_frame, text="拖曳檔案至此處，或點擊下方按鈕選取", font=ctk.CTkFont(size=14))
        self.lbl_drop.pack(expand=True)

        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self._on_drop)

        self.btn_select = ctk.CTkButton(self, text="選擇檔案", width=140, state="disabled", command=self._select_file)
        self.btn_select.pack(pady=5)

        self.lbl_filename = ctk.CTkLabel(self, text="未選擇任何檔案", text_color="lightgray", wraplength=500)
        self.lbl_filename.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(self, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(15, 5))

        self.status_label = ctk.CTkLabel(self, text="初始化中...", font=ctk.CTkFont(size=12), text_color="#A0A0A0")
        self.status_label.pack(pady=2)

        self.btn_run = ctk.CTkButton(self, text="開始人聲增強", width=220, height=40, font=ctk.CTkFont(size=15, weight="bold"),
                                     fg_color="#1F6AA5", hover_color="#144870", state="disabled", command=self._start_processing)
        self.btn_run.pack(pady=(15, 20))

    def _on_drop(self, event):
        path = event.data.strip('{}')
        self._set_input_file(path)

    def _select_file(self):
        file_path = filedialog.askopenfilename(
            title="選擇要處理的檔案",
            filetypes=[("Media Files", "*.wav *.mp3 *.m4a *.flac *.mp4 *.mov *.mkv *.avi"), ("All Files", "*.*")]
        )
        if file_path:
            self._set_input_file(file_path)

    def _set_input_file(self, path):
        self.input_file = path
        self.lbl_filename.configure(text=f"已選取：{os.path.basename(path)}")
        self.btn_run.configure(state="normal")
        self.progress_bar.set(0)
        self.status_label.configure(text="檔案就緒，點擊按鈕開始")

    def _start_processing(self):
        if not self.input_file or not self.processor:
            return

        base, ext = os.path.splitext(self.input_file)
        default_out = f"{base}_enhanced{ext}"
        output_path = filedialog.asksaveasfilename(
            initialfile=os.path.basename(default_out),
            defaultextension=ext,
            title="儲存清晰化後的檔案"
        )
        if not output_path:
            return

        self.btn_run.configure(state="disabled")
        self.btn_select.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        def worker():
            try:
                self.processor.process(
                    self.input_file, 
                    output_path, 
                    update_status_fn=lambda txt: self.status_label.configure(text=txt)
                )
                self.after(0, self._on_success, output_path)
            except Exception as e:
                self.after(0, self._on_failed, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, output_path):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1.0)
        self.status_label.configure(text="處理完成！")
        self.btn_run.configure(state="normal")
        self.btn_select.configure(state="normal")
        messagebox.showinfo("完成", f"檔案已成功增強並輸出至：\n{output_path}")

    def _on_failed(self, err_msg):
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.status_label.configure(text="處理失敗")
        self.btn_run.configure(state="normal")
        self.btn_select.configure(state="normal")
        messagebox.showerror("錯誤", f"處理過程中發生錯誤：\n{err_msg}")

if __name__ == "__main__":
    app = VoiceEnhancerApp()
    app.mainloop()
