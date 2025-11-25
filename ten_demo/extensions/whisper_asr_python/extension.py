import asyncio
import numpy as np
from datetime import datetime
from typing import Optional

from typing_extensions import override
from ten_ai_base.asr import (
    ASRBufferConfig,
    ASRBufferConfigModeDiscard,
    ASRResult,
    AsyncASRBaseExtension,
)
from ten_ai_base.message import (
    ModuleError,
    ModuleErrorCode,
)
from ten_runtime import (
    AsyncTenEnv,
    AudioFrame,
)
from ten_ai_base.const import (
    LOG_CATEGORY_KEY_POINT,
    LOG_CATEGORY_VENDOR,
)
from ten_ai_base.dumper import Dumper

try:
    import whisper
except ImportError:
    whisper = None

from .config import WhisperASRConfig


class WhisperASRExtension(AsyncASRBaseExtension):
    def __init__(self, name: str):
        super().__init__(name)
        self.connected: bool = False
        self.config: Optional[WhisperASRConfig] = None
        self.model: Optional[whisper.Whisper] = None
        self.audio_buffer: bytearray = bytearray()
        self.audio_dumper: Optional[Dumper] = None
        self.last_finalize_timestamp: int = 0
        self.processing_task: Optional[asyncio.Task] = None
        self.processing_lock = asyncio.Lock()

    @override
    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        await super().on_deinit(ten_env)
        if self.audio_dumper:
            await self.audio_dumper.stop()
            self.audio_dumper = None
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

    @override
    def vendor(self) -> str:
        """Get the name of the ASR vendor."""
        return "whisper"

    @override
    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        await super().on_init(ten_env)

        if whisper is None:
            ten_env.log_error(
                "whisper library not installed. Install with: pip install openai-whisper"
            )
            await self.send_asr_error(
                ModuleError(
                    module="asr",
                    code=ModuleErrorCode.FATAL_ERROR.value,
                    message="whisper library not installed",
                ),
            )
            return

        config_json, _ = await ten_env.get_property_to_json("")
        try:
            self.config = WhisperASRConfig.model_validate_json(config_json)
            if self.config.params:
                self.config.update(self.config.params)
            ten_env.log_info(
                f"KEYPOINT vendor_config: {self.config.to_json()}",
                category=LOG_CATEGORY_KEY_POINT,
            )

            if self.config.dump:
                import os

                dump_file_path = os.path.join(
                    self.config.dump_path, "whisper_asr_dump.pcm"
                )
                self.audio_dumper = Dumper(dump_file_path)

            # Load Whisper model
            ten_env.log_info(f"Loading Whisper model: {self.config.model}")
            self.model = whisper.load_model(
                self.config.model, device=self.config.device
            )
            ten_env.log_info("Whisper model loaded successfully")
            self.connected = True

        except Exception as e:
            ten_env.log_error(f"invalid property or model loading failed: {e}")
            self.config = WhisperASRConfig.model_validate_json("{}")
            await self.send_asr_error(
                ModuleError(
                    module="asr",
                    code=ModuleErrorCode.FATAL_ERROR.value,
                    message=str(e),
                ),
            )

    @override
    async def start_connection(self) -> None:
        assert self.config is not None
        self.ten_env.log_info("start_connection")
        self.connected = True

    @override
    async def finalize(self, session_id: Optional[str]) -> None:
        assert self.config is not None
        self.last_finalize_timestamp = int(datetime.now().timestamp() * 1000)
        self.ten_env.log_info(
            f"vendor_cmd: finalize start at {self.last_finalize_timestamp}",
            category=LOG_CATEGORY_VENDOR,
        )
        await self._process_audio_buffer(finalize=True)

    async def _process_audio_buffer(self, finalize: bool = False):
        """Process accumulated audio buffer with Whisper."""
        if not self.model or not self.config:
            return

        async with self.processing_lock:
            if len(self.audio_buffer) == 0:
                return

            # Convert PCM bytes to numpy array
            audio_data = (
                np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32)
                / 32768.0
            )

            if len(audio_data) < self.config.sample_rate * 0.5:  # Less than 0.5 seconds
                if not finalize:
                    return
                # For finalize, process even short audio

            try:
                # Run Whisper in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._run_whisper, audio_data)

                if result and result.get("text"):
                    text = result["text"].strip()
                    if text:
                        start_ms = 0  # Approximate
                        duration_ms = int(
                            len(audio_data) / self.config.sample_rate * 1000
                        )
                        language = result.get("language", self.config.language)

                        await self._handle_asr_result(
                            text=text,
                            final=finalize,
                            start_ms=start_ms,
                            duration_ms=duration_ms,
                            language=language,
                        )

                # Clear buffer after processing
                self.audio_buffer.clear()

            except Exception as e:
                self.ten_env.log_error(f"Error processing audio with Whisper: {e}")

    def _run_whisper(self, audio_data: np.ndarray) -> dict:
        """Run Whisper transcription synchronously."""
        options = {
            "language": self.config.language if self.config.language else None,
            "task": self.config.task,
            "temperature": self.config.temperature,
            "no_speech_threshold": self.config.no_speech_threshold,
            "logprob_threshold": self.config.logprob_threshold,
            "compression_ratio_threshold": self.config.compression_ratio_threshold,
            "condition_on_previous_text": self.config.condition_on_previous_text,
            "initial_prompt": self.config.initial_prompt
            if self.config.initial_prompt
            else None,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}

        result = self.model.transcribe(audio_data, **options)
        return result

    async def _handle_asr_result(
        self,
        text: str,
        final: bool,
        start_ms: int = 0,
        duration_ms: int = 0,
        language: str = "",
    ):
        """Handle the ASR result from Whisper."""
        assert self.config is not None

        if final:
            await self._finalize_end()

        asr_result = ASRResult(
            text=text,
            final=final,
            start_ms=start_ms,
            duration_ms=duration_ms,
            language=language,
            words=[],
        )
        await self.send_asr_result(asr_result)

    async def _finalize_end(self) -> None:
        """Handle finalize end logic."""
        if self.last_finalize_timestamp != 0:
            timestamp = int(datetime.now().timestamp() * 1000)
            latency = timestamp - self.last_finalize_timestamp
            self.ten_env.log_debug(
                f"KEYPOINT finalize end at {timestamp}, latency: {latency}ms"
            )
            self.last_finalize_timestamp = 0
            await self.send_asr_finalize_end()

    @override
    def is_connected(self) -> bool:
        return self.connected and self.model is not None

    @override
    def buffer_strategy(self) -> ASRBufferConfig:
        return ASRBufferConfigModeDiscard()

    @override
    def input_audio_sample_rate(self) -> int:
        assert self.config is not None
        return self.config.sample_rate

    @override
    async def send_audio(self, frame: AudioFrame, session_id: Optional[str]) -> bool:
        assert self.config is not None

        buf = frame.lock_buf()
        try:
            if self.audio_dumper:
                await self.audio_dumper.push_bytes(bytes(buf))

            # Accumulate audio in buffer
            self.audio_buffer.extend(buf)

            # Process buffer periodically (every chunk_length_s seconds of audio)
            buffer_duration_s = len(self.audio_buffer) / (
                self.config.sample_rate * 2
            )  # 2 bytes per sample (int16)
            if buffer_duration_s >= self.config.chunk_length_s:
                # Process in background
                if self.processing_task and not self.processing_task.done():
                    self.processing_task.cancel()
                self.processing_task = asyncio.create_task(
                    self._process_audio_buffer(finalize=False)
                )

        finally:
            frame.unlock_buf(buf)

        return True
