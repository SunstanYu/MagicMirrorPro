"""
WebRTC 通话集成模块
用于将 WebRTC 通话功能集成到 MagicMirrorPro
"""
import asyncio
import json
import numpy as np
import threading
from fractions import Fraction
from typing import Optional, Callable
from aiohttp import web, WSMsgType
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate, MediaStreamTrack
import av
import sounddevice as sd
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AudioInputTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, streaming_recorder=None, sample_rate=48000):
        super().__init__()
        self.streaming_recorder = streaming_recorder
        self.sample_rate = sample_rate
        self.running = False
        self._timestamp = 0

    async def start(self):
        if self.running:
            return

        if not self.streaming_recorder:
            logger.error("❌ streaming_recorder 未提供，无法启动音频输入")
            return

        # 启动 WebRTC 模式，让 recorder 开始往 _webrtc_audio_queue 里塞数据
        if hasattr(self.streaming_recorder, 'start_webrtc_mode'):
            self.streaming_recorder.start_webrtc_mode()

        self.running = True
        logger.info("✅ WebRTC 音频输入已启动（从 streaming_recorder 获取音频）")

    async def stop(self):
        logger.info("🛑 请求停止 WebRTC 音频输入轨道...")
        self.running = False

        if self.streaming_recorder and hasattr(self.streaming_recorder, 'stop_webrtc_mode'):
            self.streaming_recorder.stop_webrtc_mode()

        logger.info("✅ WebRTC 音频输入已停止")

    async def recv(self):
        """向远端发送音频帧（直接使用 streaming_recorder 的原始数据，不预处理）"""
        # WebRTC 期望 20ms 一帧
        target_samples = int(self.sample_rate * 0.02)  # 48000Hz -> 960

        if not self.streaming_recorder or not self.running:
            audio_array = np.zeros(target_samples, dtype=np.int16)
        else:
            # 获取录音器的实际采样率
            recorder_rate = getattr(
                self.streaming_recorder, '_actual_sample_rate',
                getattr(self.streaming_recorder, 'sample_rate', self.sample_rate)
            )

            # 直接从队列获取原始音频数据（已经是 20ms 块大小）
            try:
                audio_bytes = self.streaming_recorder.get_webrtc_audio(timeout=0.05)
            except Exception:
                audio_bytes = None

            if audio_bytes is None:
                # 没有数据，发送静音
                audio_array = np.zeros(target_samples, dtype=np.int16)
            else:
                # 直接使用原始数据，转换为 numpy 数组
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

                # 如果采样率匹配，直接使用（block_size 已经是 20ms，长度应该匹配）
                if recorder_rate == self.sample_rate:
                    # 理论上长度应该正好是 target_samples，但做防御性检查
                    if len(audio_array) != target_samples:
                        if len(audio_array) > target_samples:
                            audio_array = audio_array[:target_samples]
                        else:
                            # 如果样本不足，用静音填充
                            pad = np.zeros(target_samples - len(audio_array), dtype=np.int16)
                            audio_array = np.concatenate([audio_array, pad])
                else:
                    # 采样率不匹配，需要重采样
                    try:
                        from scipy import signal
                        audio_array = signal.resample(audio_array, target_samples).astype(np.int16)
                        logger.debug(
                            f"🔄 WebRTC 音频重采样: {len(audio_array)}@{recorder_rate}Hz -> "
                            f"{target_samples}@{self.sample_rate}Hz"
                        )
                    except ImportError:
                        logger.warning("⚠️ scipy 未安装，使用线性插值重采样（质量较差）")
                        # 降级：线性插值
                        if len(audio_array) > 0:
                            idx = np.linspace(0, len(audio_array) - 1, target_samples)
                            audio_array = np.interp(idx, np.arange(len(audio_array)), audio_array).astype(np.int16)
                        else:
                            audio_array = np.zeros(target_samples, dtype=np.int16)
                    except Exception as e:
                        logger.error(f"❌ 重采样失败: {e}")
                        audio_array = np.zeros(target_samples, dtype=np.int16)

        # 创建音频帧（直接使用原始数据，不进行任何预处理）
        frame = av.AudioFrame.from_ndarray(
            audio_array.reshape(1, -1), format="s16", layout="mono"
        )
        frame.sample_rate = self.sample_rate
        frame.time_base = Fraction(1, self.sample_rate)
        frame.pts = self._timestamp
        self._timestamp += len(audio_array)
        return frame




class WebRTCIntegration:
    """WebRTC 集成类 - 用于 MagicMirrorPro"""
    
    def __init__(self, 
                 host='0.0.0.0', 
                 port=8080, 
                 use_https=False, 
                 cert_file=None, 
                 key_file=None,
                 on_call_start: Optional[Callable] = None,
                 on_call_end: Optional[Callable] = None,
                 streaming_recorder=None):
        """
        初始化 WebRTC 集成
        
        Args:
            host: 服务器地址
            port: 服务器端口
            use_https: 是否使用 HTTPS
            cert_file: SSL 证书文件
            key_file: SSL 私钥文件
            on_call_start: 通话开始时的回调函数
            on_call_end: 通话结束时的回调函数
            streaming_recorder: StreamingRecorder 实例，用于获取音频数据
        """
        self.host = host
        self.port = port
        self.use_https = use_https
        self.cert_file = cert_file
        self.key_file = key_file
        self.on_call_start = on_call_start
        self.on_call_end = on_call_end
        self.streaming_recorder = streaming_recorder
        
        self.app = web.Application()
        self.pcs = set()
        self.current_pc = None
        self.server_thread = None
        self.running = False
        
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        # 静态文件路径在 MagicMirrorPro/webrtc/static
        import os
        # __file__ 是 webrtc_integration.py 的路径
        magicmirror_dir = os.path.dirname(__file__)  # /home/pi/MagicMirrorPro
        static_path = os.path.join(magicmirror_dir, 'webrtc', 'static')
        static_path = os.path.abspath(static_path)  # 转换为绝对路径
        
        if not os.path.exists(static_path):
            logger.error(f"❌ 静态文件目录不存在: {static_path}")
            raise FileNotFoundError(f"静态文件目录不存在: {static_path}")
        
        logger.info(f"📂 静态文件目录: {static_path}")
        self.app.router.add_static('/static', path=static_path, name='static')
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/', self.html_handler)
    
    async def html_handler(self, request):
        """返回 HTML 页面"""
        import os
        magicmirror_dir = os.path.dirname(__file__)  # /home/pi/MagicMirrorPro
        html_path = os.path.join(magicmirror_dir, 'webrtc', 'static', 'index.html')
        html_path = os.path.abspath(html_path)  # 转换为绝对路径
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        except FileNotFoundError:
            logger.error(f"❌ HTML 文件未找到: {html_path}")
            return web.Response(text=f"<h1>页面未找到: {html_path}</h1>", content_type='text/html')
    
    async def websocket_handler(self, request):
        """WebSocket 信令处理"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        pc = None
        logger.info("🔌 新的 WebSocket 连接")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    logger.info(f"📨 收到消息: {data.get('type')}")
                    
                    if data['type'] == 'offer':
                        # 通知应用开始通话
                        if self.on_call_start:
                            self.on_call_start()
                        
                        # 创建 peer connection
                        pc = RTCPeerConnection(
                            configuration=RTCConfiguration(
                                iceServers=[
                                    RTCIceServer(urls=['stun:stun.l.google.com:19302'])
                                ]
                            )
                        )
                        self.pcs.add(pc)
                        self.current_pc = pc
                        
                        # 设置音频输入轨道（从 streaming_recorder 获取音频）
                        try:
                            audio_track = AudioInputTrack(
                                streaming_recorder=self.streaming_recorder,
                                sample_rate=48000
                            )
                            await audio_track.start()
                            if audio_track.running:
                                pc.addTrack(audio_track)
                                logger.info("✅ 音频输入已添加（从 streaming_recorder 获取）")
                            else:
                                logger.warning("⚠️ 音频输入启动失败")
                        except Exception as e:
                            logger.error(f"❌ 无法打开音频输入: {e}")
                        
                        @pc.on('track')
                        def on_track(track):
                            logger.info(f"🎵 收到远程音频轨道: {track.kind}")
                        
                        @pc.on('iceconnectionstatechange')
                        async def on_ice_state():
                            logger.info(f"🧊 ICE 状态: {pc.iceConnectionState}")
                        
                        # 接收 offer
                        offer = RTCSessionDescription(
                            sdp=data['sdp'],
                            type=data['type']
                        )
                        await pc.setRemoteDescription(offer)
                        logger.info("✅ 已设置远程描述 (offer)")
                        
                        # 创建 answer
                        answer = await pc.createAnswer()
                        await pc.setLocalDescription(answer)
                        logger.info("✅ 已创建本地描述 (answer)")
                        
                        # 发送 answer
                        await ws.send_str(json.dumps({
                            'type': 'answer',
                            'sdp': pc.localDescription.sdp
                        }))
                        logger.info("📤 已发送 answer")
                        
                        # 收集并发送 ICE candidates
                        @pc.on('icecandidate')
                        async def on_ice_candidate(candidate):
                            if candidate:
                                await ws.send_str(json.dumps({
                                    'type': 'ice-candidate',
                                    'candidate': candidate.candidate,
                                    'sdpMLineIndex': candidate.sdpMLineIndex,
                                    'sdpMid': candidate.sdpMid
                                }))
                    
                    elif data['type'] == 'ice-candidate' and pc:
                        try:
                            parts = data['candidate'].replace('candidate:', '').split()
                            if len(parts) >= 8:
                                candidate = RTCIceCandidate(
                                    component=int(parts[1]),
                                    foundation=parts[0],
                                    ip=parts[4],
                                    port=int(parts[5]),
                                    priority=int(parts[3]),
                                    protocol=parts[2],
                                    type=parts[7],
                                    sdpMLineIndex=data.get('sdpMLineIndex'),
                                    sdpMid=data.get('sdpMid')
                                )
                                await pc.addIceCandidate(candidate)
                        except Exception as e:
                            logger.error(f"❌ ICE candidate 处理失败: {e}")
                    
                    elif data['type'] == 'bye':
                        logger.info("👋 收到断开连接请求")
                        break
                
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"❌ WebSocket 错误: {ws.exception()}")
                    break
        
        except Exception as e:
            logger.error(f"❌ WebSocket 处理错误: {e}", exc_info=True)
        
        finally:
            # 通知应用通话结束
            if pc:
                # 先停止所有音频轨道（释放麦克风）
                try:
                    for sender in pc.getSenders():
                        track = sender.track
                        if isinstance(track, AudioInputTrack):
                            logger.info("🛑 正在停止 WebRTC 音频输入轨道...")
                            try:
                                await track.stop()
                            except Exception as e:
                                logger.warning(f"⚠️ 停止 AudioInputTrack 时出错: {e}")
                except Exception as e:
                    logger.warning(f"⚠️ 遍历 sender 停止轨道时出错: {e}")

                # 再多等一会儿，让 PortAudio / ALSA 完全释放设备
                await asyncio.sleep(0.5)

                # 关闭 peer connection
                try:
                    self.pcs.discard(pc)
                    await pc.close()
                    logger.info("✅ RTCPeerConnection 已关闭")
                except Exception as e:
                    logger.warning(f"⚠️ 关闭 RTCPeerConnection 时出错: {e}")
                finally:
                    if self.current_pc == pc:
                        self.current_pc = None

                logger.info("✅ WebRTC 连接已完全关闭（轨道 + PC）")

                # 通知应用通话结束（在设备释放之后）
                try:
                    if self.on_call_end:
                        self.on_call_end()
                except Exception as e:
                    logger.error(f"❌ on_call_end 回调执行失败: {e}", exc_info=True)

            await ws.close()
        
        return ws
    
    def _run_server(self):
        """在后台线程中运行服务器"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def on_shutdown(app):
                await self.cleanup()
            self.app.on_shutdown.append(on_shutdown)
            
            ssl_context = None
            if self.use_https and self.cert_file and self.key_file:
                try:
                    import ssl
                    import os
                    # 检查文件是否存在
                    if not os.path.exists(self.cert_file):
                        logger.error(f"❌ 证书文件不存在: {self.cert_file}")
                    elif not os.path.exists(self.key_file):
                        logger.error(f"❌ 私钥文件不存在: {self.key_file}")
                    else:
                        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                        ssl_context.load_cert_chain(self.cert_file, self.key_file)
                        logger.info(f"✅ SSL 证书已加载: {self.cert_file}")
                except Exception as e:
                    logger.error(f"❌ SSL 证书加载失败: {e}", exc_info=True)
                    ssl_context = None
            
            protocol = "https" if ssl_context else "http"
            logger.info(f"🚀 正在启动 WebRTC 服务器: {protocol}://{self.host}:{self.port}")
            
            # 检查静态文件路径（减少日志输出）
            import os
            magicmirror_dir = os.path.dirname(__file__)  # /home/pi/MagicMirrorPro
            static_path = os.path.join(magicmirror_dir, 'webrtc', 'static')
            if not os.path.exists(static_path):
                logger.warning(f"⚠️ 静态文件目录不存在: {static_path}")
            
            # 使用 AppRunner 和 TCPSite 手动启动服务器（避免信号处理器问题）
            async def start_server():
                runner = web.AppRunner(self.app)
                await runner.setup()
                site = web.TCPSite(runner, host=self.host, port=self.port, ssl_context=ssl_context)
                await site.start()
                logger.info(f"🌐 服务器开始监听: {protocol}://{self.host}:{self.port}")
                
                # 保持运行（使用更长的 sleep 间隔，减少 CPU 占用）
                try:
                    while self.running:
                        await asyncio.sleep(0.5)  # 减少到 0.5 秒，但不会太频繁
                except asyncio.CancelledError:
                    pass
                finally:
                    await runner.cleanup()
                    logger.info("🛑 WebRTC 服务器已停止")
            
            # 运行服务器（使用 run_forever 而不是 run_until_complete）
            try:
                loop.run_until_complete(start_server())
            except KeyboardInterrupt:
                logger.info("🛑 收到中断信号，停止服务器")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"❌ WebRTC 服务器启动失败: {e}", exc_info=True)
            self.running = False
    
    async def cleanup(self):
        """清理所有连接"""
        for pc in self.pcs:
            await pc.close()
        self.pcs.clear()
    
    def start(self):
        """启动 WebRTC 服务器（在后台线程）"""
        try:
            if self.running:
                logger.warning("⚠️ WebRTC 服务器已在运行")
                return
            
            protocol = "https" if self.use_https else "http"
            logger.info(f"🔄 启动 WebRTC 服务器: {protocol}://{self.host}:{self.port}")
            
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True, name="WebRTC-Server")
            self.server_thread.start()
            
            # 等待一下，让服务器有时间启动（减少等待时间）
            import time
            time.sleep(0.5)  # 减少等待时间
            
            if self.server_thread.is_alive():
                logger.info(f"✅ WebRTC 服务器已启动: {protocol}://<树莓派IP>:{self.port}")
            else:
                logger.error("❌ WebRTC 服务器启动失败，线程已退出")
                self.running = False
        except Exception as e:
            logger.error(f"❌ 启动 WebRTC 服务器时发生异常: {e}", exc_info=True)
            self.running = False
    
    def stop(self):
        """停止 WebRTC 服务器"""
        self.running = False
        # 注意：web.run_app 是阻塞的，实际停止需要关闭应用
        logger.info("🛑 WebRTC 服务器已停止")

