"""
音频录音模块
"""
import time
from typing import Optional
from pathlib import Path
from utils.logger import setup_logger
import subprocess
import config
import wave
AUDIO_FILE = "recording.wav"
logger = setup_logger(__name__)


class AudioRecorder:
    """音频录音器"""
    
    def __init__(self):
        """初始化录音器"""
        self.is_recording = False
        self.audio_data = []
        logger.info("🎤 音频录音器已初始化")
        
    def fix_wav_to_linear16(self, input_path, output_path):
        self.cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        "-sample_fmt", "s16",
        output_path
        ]
        subprocess.run(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def start_recording(self) -> None:
        """
        开始录音
        
        Returns:
            None
        """
        # TODO: 实现录音逻辑
        # 使用 pyaudio 或 sounddevice 录制音频
        # 保存到 self.audio_data
        logger.info("🔴 开始录音...")
        self.is_recording = True
        raise NotImplementedError("录音功能待实现")
    
    def stop_recording(self) -> str:
        """
        停止录音并保存为文件
        
        Returns:
            str: 保存的音频文件路径
        """
        # TODO: 实现停止录音和保存逻辑
        # 将 self.audio_data 保存为 FLAC 或 WAV 文件
        # 返回文件路径
        logger.info("⏹️ 停止录音...")
        self.is_recording = False
        
        # 生成临时文件路径
        audio_path = config.AUDIO_TEMP_DIR / f"recording_{int(time.time())}.{config.AUDIO_FORMAT}"
        
        # TODO: 保存音频数据到文件
        # 使用 soundfile 保存为 FLAC/WAV
        # 占位实现：返回路径（实际需要实现录音逻辑）
        logger.warning("⚠️ 录音功能未实现，返回占位路径")
        return str(audio_path)
    
    def record_for_duration(self, duration: float) -> str:
        """
        录制指定时长的音频
        
        Args:
            duration: 录音时长（秒）
            
        Returns:
            str: 保存的音频文件路径
        """
        # TODO: 实现定时录音
        rec = subprocess.Popen([
            "arecord", "-D", "plughw:1", "-c1", "-r", "48000",
            "-f", "S32_LE", "-t", "wav", "-V", "mono", "-v", AUDIO_FILE
        ])
        time.sleep(duration)
        rec.terminate()
        rec.wait()
        
        print(f"录音已保存: {AUDIO_FILE}")
        
        # 放大音频音量
        print("放大音频音量...")
        amplified_file = "recording_amplified.wav"
        subprocess.run([
            "sox", "-v", "10", AUDIO_FILE, amplified_file
        ])
        # 替换原文件
        subprocess.run(["mv", amplified_file, AUDIO_FILE])
        print(f"音频已放大并保存: {AUDIO_FILE}")
        
        # 转换音频格式为 Linear16
        converted_file = "converted.wav"
        self.fix_wav_to_linear16(AUDIO_FILE, converted_file)
        print(f"音频已转换为 Linear16: {converted_file}")
        
        logger.info(f"⏱️ 录制 {duration} 秒音频完成")
        
        # 返回转换后的文件路径
        return converted_file

