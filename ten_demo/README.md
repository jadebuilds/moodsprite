# TEN Chatbot Local Demo

This demo sets up a TEN chatbot using entirely local models:
- **ASR**: Whisper (local inference)
- **LLM**: vLLM server (Qwen 2.5 Instruct 7B) at `localhost:8890`
- **TTS**: Coqui TTS (local inference)

## Prerequisites

1. **vLLM Server**: Ensure your vLLM server is running on port 8890
   - The server should be accessible at `http://localhost:8890/v1`
   - It should expose an OpenAI-compatible API

2. **Docker and Docker Compose**: Required for running TEN framework

3. **Node.js LTS v18**: Required for the web UI

## Setup

1. **Navigate to the demo directory**:
   ```bash
   cd ten_demo/ten-framework/ai_agents
   ```

2. **Set up environment variables** (if needed):
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and ensure you have:
   - `AGORA_APP_ID` and `AGORA_APP_CERTIFICATE` (for Agora RTC)
   - No API keys needed for DeepGram, OpenAI, or ElevenLabs (we're using local models)

3. **Start the development containers**:
   ```bash
   docker compose up -d
   ```

4. **Enter the container**:
   ```bash
   docker exec -it ten_agent_dev bash
   ```

5. **Navigate to the demo agent**:
   ```bash
   cd agents/examples/local-demo
   ```

6. **Install dependencies**:
   ```bash
   task install
   ```
   This will install Python dependencies including:
   - `openai-whisper` for ASR
   - `TTS` (Coqui) for TTS
   - Other TEN framework dependencies

7. **Run the agent**:
   ```bash
   task run
   ```

8. **Access the web UI**:
   - TEN Web UI: http://localhost:3001
   - TMAN Designer: http://localhost:49483

## Configuration

### Whisper ASR Configuration

Edit `tenapp/property.json` to configure Whisper:
- `model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`)
- `language`: Language code (e.g., `en`, `zh`, or `null` for auto-detect)
- `device`: `cpu` or `cuda`
- `chunk_length_s`: Process audio in chunks of this many seconds

### vLLM LLM Configuration

The LLM is configured to use your local vLLM server:
- `base_url`: `http://localhost:8890/v1`
- `model`: Should match your vLLM model name
- `api_key`: Can be any dummy value (vLLM doesn't require auth by default)

### Coqui TTS Configuration

Edit `tenapp/property.json` to configure Coqui TTS:
- `model_name`: Coqui TTS model (e.g., `tts_models/en/ljspeech/tacotron2-DDC`)
- `language`: Language code
- `sample_rate`: Output sample rate (default: 22050)
- `device`: `cpu` or `cuda`

## Troubleshooting

1. **Whisper model not loading**: Ensure `openai-whisper` is installed and you have enough disk space for the model
2. **vLLM connection failed**: Verify vLLM is running: `curl http://localhost:8890/health`
3. **Coqui TTS errors**: Check that the TTS model name is valid and you have enough memory
4. **Audio issues**: Ensure sample rates match between ASR (16000) and TTS (22050) - TEN handles conversion

## Notes

- First run will download Whisper and Coqui models, which may take time
- GPU acceleration is optional but recommended for better performance
- The demo uses Agora RTC for audio transport - you'll need Agora credentials

