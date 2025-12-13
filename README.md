# MagicMirrorPro - Voice AI Assistant

A voice AI assistant project running on Raspberry Pi, supporting wake word detection, speech recognition, natural language understanding, and text-to-speech.

## Features

- 🎤 **Wake Word Detection**: Local wake word detection using Vosk
- 🔊 **Speech Recognition**: Integration with Google Speech-to-Text API and local Vosk ASR
- 💬 **Natural Language Understanding**: Pattern matching-based intent recognition and LLM chat
- 🎵 **Text-to-Speech**: Local speech synthesis using Piper TTS
- 🖥️ **Pygame UI**: Clean graphical interface supporting multiple state displays

## Installation

### 1. Clone the Project

```bash
git clone https://github.com/your-username/MagicMirrorPro.git
cd MagicMirrorPro
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

#### 3.1 Copy Configuration File

```bash
cp config.py.example config.py
```

#### 3.2 Configure API Keys

Edit `config.py` and fill in your API keys:

```python
# Google Cloud Speech-to-Text API credentials
GOOGLE_ASR_CREDENTIALS_PATH = "asr/your-google-credentials.json"

# Hugging Face API Key (for LLM)
LLM_API_KEY = "your-huggingface-api-key-here"
```

#### 3.3 Download Google Cloud Credentials File

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a service account and download the JSON credentials file
3. Place the credentials file in the `asr/` directory
4. Update `GOOGLE_ASR_CREDENTIALS_PATH` in `config.py`

#### 3.4 Download TTS Model (Optional)

If you need to use local TTS, download the Piper model:

```bash
# Create model directory
mkdir -p tts/model

# Download model (example)
# Download from https://github.com/rhasspy/piper/releases
# Place the .onnx file in the tts/model/ directory
```

## Project Structure

```
MagicMirrorPro/
├── main.py              # Program entry point
├── config.py            # Configuration file (create yourself)
├── config.py.example    # Configuration file example
├── requirements.txt     # Python dependencies
├── core/                # Core modules
│   ├── app.py          # Main application class (state machine)
│   └── state.py        # State enumeration
├── io_audio/            # Audio input/output
│   ├── recorder.py     # Recording module
│   ├── player.py       # Playback module
│   └── streaming_recorder.py  # Streaming recording and wake word detection
├── asr/                 # Speech recognition
│   ├── google_asr_client.py  # Google ASR client
│   └── models.py       # ASR data models
├── nlu/                 # Natural language understanding
│   ├── pattern_nlu.py  # Pattern matching NLU
│   ├── llm_client.py   # LLM client
│   └── models.py       # NLU data models
├── actions/             # Predefined actions
│   ├── weather.py      # Weather query
│   ├── news.py         # News broadcast
│   └── registry.py     # Action registry
├── tts/                 # Text-to-speech
│   ├── tts_client.py   # TTS client
│   └── models.py       # TTS data models
├── ui/                  # User interface
│   ├── ui_manager.py   # UI manager
│   └── screens.py      # Screen definitions
└── utils/               # Utility functions
    └── logger.py        # Logging utility
```

## Usage

### Run the Program

```bash
python3 main.py
```

### Operation Instructions

- **Wake**: Say the wake word "hello" (configurable in code)
- **Exit**: Press spacebar to exit the program

## State Flow

```
IDLE → LISTENING → THINKING → ACTING/CHATTING → SPEAKING → IDLE
```

1. **IDLE**: Idle state, listening for wake word in the background
2. **LISTENING**: Wake word detected, starting recording and recognition
3. **THINKING**: Recognition complete, performing intent understanding and response generation
4. **ACTING/CHATTING**: Executing predefined actions or displaying chat responses
5. **SPEAKING**: Playing TTS audio
6. **IDLE**: Return to idle state

## Configuration

### Environment Variables

You can override settings in the configuration file through environment variables:

```bash
export GOOGLE_ASR_CREDENTIALS_PATH="/path/to/credentials.json"
export LLM_API_KEY="your-api-key"
export LLM_API_URL="https://router.huggingface.co/v1/chat/completions"
export NEWS_API_KEY="your-news-api-key"  # Optional
```

### Log Files

- Log location: `logs/assistant.log`
- ASR results: `temp/asr_results/asr_results.txt` (rewritten each time)

## Development

### Adding New Predefined Actions

1. Create a new action file in the `actions/` directory
2. Implement the `BaseAction` interface
3. Register the action in `actions/registry.py`
4. Add matching patterns in `nlu/pattern_nlu.py`

### Testing

Run test files:

```bash
# ASR test
python3 test/asr_test.py

# LLM test
python3 test/llm_test.py

# TTS test
python3 test/tts_test.py

# UI test
python3 test/ui_manager_test.py
```

## Important Notes

⚠️ **Important**:
- Do not commit `config.py` and API credential files to Git
- Large files (such as TTS models) are not included in the repository
- Please use `config.py.example` as a configuration template

## License

[Add your license information]

## Contributing

Issues and Pull Requests are welcome!
