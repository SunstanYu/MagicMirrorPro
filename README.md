# MagicMirrorPro - 语音 AI 助手

运行在树莓派上的语音 AI 助手项目，支持唤醒词检测、语音识别、自然语言理解和文本转语音。

## 功能特性

- 🎤 **唤醒词检测**：使用 Vosk 进行本地唤醒词检测
- 🔊 **语音识别**：集成 Google Speech-to-Text API 和本地 Vosk ASR
- 💬 **自然语言理解**：基于模式匹配的意图识别和 LLM 聊天
- 🎵 **文本转语音**：使用 Piper TTS 进行本地语音合成
- 🖥️ **Pygame UI**：简洁的图形界面，支持多种状态显示

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-username/MagicMirrorPro.git
cd MagicMirrorPro
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

#### 3.1 复制配置文件

```bash
cp config.py.example config.py
```

#### 3.2 配置 API 密钥

编辑 `config.py`，填入你的 API 密钥：

```python
# Google Cloud Speech-to-Text API 凭证
GOOGLE_ASR_CREDENTIALS_PATH = "asr/your-google-credentials.json"

# Hugging Face API Key（用于 LLM）
LLM_API_KEY = "your-huggingface-api-key-here"
```

#### 3.3 下载 Google Cloud 凭证文件

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建服务账号并下载 JSON 凭证文件
3. 将凭证文件放到 `asr/` 目录下
4. 在 `config.py` 中更新 `GOOGLE_ASR_CREDENTIALS_PATH`

#### 3.4 下载 TTS 模型（可选）

如果需要使用本地 TTS，下载 Piper 模型：

```bash
# 创建模型目录
mkdir -p tts/model

# 下载模型（示例）
# 从 https://github.com/rhasspy/piper/releases 下载模型
# 将 .onnx 文件放到 tts/model/ 目录
```

## 项目结构

```
MagicMirrorPro/
├── main.py              # 程序入口
├── config.py            # 配置文件（需要自己创建）
├── config.py.example    # 配置文件示例
├── requirements.txt     # Python 依赖
├── core/                # 核心模块
│   ├── app.py          # 主应用类（状态机）
│   └── state.py        # 状态枚举
├── io_audio/            # 音频输入输出
│   ├── recorder.py     # 录音模块
│   ├── player.py       # 播放模块
│   └── streaming_recorder.py  # 流式录音和唤醒词检测
├── asr/                 # 语音识别
│   ├── google_asr_client.py  # Google ASR 客户端
│   └── models.py       # ASR 数据模型
├── nlu/                 # 自然语言理解
│   ├── pattern_nlu.py  # 模式匹配 NLU
│   ├── llm_client.py   # LLM 客户端
│   └── models.py       # NLU 数据模型
├── actions/             # 预定义动作
│   ├── weather.py      # 天气查询
│   ├── news.py         # 新闻播报
│   └── registry.py     # 动作注册表
├── tts/                 # 文本转语音
│   ├── tts_client.py   # TTS 客户端
│   └── models.py       # TTS 数据模型
├── ui/                  # 用户界面
│   ├── ui_manager.py   # UI 管理器
│   └── screens.py      # 屏幕定义
└── utils/               # 工具函数
    └── logger.py        # 日志工具
```

## 使用方法

### 运行程序

```bash
python3 main.py
```

### 操作说明

- **唤醒**：说出唤醒词 "hello"（可在代码中配置）
- **退出**：按空格键退出程序

## 状态流程

```
IDLE → LISTENING → THINKING → ACTING/CHATTING → SPEAKING → IDLE
```

1. **IDLE**：空闲状态，后台监听唤醒词
2. **LISTENING**：检测到唤醒词，开始录音和识别
3. **THINKING**：识别完成，进行意图理解和回复生成
4. **ACTING/CHATTING**：执行预定义动作或显示聊天回复
5. **SPEAKING**：播放 TTS 音频
6. **IDLE**：回到空闲状态

## 配置说明

### 环境变量

可以通过环境变量覆盖配置文件中的设置：

```bash
export GOOGLE_ASR_CREDENTIALS_PATH="/path/to/credentials.json"
export LLM_API_KEY="your-api-key"
export LLM_API_URL="https://router.huggingface.co/v1/chat/completions"
export NEWS_API_KEY="your-news-api-key"  # 可选
```

### 日志文件

- 日志位置：`logs/assistant.log`
- ASR 结果：`temp/asr_results/asr_results.txt`（每次重写）

## 开发说明

### 添加新的预定义动作

1. 在 `actions/` 目录下创建新的动作文件
2. 实现 `BaseAction` 接口
3. 在 `actions/registry.py` 中注册动作
4. 在 `nlu/pattern_nlu.py` 中添加匹配模式

### 测试

运行测试文件：

```bash
# ASR 测试
python3 test/asr_test.py

# LLM 测试
python3 test/llm_test.py

# TTS 测试
python3 test/tts_test.py

# UI 测试
python3 test/ui_manager_test.py
```

## 注意事项

⚠️ **重要**：
- 不要将 `config.py` 和 API 凭证文件提交到 Git
- 大文件（如 TTS 模型）不会包含在仓库中
- 请使用 `config.py.example` 作为配置模板

## 许可证

[添加你的许可证信息]

## 贡献

欢迎提交 Issue 和 Pull Request！
