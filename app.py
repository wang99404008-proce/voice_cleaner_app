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

# 拖曳功能相容支援
try:
    from TkinterDnD2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from df.enhance import enhance, init_df, load_audio, save_audio
from pedalboard import Pedalboard, HighpassFilter, Compressor, PeakFilter

def get_ffmpeg_path():
    """尋找與本程式同目錄下的獨立 ffmpeg.exe，找不到則 fallback 到系統 PATH"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包成 exe 時，取得 exe 所在的真實資料夾路徑
        base_dir = os.path.dirname(sys.executable)
    else:
        # 開發環境下，取得目前 py 檔所在目錄
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 優先檢查同目錄是否有 ffmpeg.exe
    local_ffmpeg = os.path.join(base_dir, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # 2. 備用：檢查系統環境變數中的 ffmpeg
    return shutil.which("ffmpeg") or "ffmpeg"

FFMPEG_BIN = get_ffmpeg_path()

# 設定深色主題風格
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AudioProcessor:
    def __init__(self):
        # 初始化 DeepFilterNet 增強模型 (48kHz)
        self.model, self.df_state, _ = init_df()
        
        # 定義人聲增強 DSP 鏈 (修飾音質、凸顯咬字)
        self.dsp_board = Pedalboard([
            HighpassFilter(cutoff_frequency_hz=80.0),                      # 濾除 80Hz 以下環境低頻轟鳴與底噪
            PeakFilter(cutoff_frequency_hz=3200.0, gain_db=2.5, q=1.0),   # 增強人聲咬字頻段 (提升清晰度)
            Compressor(threshold_db=-18.0, ratio=2.5, attack_ms=10.0, release_ms=100.0) # 壓制爆音、提昇細節平衡度
        ])

    def process(self, input_path: str, output_path: str, update_status_fn=None):
        base, ext = os.path.splitext(input_path)
        ext = ext.lower()
        is_video = ext in ['.mp4', '.mov', '.mkv', '.avi']

        # 在 Windows 上調用外部程式時隱藏命令提示字元黑底視窗
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        with tempfile.TemporaryDirectory() as tmpdir:
            extracted_wav = os.path.join(tmpdir, "extracted.wav")
            enhanced_wav = os.path.join(tmpdir, "enhanced.wav")

            # 步驟 1: 使用獨立的 ffmpeg 抽取音訊並轉成 48kHz WAV
            if update_
