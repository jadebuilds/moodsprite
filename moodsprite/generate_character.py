"""
Sera Character Keyframe Generator using InstantCharacter.

This script generates mood-based keyframes of Sera using Tencent's InstantCharacter model.
Each mood state has multiple variants based on the character specification.
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

try:
    from pipeline import InstantCharacterFluxPipeline
    INSTANT_CHARACTER_AVAILABLE = True
except ImportError:
    INSTANT_CHARACTER_AVAILABLE = False
    print("Warning: InstantCharacter not available. Using fallback method.")
    print("Run: git clone https://github.com/Tencent-Hunyuan/InstantCharacter.git for full functionality")

# Character mood definitions
moods = {
    "helpful, earnest, just having met the user and seeking to assist them": [
        "slightly smiling",
        "smiling",
        "smiling broadly",
        "waving hello, hand to the left",
        "waving hello, hand to the right",
        "tilting her head to the side in acknowledgement",
    ],
    "skeptical": [
        "slightly smiling with a distant look in the eyes",
        "frowning slightly",
        "looking away with a slightly furrowed brow",
        "looking directly at the camera with a slightly furrowed brow and a look of concern",
    ],
    "sad": [
        "looking deflated",
        "looking about to cry",
        "looking dejectedly at the camera",
    ]
}

"""
Character Mood States:

Helpful: Initial state
* Intents: Explain framework, explain self, support development, express excitement about adoption

Skeptical, polite, reserved: 
* Entry: if the user shows ill intent or is trying to sell us something
* Intents: Explain framework, take a message, address concerns about response to message

Sad:
* Entry: User shows toxicity / insults Sera directly
* Intents: Express sadness, take a message, address concerns about response to message
"""


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
            device: Device to run on (auto-detect if None)
        """
        self.model_path = model_path
        self.base_model = base_model
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
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
        if not INSTANT_CHARACTER_AVAILABLE:
            print("❌ InstantCharacter not available")
            return False
        
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
            
            # Load the pipeline
            self.pipe = InstantCharacterFluxPipeline.from_pretrained(
                self.base_model, 
                torch_dtype=torch.bfloat16
            )
            self.pipe.to(self.device)
            
            # Initialize adapter
            image_encoder_path = "google/siglip-so400m-patch14-384"
            image_encoder_2_path = "facebook/dinov2-giant"
            
            self.pipe.init_adapter(
                image_encoder_path=image_encoder_path,
                image_encoder_2_path=image_encoder_2_path,
                subject_ipadapter_cfg=dict(
                    subject_ip_adapter_path=ip_adapter_path, 
                    nb_token=1024
                ),
            )
            
            print("✅ Model loaded successfully")
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
                generator=torch.manual_seed(42 + variant_index),  # Consistent but varied seeds
            )
            
            return result.images[0]
            
        except Exception as e:
            print(f"❌ Error generating {mood} variant {variant_index + 1}: {e}")
            return None
    
    def save_variant(self, 
                    image: Image.Image, 
                    mood: str, 
                    variant_index: int, 
                    cue: str) -> str:
        """Save a generated variant.
        
        Args:
            image: Generated image
            mood: Mood category
            variant_index: Index of this variant
            cue: Original cue description
            
        Returns:
            Path to saved file
        """
        # Create mood directory
        mood_dir = self.output_dir / mood
        mood_dir.mkdir(exist_ok=True)
        
        # Generate filename
        safe_cue = cue.replace(" ", "_").replace(",", "").replace("'", "").replace("(", "").replace(")", "")
        filename = f"sera_{mood}_variant_{variant_index + 1:02d}_{safe_cue}.png"
        filepath = mood_dir / filename
        
        # Save image
        image.save(filepath, "PNG")
        print(f"💾 Saved: {filepath}")
        
        return str(filepath)
    
    def generate_all_keyframes(self) -> Dict[str, List[Dict]]:
        """Generate all mood keyframes.
        
        Returns:
            Dictionary with generated file information
        """
        # Load reference image
        reference_image = self.load_reference_image()
        if not reference_image:
            return {}
        
        # Load model
        if not self.load_model():
            return {}
        
        print(f"\n🎬 Generating keyframes for {len(moods)} mood states...")
        
        generated_files = {}
        
        for mood, cues in moods.items():
            print(f"\n=== Generating {mood.upper()} keyframes ===")
            generated_files[mood] = []
            
            for i, cue in enumerate(cues):
                # Generate variant
                variant_image = self.generate_mood_variant(
                    reference_image, mood, cue, i
                )
                
                if variant_image:
                    # Save variant
                    filepath = self.save_variant(variant_image, mood, i, cue)
                    
                    generated_files[mood].append({
                        "filepath": filepath,
                        "cue": cue,
                        "variant_index": i,
                        "mood": mood
                    })
                else:
                    print(f"⚠️  Skipped {mood} variant {i + 1}")
        
        # Save metadata
        metadata_path = self.output_dir / "generated_keyframes.json"
        with open(metadata_path, "w") as f:
            json.dump(generated_files, f, indent=2)
        
        print(f"\n✅ Generation complete!")
        print(f"📁 Keyframes saved to: {self.output_dir}")
        print(f"📋 Metadata saved to: {metadata_path}")
        
        return generated_files


def main():
    """Main function to generate Sera keyframes."""
    print("🤖 Sera Keyframe Generator")
    print("=" * 40)
    
    # Initialize generator
    generator = SeraKeyframeGenerator()
    
    # Generate all keyframes
    try:
        generated_files = generator.generate_all_keyframes()
        
        if generated_files:
            total_variants = sum(len(files) for files in generated_files.values())
            print(f"\n🎉 Successfully generated {total_variants} keyframe variants!")
            
            # Print summary
            for mood, files in generated_files.items():
                print(f"  {mood}: {len(files)} variants")
        else:
            print("❌ No keyframes generated")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())