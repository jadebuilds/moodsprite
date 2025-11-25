import asyncio
import os
import traceback
from datetime import datetime
from typing import Tuple

from ten_ai_base.helper import PCMWriter
from ten_ai_base.message import (
    ModuleError,
    ModuleErrorCode,
    ModuleType,
    TTSAudioEndReason,
)
from ten_ai_base.struct import TTSTextInput
from ten_ai_base.tts2 import AsyncTTS2BaseExtension
from ten_runtime import AsyncTenEnv
from ten_ai_base.const import LOG_CATEGORY_KEY_POINT, LOG_CATEGORY_VENDOR

try:
    from TTS.api import TTS
    import torch
    import numpy as np
except ImportError:
    TTS = None
    torch = None
    np = None

from .config import CoquiTTSConfig


class CoquiTTSExtension(AsyncTTS2BaseExtension):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.config: CoquiTTSConfig = None
        self.tts_model: TTS = None
        self.current_request_id: str = None
        self.recorder: PCMWriter = None
        self.request_start_ts: datetime | None = None
        self.request_total_audio_duration: int | None = None
        self.recorder_map: dict[str, PCMWriter] = {}
        self.completed_request_ids: set[str] = set()

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        try:
            await super().on_init(ten_env)
            ten_env.log_debug("on_init")

            if TTS is None:
                ten_env.log_error("TTS library not installed. Install with: pip install TTS")
                await self.send_tts_error(
                    request_id="",
                    error=ModuleError(
                        message="TTS library not installed",
                        module=ModuleType.TTS,
                        code=ModuleErrorCode.FATAL_ERROR,
                        vendor_info={},
                    ),
                )
                return

            config_json, _ = await self.ten_env.get_property_to_json("")
            self.config = CoquiTTSConfig.model_validate_json(config_json)
            self.config.update_params()

            self.ten_env.log_info(
                f"config: {self.config.to_str()}",
                category=LOG_CATEGORY_KEY_POINT,
            )

            # Initialize TTS model
            ten_env.log_info(f"Loading Coqui TTS model: {self.config.model_name}")
            device = "cuda" if torch and torch.cuda.is_available() and self.config.device == "cuda" else "cpu"
            
            self.tts_model = TTS(model_name=self.config.model_name, progress_bar=False)
            if device == "cuda":
                self.tts_model.to(device)
            
            ten_env.log_info(f"Coqui TTS model loaded on {device}")

        except Exception as e:
            ten_env.log_error(f"on_init failed: {traceback.format_exc()}")
            await self.send_tts_error(
                request_id="",
                error=ModuleError(
                    message=str(e),
                    module=ModuleType.TTS,
                    code=ModuleErrorCode.FATAL_ERROR,
                    vendor_info={},
                ),
            )

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        # Close all PCMWriter
        for request_id, recorder in self.recorder_map.items():
            try:
                await recorder.flush()
                ten_env.log_debug(f"Flushed PCMWriter for request_id: {request_id}")
            except Exception as e:
                ten_env.log_error(f"Error flushing PCMWriter for request_id {request_id}: {e}")

        await super().on_stop(ten_env)
        ten_env.log_debug("on_stop")

    async def on_deinit(self, ten_env: AsyncTenEnv) -> None:
        await super().on_deinit(ten_env)
        ten_env.log_debug("on_deinit")

    def vendor(self) -> str:
        return "coqui"

    def synthesize_audio_sample_rate(self) -> int:
        return self.config.sample_rate

    def synthesize_audio_channels(self) -> int:
        return 1

    def synthesize_audio_sample_width(self) -> int:
        return 2

    async def request_tts(self, t: TTSTextInput) -> None:
        """Handle TTS requests."""
        try:
            self.ten_env.log_info(
                f"Requesting TTS for text: {t.text}, request ID: {t.request_id}"
            )

            # Check if request_id has already been completed
            if t.request_id in self.completed_request_ids:
                self.ten_env.log_warn(f"Request ID {t.request_id} has already been completed")
                return

            if t.text_input_end:
                self.completed_request_ids.add(t.request_id)

            # New request id
            if self.current_request_id is None or t.request_id != self.current_request_id:
                self.ten_env.log_debug(f"New TTS request with ID: {t.request_id}")
                self.current_request_id = t.request_id
                self.request_total_audio_duration = 0
                self.request_start_ts = datetime.now()

                # Create PCMWriter for new request_id
                if self.config.dump:
                    dump_file_path = os.path.join(
                        self.config.dump_path,
                        f"coqui_tts_dump_{t.request_id}.pcm",
                    )
                    self.recorder_map[t.request_id] = PCMWriter(dump_file_path)
                    self.ten_env.log_info(
                        f"Created PCMWriter for request_id: {t.request_id}"
                    )

                await self.send_tts_audio_start(request_id=t.request_id)

            if self.tts_model is None:
                self.ten_env.log_error("TTS model is not initialized")
                await self.send_tts_error(
                    request_id=t.request_id,
                    error=ModuleError(
                        message="TTS model is not initialized",
                        module=ModuleType.TTS,
                        code=ModuleErrorCode.FATAL_ERROR,
                        vendor_info={"vendor": "coqui"},
                    ),
                )
                return

            # Synthesize audio in executor to avoid blocking
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_audio,
                t.text
            )

            if audio_data is not None:
                # Write to dump file if enabled
                if self.config.dump and t.request_id in self.recorder_map:
                    await self.recorder_map[t.request_id].write(audio_data)

                # Calculate duration
                cur_duration = self.calculate_audio_duration(
                    len(audio_data),
                    self.synthesize_audio_sample_rate(),
                    self.synthesize_audio_channels(),
                    self.synthesize_audio_sample_width(),
                )
                if self.request_total_audio_duration is None:
                    self.request_total_audio_duration = cur_duration
                else:
                    self.request_total_audio_duration += cur_duration

                await self.send_tts_audio_data(audio_data)

            # If this is the end of text input, send audio_end
            if t.text_input_end:
                await self.handle_completed_request(TTSAudioEndReason.REQUEST_END)

        except Exception as e:
            self.ten_env.log_error(f"Error in request_tts: {traceback.format_exc()}")
            await self.send_tts_error(
                request_id=self.current_request_id,
                error=ModuleError(
                    message=str(e),
                    module=ModuleType.TTS,
                    code=ModuleErrorCode.NON_FATAL_ERROR,
                    vendor_info={"vendor": "coqui"},
                ),
            )

    def _synthesize_audio(self, text: str) -> bytes:
        """Synthesize audio synchronously."""
        try:
            # Use TTS API to synthesize
            kwargs = {}
            if self.config.speaker_wav:
                kwargs["speaker_wav"] = self.config.speaker_wav
            if self.config.speaker_idx:
                kwargs["speaker_idx"] = self.config.speaker_idx
            if self.config.language:
                kwargs["language"] = self.config.language

            wav = self.tts_model.tts(text=text, **kwargs)
            
            # Convert to numpy array if needed
            if isinstance(wav, list):
                wav = np.array(wav)
            
            # Ensure it's float32 in range [-1, 1]
            if wav.dtype != np.float32:
                wav = wav.astype(np.float32)
            
            # Normalize if needed
            if wav.max() > 1.0 or wav.min() < -1.0:
                wav = wav / np.max(np.abs(wav))
            
            # Convert to int16 PCM
            wav_int16 = (wav * 32767).astype(np.int16)
            
            # Convert to bytes
            return wav_int16.tobytes()
            
        except Exception as e:
            self.ten_env.log_error(f"Error synthesizing audio: {e}")
            return None

    async def cancel_tts(self) -> None:
        """Cancel current TTS request."""
        await self.handle_completed_request(TTSAudioEndReason.INTERRUPTED)

    async def handle_completed_request(self, reason: TTSAudioEndReason):
        """Handle completed TTS request."""
        if self.current_request_id:
            self.completed_request_ids.add(self.current_request_id)

            # Flush PCMWriter
            if self.config.dump and self.current_request_id in self.recorder_map:
                try:
                    await self.recorder_map[self.current_request_id].flush()
                except Exception as e:
                    self.ten_env.log_error(f"Error flushing PCMWriter: {e}")

            # Send audio_end
            request_event_interval = 0
            if self.request_start_ts is not None:
                request_event_interval = int(
                    (datetime.now() - self.request_start_ts).total_seconds() * 1000
                )
            
            duration_ms = self.request_total_audio_duration if self.request_total_audio_duration is not None else 0
            
            await self.send_tts_audio_end(
                request_id=self.current_request_id,
                request_event_interval_ms=request_event_interval,
                request_total_audio_duration_ms=duration_ms,
                reason=reason,
            )
            
            self.request_start_ts = None
            self.request_total_audio_duration = None

    def calculate_audio_duration(
        self,
        bytes_length: int,
        sample_rate: int,
        channels: int = 1,
        sample_width: int = 2,
    ) -> int:
        """Calculate audio duration in milliseconds."""
        bytes_per_second = sample_rate * channels * sample_width
        duration_seconds = bytes_length / bytes_per_second
        return int(duration_seconds * 1000)
