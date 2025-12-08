# 语音 AI 助手 - 项目骨架

这是一个运行在树莓派上的语音 AI 助手项目骨架代码。项目采用模块化设计，便于后续扩展和实现具体功能。

## 项目结构

```
MagicMirrorPro/
├── main.py                 # 程序入口
├── config.py               # 全局配置
├── requirements.txt        # 依赖列表
├── README.md              # 项目说明
│
├── core/                   # 核心模块
│   ├── app.py             # 主应用类和状态机
│   └── state.py           # 状态枚举
│
├── io_audio/              # 音频输入输出
│   ├── recorder.py        # 录音模块
│   └── player.py          # 播放模块
│
├── asr/                   # 语音识别
│   ├── google_asr_client.py    # Google ASR 客户端
│   ├── local_asr_stub.py        # 本地 ASR 占位实现
│   └── models.py               # ASR 数据模型
│
├── nlu/                   # 自然语言理解
│   ├── llm_client.py      # LLM 客户端
│   ├── intent_parser.py   # 意图解析器
│   └── models.py          # NLU 数据模型
│
├── actions/               # 动作执行
│   ├── base.py            # 动作基类
│   ├── weather.py          # 天气动作
│   ├── news.py            # 新闻动作
│   └── registry.py        # 动作注册表
│
├── ui/                    # UI 模块
│   ├── ui_manager.py      # UI 管理器
│   ├── screens.py         # 屏幕类
│   └── constants.py       # UI 常量
│
├── tts/                   # 文本转语音
│   ├── tts_client.py      # TTS 客户端
│   └── models.py          # TTS 数据模型
│
└── utils/                 # 工具模块
    ├── logger.py          # 日志工具
    └── paths.py           # 路径管理
```

## 功能流程

1. **唤醒** → 按键（空格键）或唤醒词检测
2. **录音** → 采集麦克风音频，保存为 FLAC/WAV
3. **ASR** → 语音转文字（Google ASR 或本地 ASR）
4. **NLU/LLM** → 语义理解和意图识别
5. **意图路由** → 判断是预定义动作还是普通聊天
6. **执行动作/聊天** → 执行相应功能并更新 UI
7. **TTS** → 文本转语音
8. **播放** → 播放回复音频
9. **回到空闲** → 等待下一次唤醒

## 状态机

```
IDLE → LISTENING → TRANSCRIBING → THINKING → ACTING/CHATTING → SPEAKING → IDLE
```

## 安装和运行

### 1. 安装依赖

```bash
cd /home/pi/MagicMirrorPro
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py` 设置：
- Google ASR 凭证路径
- LLM API 密钥和 URL
- 音频参数
- UI 设置

### 3. 运行

```bash
python main.py
```

### 4. 使用

- 按 **空格键** 唤醒助手
- 程序会模拟完整的处理流程
- 在 pygame 窗口中查看 UI 状态变化

## 开发说明

### 当前状态

- ✅ 项目骨架和模块划分已完成
- ✅ 状态机和主循环框架已实现
- ✅ UI 框架（pygame）已搭建
- ⚠️ 大部分功能为占位实现（TODO）

### 待实现功能

1. **录音功能** (`io_audio/recorder.py`)
   - 使用 pyaudio 或 sounddevice 实现真实录音
   - 保存为 FLAC/WAV 格式

2. **音频播放** (`io_audio/player.py`)
   - 使用 pygame.mixer 实现音频播放

3. **Google ASR** (`asr/google_asr_client.py`)
   - 实现 Google Cloud Speech-to-Text API 调用

4. **本地 ASR** (`asr/local_asr_stub.py`)
   - 可以集成 vosk 或其他本地 ASR 引擎

5. **LLM 客户端** (`nlu/llm_client.py`)
   - 实现 OpenAI、Claude 或其他 LLM API 调用

6. **TTS 客户端** (`tts/tts_client.py`)
   - 实现 gTTS、pyttsx3 或其他 TTS 引擎

7. **动作实现** (`actions/`)
   - 实现天气、新闻等具体动作的业务逻辑

### 扩展新功能

1. **添加新动作**：
   - 在 `actions/` 目录创建新动作类（继承 `BaseAction`）
   - 在 `actions/registry.py` 中注册

2. **添加新 UI 屏幕**：
   - 在 `ui/screens.py` 中创建新屏幕类（继承 `BaseScreen`）
   - 在 `ui/ui_manager.py` 中注册

3. **切换 ASR/TTS 引擎**：
   - 在 `core/app.py` 中修改初始化代码
   - 或通过配置文件控制

## 注意事项

- 当前代码使用占位实现，可以运行但不会执行真实功能
- 需要逐步实现各个模块的具体逻辑
- 确保树莓派有足够的权限访问麦克风和音频设备
- 如果使用 Google ASR，需要配置服务账号凭证

## 许可证

本项目为骨架代码，供学习和开发使用。

