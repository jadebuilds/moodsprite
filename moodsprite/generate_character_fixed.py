"""
Super basic getting started: totally hand-rolled script to generate Sera;
we'll framework-ify it later
"""

import os
import sys
import json
import torch
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image

# Add InstantCharacter to path if it's in a subdirectory
instant_character_path = os.path.join(os.path.dirname(__file__), "..", "InstantCharacter")
if os.path.exists(instant_character_path):
    sys.path.insert(0, instant_character_path)
    print(f"Added InstantCharacter path: {instant_character_path}")

# Monkey patch to fix the offload_state_dict issue
import transformers

# Patch CLIPTextModel
original_clip_init = transformers.models.clip.modeling_clip.CLIPTextModel.__init__
def patched_clip_init(self, config, *args, **kwargs):
    kwargs.pop('offload_state_dict', None)
    return original_clip_init(self, config, *args, **kwargs)
transformers.models.clip.modeling_clip.CLIPTextModel.__init__ = patched_clip_init

# Patch T5EncoderModel
original_t5_init = transformers.models.t5.modeling_t5.T5EncoderModel.__init__
def patched_t5_init(self, config, *args, **kwargs):
    kwargs.pop('offload_state_dict', None)
    return original_t5_init(self, config, *args, **kwargs)
transformers.models.t5.modeling_t5.T5EncoderModel.__init__ = patched_t5_init

from pipeline import InstantCharacterFluxPipeline

# Character mood definitions
# TEMPORARY HACK: Simplified for testing
moods = {
    "helpful": [
        "slightly smiling",
    ]
}

# Original moods (commented out for testing):
# moods = {
#     "helpful, earnest, just having met the user and seeking to assist them": [
#         "slightly smiling",
#         "smiling",
#         "smiling broadly",
#         "waving hello, hand to the left",
#         "waving hello, hand to the right",
#     ],
#     "skeptical, polite, reserved": [
#         "slightly smiling with a distant look in the eyes",
#         "frowning slightly",
#         "looking away with a slightly furrowed brow",
#         "looking directly at the camera with a slightly furrowed brow and a look of concern",
#     ],
#     "sad": [
#         "looking deflated",
#         "looking about to cry",
#         "looking dejectedly at the camera",
#     ]
# }

class SeraKeyframeGenerator:
    """Generate Sera keyframes using InstantCharacter."""
    
    def __init__(self, 
                 model_path: str = "/Users/Jade/Documents/ComfyUI/models/ipadapter",
                 base_model: str = "/Users/Jade/Documents/ComfyUI/models/diffusers/models--black-forest-labs--FLUX.1-dev/snapshots/3de623fc3c33e44ffbe2bad470d0f45bccf2eb21",
                 device: Optional[str] = None):
        """Initialize the keyframe generator.
        
        Args:
            model_path: Path to InstantCharacter checkpoints
            base_model: Base model name for FLUX
            device: Device to run the model on (e.g., "cuda", "cpu")
        """
        self.model_path = model_path
        self.base_model = base_model
        self.device = device if device else "cpu"  # Use CPU to avoid memory issues
        self.pipe = None
        
        # Paths
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.subject_image_path = self.project_root / "sera" / "keyframes" / "neutral.png"
        self.output_dir = self.project_root / "sera" / "keyframes"
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_model(self) -> bool:
        """Load the InstantCharacter model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            print("🤖 Loading InstantCharacter model...")
            
            # Set Hugging Face cache to use ComfyUI models
            os.environ["HF_HOME"] = "/Users/Jade/Documents/ComfyUI/models"
            os.environ["HUGGINGFACE_HUB_CACHE"] = "/Users/Jade/Documents/ComfyUI/models"
            
            # Check if model files exist
            ip_adapter_path = os.path.join(self.model_path, "instantcharacter_ip-adapter.bin")
            if not os.path.exists(ip_adapter_path):
                print(f"❌ IP adapter not found: {ip_adapter_path}")
                print("Please download the model files first:")
                print("huggingface-cli download --resume-download Tencent/InstantCharacter --local-dir checkpoints --local-dir-use-symlinks False")
                return False
            
            # Load the pipeline with lower precision to save memory
            self.pipe = InstantCharacterFluxPipeline.from_pretrained(
                self.base_model, 
                torch_dtype=torch.float16  # Use float16 instead of bfloat16 to save memory
            )
            self.pipe.to(self.device)
            print(f"Using device: {self.device}")
            print("Initializing adapter...")
            self.pipe.init_adapter(
                image_encoder_path="google/siglip-so400m-patch14-384",
                image_encoder_2_path="facebook/dinov2-giant",
                subject_ipadapter_cfg=dict(subject_ip_adapter_path=ip_adapter_path, nb_token=1024),
                device=torch.device(self.device)
            )
            print("✅ InstantCharacter model loaded successfully!")
            print(f"Pipeline attributes: {[attr for attr in dir(self.pipe) if 'siglip' in attr.lower()]}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def load_reference_image(self) -> Optional[Image.Image]:
        """Load the neutral reference image.
        
        Returns:
            Reference image or None if not found
        """
        if not self.subject_image_path.exists():
            print(f"❌ Reference image not found: {self.subject_image_path}")
            return None
        
        try:
            image = Image.open(self.subject_image_path).convert('RGB')
            print(f"✅ Loaded reference image: {self.subject_image_path} ({image.size})")
            return image
        except Exception as e:
            print(f"❌ Error loading reference image: {e}")
            return None
    
    def generate_mood_variant(self, 
                            reference_image: Image.Image, 
                            mood: str, 
                            cue: str, 
                            variant_index: int) -> Optional[Image.Image]:
        """Generate a single mood variant.
        
        Args:
            reference_image: The neutral reference image
            mood: Mood category (helpful, skeptical, sad)
            cue: Specific mood description
            variant_index: Index of this variant
            
        Returns:
            Generated image or None if failed
        """
        if not self.pipe:
            print("❌ Model not loaded")
            return None
        
        try:
            # Create detailed prompt
            prompt = f"Sera's mood is '{mood}'. From this initial posture, she has: '{cue}'. She is depicted against a perfectly white background (0xFFFFFF)"
            
            print(f"🎭 Generating {mood} variant {variant_index + 1}: {cue}")
            
            # Generate image
            result = self.pipe(
                prompt=prompt,
                num_inference_steps=28,
                guidance_scale=3.5,
                subject_image=reference_image,
                subject_scale=0.9,
                generator=torch.manual_seed(variant_index), # Use unique seed for each variant
            )
            
            return result.images[0]
        except Exception as e:
            print(f"❌ Error generating variant: {e}")
            return None
    
    def generate_keyframes(self, moods: Dict[str, List[str]]):
        """Generate keyframes for each mood.
        
        Args:
            moods: A dictionary where keys are mood names and values are lists of prompts.
        """
        reference_image = self.load_reference_image()
        if not reference_image:
            raise RuntimeError("Failed to load reference image")

        generated_metadata = {"moods": {}}

        for mood_name, prompts in moods.items():
            print(f"\n=== Generating {mood_name.upper()} variants ===")
            mood_output_dir = self.output_dir / mood_name
            mood_output_dir.mkdir(parents=True, exist_ok=True)
            generated_metadata["moods"][mood_name] = []

            for i, prompt_suffix in enumerate(prompts):
                print(f"Creating {mood_name} variant {i+1}: {prompt_suffix}")
                
                image = self.generate_mood_variant(reference_image, mood_name, prompt_suffix, i)
                if image:
                    # Sanitize prompt_suffix for filename
                    sanitized_prompt = "".join(c if c.isalnum() else "_" for c in prompt_suffix).lower()
                    output_filename = f"sera_{mood_name}_variant_{i+1:02d}_{sanitized_prompt}.png"
                    output_path = mood_output_dir / output_filename
                    image.save(output_path)
                    print(f"💾 Saved: {output_path}")
                    generated_metadata["moods"][mood_name].append({
                        "prompt": f"Sera's mood is '{mood_name}'. From this initial posture, she has: '{prompt_suffix}'. She is depicted against a perfectly white background (0xFFFFFF)",
                        "filename": str(output_path.relative_to(self.output_dir)),
                        "seed": i
                    })
                else:
                    print(f"❌ Failed to generate variant for '{prompt_suffix}'")
        
        metadata_path = self.output_dir / "generated_keyframes.json"
        with open(metadata_path, "w") as f:
            json.dump(generated_metadata, f, indent=4)
        print(f"\n📋 Metadata saved to: {metadata_path}")
        print("\n🎉 Successfully generated mood variants!")
        for mood_name, variants in generated_metadata["moods"].items():
            print(f"  {mood_name}: {len(variants)} variants")

if __name__ == "__main__":
    print("🤖 Sera Keyframe Generator")
    print("========================================")
    
    generator = SeraKeyframeGenerator()
    generator.load_model()
    generator.generate_keyframes(moods)
