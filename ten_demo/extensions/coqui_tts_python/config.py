from typing import Optional
from pydantic import BaseModel


class CoquiTTSConfig(BaseModel):
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    vocoder_name: Optional[str] = None  # Auto-select if None
    speaker_wav: Optional[str] = None  # Path to speaker reference audio for XTTS
    language: str = "en"
    speaker_idx: Optional[str] = None
    sample_rate: int = 22050
    device: str = "cpu"  # "cpu" or "cuda"
    dump: bool = False
    dump_path: str = "/tmp"
    params: dict = {}

    def update_params(self) -> None:
        """Update configuration with additional parameters."""
        if self.params:
            for key, value in self.params.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def to_str(self, sensitive_handling: bool = False) -> str:
        """Convert config to string."""
        config_dict = self.model_dump()
        return str(config_dict)
