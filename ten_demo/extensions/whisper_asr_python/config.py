from pydantic import BaseModel, Field
from dataclasses import dataclass


@dataclass
class WhisperASRConfig(BaseModel):
    model: str = "base"  # tiny, base, small, medium, large
    language: str = "en"  # Language code or None for auto-detect
    sample_rate: int = 16000
    device: str = "cpu"  # "cpu" or "cuda"
    task: str = "transcribe"  # "transcribe" or "translate"
    initial_prompt: str = ""
    temperature: float = 0.0
    no_speech_threshold: float = 0.6
    logprob_threshold: float = -1.0
    compression_ratio_threshold: float = 2.4
    condition_on_previous_text: bool = True
    dump: bool = False
    dump_path: str = "/tmp"
    chunk_length_s: int = 30  # Process audio in chunks
    params: dict = Field(default_factory=dict)

    def update(self, params: dict) -> None:
        """Update configuration with additional parameters."""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_json(self, sensitive_handling: bool = False) -> str:
        """Convert config to JSON string."""
        config_dict = self.model_dump()
        return str(config_dict)
