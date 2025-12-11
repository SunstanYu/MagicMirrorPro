"""
音乐播放动作
"""
import os
import requests
import soundfile as sf
import sounddevice as sd
import tempfile
import threading
from typing import Dict, Any, Optional
from actions.base import BaseAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MusicAction(BaseAction):
    """音乐播放动作"""

    def __init__(self):
        """初始化音乐动作"""
        super().__init__("music")
        self.api_key = os.getenv("JAMENDO_API_KEY", "dbaba392")
        self.current_track_info: Optional[Dict[str, Any]] = None

        # 播放线程与状态
        self._playback_thread: Optional[threading.Thread] = None
        self._is_playing = False
        self._lock = threading.Lock()  # 保护 _is_playing / _playback_thread

        # 预设音乐映射
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.preset_music = {
            "happy": {
                "file": os.path.join(project_root, "resources", "bgm", "Happy.wav"),
                "name": "Happy",
                "artist": "Preset Music",
                "album": "Background Music"
            },
            "workout": {
                "file": os.path.join(project_root, "resources", "bgm", "Rocky.wav"),
                "name": "Rocky",
                "artist": "Preset Music",
                "album": "Background Music"
            },
            "relaxing": {
                "file": os.path.join(project_root, "resources", "bgm", "Merry-Go-Round of Life.wav"),
                "name": "Merry-Go-Round of Life",
                "artist": "Preset Music",
                "album": "Background Music"
            }
        }

    # =========================================================
    # 对外接口
    # =========================================================
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行音乐播放
        """
        query = params.get("query", "").strip().lower()

        if not query:
            logger.warning("❌ 未提供歌曲名")
            return {
                "reply_text": "Please tell me which song you want to play.",
                "data": {},
                "success": False
            }

        # 任何新的播放请求先清理旧播放
        self._prepare_new_playback()

        # 检查是否是预设音乐
        preset_type = self._check_preset_music(query)
        if preset_type:
            logger.info(f"🎵 检测到预设音乐: {preset_type}")
            return self._play_preset_music(preset_type)

        # 否则，搜索并播放在线音乐
        logger.info(f"🎵 搜索并播放音乐: {query}")

        tracks = self._search_tracks(query)
        if not tracks:
            return {
                "reply_text": f"Sorry, I couldn't find any songs matching '{query}'. Please try another song.",
                "data": {},
                "success": False
            }

        track_info = self._get_track_info(tracks[0])
        self.current_track_info = track_info

        with self._lock:
            self._is_playing = True
            self._playback_thread = threading.Thread(
                target=self._play_track_background,
                args=(track_info,),
                daemon=True
            )
            self._playback_thread.start()

        reply_text = f"Playing '{track_info['name']}' by {track_info['artist']}."
        logger.info(f"✅ 开始播放: {track_info['name']} - {track_info['artist']}")

        return {
            "reply_text": reply_text,
            "data": {
                "track_name": track_info['name'],
                "artist": track_info['artist'],
                "album": track_info['album'],
                "duration": track_info['duration']
            },
            "success": True
        }

    # =========================================================
    # 预设音乐
    # =========================================================
    def _check_preset_music(self, query: str) -> Optional[str]:
        """检查是否是预设音乐"""
        query_lower = query.lower()

        if "happy" in query_lower and "music" in query_lower:
            return "happy"
        if query_lower in ["happy", "happy music"]:
            return "happy"

        if "workout" in query_lower and "music" in query_lower:
            return "workout"
        if query_lower in ["workout", "workout music"]:
            return "workout"

        if "relax" in query_lower and "music" in query_lower:
            return "relaxing"
        if query_lower in ["relaxing", "relaxing music", "relax"]:
            return "relaxing"

        return None

    def _play_preset_music(self, preset_type: str) -> Dict[str, Any]:
        """播放预设音乐"""
        if preset_type not in self.preset_music:
            return {
                "reply_text": f"Unknown preset music type: {preset_type}",
                "data": {},
                "success": False
            }

        preset = self.preset_music[preset_type]
        file_path = preset["file"]

        if not os.path.exists(file_path):
            logger.error(f"❌ 预设音乐文件不存在: {file_path}")
            return {
                "reply_text": f"Preset music file not found: {preset_type}",
                "data": {},
                "success": False
            }

        # 读取时长
        try:
            data, samplerate = sf.read(file_path)
            duration = len(data) / samplerate
        except Exception as e:
            logger.warning(f"⚠️ 无法读取音频时长: {e}")
            duration = 0

        track_info = {
            "name": preset["name"],
            "artist": preset["artist"],
            "album": preset["album"],
            "duration": int(duration),
            "file_path": file_path
        }
        self.current_track_info = track_info

        with self._lock:
            self._is_playing = True
            self._playback_thread = threading.Thread(
                target=self._play_local_file_background,
                args=(file_path,),
                daemon=True
            )
            self._playback_thread.start()

        reply_text = f"Playing {preset_type} music: '{preset['name']}'."
        logger.info(f"✅ 开始播放预设音乐: {preset['name']}")

        return {
            "reply_text": reply_text,
            "data": {
                "track_name": preset["name"],
                "artist": preset["artist"],
                "album": preset["album"],
                "duration": int(duration)
            },
            "success": True
        }

    # =========================================================
    # 播放实现（本地 / 在线）
    # =========================================================
    def _play_local_file_background(self, file_path: str) -> None:
        """在后台线程中播放本地音频文件（可被 stop() 打断，不使用 sd.wait）"""
        try:
            logger.info(f"▶️ [音乐播放] 开始播放本地文件: {file_path}")

            if not os.path.exists(file_path):
                logger.error(f"❌ [音乐播放] 文件不存在: {file_path}")
                return

            data, samplerate = sf.read(file_path)
            logger.info(f"✅ [音乐播放] 音频文件读取成功，采样率: {samplerate}Hz, 数据形状: {data.shape}")

            # 立体声转单声道
            if len(data.shape) > 1:
                data = data.mean(axis=1)

            playback_rate = samplerate * 0.8
            logger.info(f"▶️ [音乐播放] 开始播放，播放速率: {playback_rate}Hz")

            # 计算大致播放时长（秒）
            total_seconds = len(data) / playback_rate

            # 输出设备信息（可选）
            try:
                default_output = sd.query_devices(kind='output')
                logger.info(f"🔍 [音乐播放] 默认输出设备: {default_output['name']}")
            except Exception as e:
                logger.warning(f"⚠️ [音乐播放] 查询设备信息失败: {e}")

            # 启动播放（异步）
            sd.play(data, samplerate=playback_rate)

            # 自己控制播放循环，而不是用 sd.wait()
            elapsed = 0.0
            step = 0.1  # 100ms 检查一次
            import time

            while True:
                with self._lock:
                    playing_flag = self._is_playing
                if not playing_flag:
                    logger.info("⏹️ [音乐播放] _is_playing 变为 False，中断播放循环")
                    break

                if elapsed >= total_seconds:
                    logger.info("✅ [音乐播放] 预计播放时长已到，结束播放循环")
                    break

                time.sleep(step)
                elapsed += step

            # 最后确保停止
            try:
                sd.stop()
                logger.info("🛑 [音乐播放] sd.stop() 已调用（本地文件）")
            except Exception as e:
                logger.warning(f"⚠️ [音乐播放] sd.stop() 失败: {e}")

        except Exception as e:
            logger.error(f"❌ [音乐播放] 播放失败: {e}", exc_info=True)
        finally:
            with self._lock:
                self._is_playing = False
                logger.info("✅ [音乐播放] 本地文件播放线程结束，_is_playing 已设置为 False")


    def _play_track_background(self, track_info: dict) -> None:
        """在后台线程中播放在线歌曲（可被 stop() 打断，不使用 sd.wait）"""
        audio_url = track_info.get("audio_url") or track_info.get("audio_download")
        if not audio_url:
            logger.error("❌ [音乐播放] 该歌曲没有可用的音频 URL")
            with self._lock:
                self._is_playing = False
            return

        tmp_path = None
        try:
            logger.info(f"📥 [音乐播放] 下载音频: {audio_url}")
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()

            # 下载到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    # 下载过程中也要支持 stop()
                    with self._lock:
                        if not self._is_playing:
                            logger.warning("⚠️ [音乐播放] 播放被中断，停止下载")
                            break
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            with self._lock:
                if not self._is_playing:
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.info("🗑️ [音乐播放] 已删除中断下载的临时文件")
                    return

            # 读取音频
            data, samplerate = sf.read(tmp_path)
            logger.info(f"✅ [音乐播放] 音频文件读取成功，采样率: {samplerate}Hz, 数据形状: {data.shape}")

            if len(data.shape) > 1:
                data = data.mean(axis=1)

            playback_rate = samplerate * 0.8
            logger.info(f"▶️ [音乐播放] 开始播放在线音频，播放速率: {playback_rate}Hz")

            total_seconds = len(data) / playback_rate

            sd.play(data, samplerate=playback_rate)

            # 播放轮询循环
            elapsed = 0.0
            step = 0.1
            import time

            while True:
                with self._lock:
                    playing_flag = self._is_playing
                if not playing_flag:
                    logger.info("⏹️ [音乐播放] _is_playing 变为 False，中断在线播放循环")
                    break

                if elapsed >= total_seconds:
                    logger.info("✅ [音乐播放] 在线音频预计播放时长已到，结束播放循环")
                    break

                time.sleep(step)
                elapsed += step

            try:
                sd.stop()
                logger.info("🛑 [音乐播放] sd.stop() 已调用（在线音频）")
            except Exception as e:
                logger.warning(f"⚠️ [音乐播放] sd.stop() 失败: {e}")

        except Exception as e:
            logger.error(f"❌ [音乐播放] 播放失败: {e}", exc_info=True)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    logger.info("✅ [音乐播放] 临时文件已删除")
                except Exception as e2:
                    logger.warning(f"⚠️ [音乐播放] 删除临时文件失败: {e2}")
            with self._lock:
                self._is_playing = False
                logger.info("✅ [音乐播放] 在线播放线程结束，_is_playing 已设置为 False")


    # =========================================================
    # Jamendo 搜索
    # =========================================================
    def _search_tracks(self, query: str, limit: int = 5) -> Optional[list]:
        """搜索歌曲"""
        try:
            url = "https://api.jamendo.com/v3.0/tracks/"
            params = {
                "client_id": self.api_key,
                "format": "json",
                "search": query,
                "limit": limit,
                "audioformat": "mp32",
                "order": "popularity_total"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("headers", {}).get("status") == "success":
                tracks = data.get("results", [])
                if tracks:
                    logger.info(f"✅ 找到 {len(tracks)} 首歌曲")
                    return tracks
                else:
                    logger.warning("❌ 未找到歌曲")
                    return None
            else:
                error_msg = data.get('headers', {}).get('error_message', '未知错误')
                logger.error(f"❌ API 返回错误: {error_msg}")
                return None

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}", exc_info=True)
            return None

    def _get_track_info(self, track: dict) -> dict:
        """提取歌曲信息"""
        return {
            "name": track.get("name", "未知"),
            "artist": track.get("artist_name", "未知艺术家"),
            "album": track.get("album_name", "未知专辑"),
            "duration": track.get("duration", 0),
            "audio_url": track.get("audio", ""),
            "audio_download": track.get("audiodownload", ""),
            "share_url": track.get("shareurl", ""),
            "image": track.get("image", "")
        }

    # =========================================================
    # 控制接口
    # =========================================================
    def _prepare_new_playback(self) -> None:
        """
        在每次新播放前调用：
        停止当前播放并尽量等待旧播放线程退出，避免多个线程同时操作 sounddevice。
        """
        with self._lock:
            if self._is_playing:
                logger.info("⏹️ [音乐播放] 新播放前先停止旧播放")
                self._is_playing = False
                try:
                    sd.stop()
                except Exception as e:
                    logger.warning(f"⚠️ [音乐播放] 预停止 sd.stop() 失败: {e}")

            thread = self._playback_thread

        if thread and thread.is_alive():
            logger.info("⏳ [音乐播放] 等待旧播放线程退出...")
            thread.join(timeout=2.0)
            if thread.is_alive():
                logger.warning("⚠️ [音乐播放] 旧播放线程在 2 秒内未完全退出（但会被设为守护线程继续退出）")

    def stop(self) -> None:
        """停止播放（供外部调用，例如按回车键时）"""
        logger.info(f"⏹️ [音乐播放] stop() 被调用")
        with self._lock:
            if not self._is_playing:
                logger.info("ℹ️ [音乐播放] 当前未在播放，无需停止")
                return
            self._is_playing = False
            try:
                sd.stop()
                logger.info("✅ [音乐播放] sd.stop() 已调用")
            except Exception as e:
                logger.error(f"❌ [音乐播放] sd.stop() 失败: {e}", exc_info=True)
            thread = self._playback_thread

        if thread and thread.is_alive():
            logger.info("⏳ [音乐播放] stop() 等待播放线程退出...")
            thread.join(timeout=2.0)
            if thread.is_alive():
                logger.warning("⚠️ [音乐播放] 播放线程在 2 秒内未退出")

    def is_playing(self) -> bool:
        """检查是否正在播放"""
        with self._lock:
            result = self._is_playing
        logger.debug(f"🔍 [音乐播放] is_playing() 返回: {result}")
        return result
