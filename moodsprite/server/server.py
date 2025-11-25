"""
gRPC Moodsprite Server

Serves Sera character keyframes and streams live cues.
This is a research spike - crashes immediately on any error.
"""

import os
import sys
import uuid
import gzip
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional
from concurrent import futures
import threading
from datetime import datetime

import grpc
from PIL import Image

# Import generated protobuf classes (will be created by build_proto.sh)
try:
    import moodsprite_pb2
    import moodsprite_pb2_grpc
except ImportError:
    # Try importing from the server directory
    import sys
    from pathlib import Path
    server_dir = Path(__file__).parent
    sys.path.insert(0, str(server_dir))
    try:
        import moodsprite_pb2
        import moodsprite_pb2_grpc
    except ImportError:
        print("❌ Protobuf classes not found. Run: ./build_proto.sh")
        sys.exit(1)

# Hard-coded mood definitions from generate_character.py
MOODS = {
    "helpful": [
        "slightly smiling",
        "smiling",
        "smiling broadly",
        "waving hello, hand to the left",
        "waving hello, hand to the right",
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


class MoodspriteService(moodsprite_pb2_grpc.MoodspriteServiceServicer):
    """gRPC service implementation for Moodsprite."""
    
    def __init__(self, keyframes_dir: Path):
        self.keyframes_dir = keyframes_dir
        self.cached_character: Optional[moodsprite_pb2.SpriteCharacter] = None
        self._load_and_cache_character()
    
    def _load_and_cache_character(self):
        """Load all character data and cache it as base64-encoded, gzipped data."""
        print("🔄 Loading and caching Sera character...")
        
        # Create the character version
        character_version = moodsprite_pb2.SpriteCharacterVersion()
        character_version.name = "Sera"
        character_version.notes = "SLR-9 'Soft Liaison, Reflective' model - Experimental empathic interface android"
        character_version.changelog = "Initial version with basic mood keyframes"
        
        # Load subject image (neutral reference)
        subject_image_path = self.keyframes_dir / "neutral.png"
        if not subject_image_path.exists():
            raise RuntimeError(f"❌ Subject image not found: {subject_image_path}")
        
        subject_keyframe = self._create_sprite_keyframe(
            subject_image_path, 
            "neutral reference image",
            "subject"
        )
        character_version.subject_image.CopyFrom(subject_keyframe)
        
        # Load moods
        for mood_name, cue_descriptions in MOODS.items():
            mood_dir = self.keyframes_dir / mood_name
            
            if not mood_dir.exists():
                raise RuntimeError(f"❌ Keyframe directory not found: {mood_dir}")
            
            if not any(mood_dir.iterdir()):
                raise RuntimeError(f"❌ Keyframe directory is empty: {mood_dir}")
            
            print(f"📁 Loading {mood_name} keyframes from {mood_dir}")
            
            # Create sprite mood
            sprite_mood = moodsprite_pb2.SpriteMood()
            sprite_mood.uuid = str(uuid.uuid4())
            sprite_mood.description = self._get_mood_description(mood_name)
            sprite_mood.notes = f"Generated from {len(cue_descriptions)} keyframe descriptions"
            
            # Load keyframes
            for i, description in enumerate(cue_descriptions):
                # Find matching image file
                image_file = self._find_keyframe_image(mood_dir, description, i)
                if not image_file:
                    raise RuntimeError(f"❌ Keyframe image not found for {mood_name}: {description}")
                
                # Create sprite keyframe
                sprite_keyframe = self._create_sprite_keyframe(image_file, description)
                sprite_mood.keyframes.append(sprite_keyframe)
                
                print(f"  ✅ Loaded: {image_file.name}")
            
            character_version.moods.append(sprite_mood)
        
        # Create the character
        self.cached_character = moodsprite_pb2.SpriteCharacter()
        self.cached_character.semantic_version = "1.0.0"
        self.cached_character.character.CopyFrom(character_version)
        
        total_keyframes = sum(len(mood.keyframes) for mood in character_version.moods)
        print(f"✅ Cached Sera character v{self.cached_character.semantic_version} with {len(character_version.moods)} moods and {total_keyframes} keyframes")
    
    def _get_mood_description(self, mood_name: str) -> str:
        """Get a detailed description for a mood."""
        descriptions = {
            "helpful": "helpful, open, having newly met the user and coming in with warmth and positive expectations",
            "skeptical": "skeptical, polite, reserved - when the user shows ill intent or is trying to sell something",
            "sad": "sad and deflated - when the user shows toxicity or insults Sera directly"
        }
        return descriptions.get(mood_name, f"{mood_name} mood state")
    
    def _create_sprite_keyframe(self, image_path: Path, description: str, keyframe_type: str = "mood") -> moodsprite_pb2.SpriteKeyframe:
        """Create a SpriteKeyframe from an image file."""
        keyframe = moodsprite_pb2.SpriteKeyframe()
        keyframe.uuid = str(uuid.uuid4())
        keyframe.description = description
        keyframe.image_data = self._load_and_encode_image(image_path)
        return keyframe
    
    def _find_keyframe_image(self, mood_dir: Path, description: str, index: int) -> Optional[Path]:
        """Find the keyframe image file for a given description and index."""
        # Try different naming patterns
        patterns = [
            f"sera_{mood_dir.name}_variant_{index + 1:02d}_{description.replace(' ', '_').replace(',', '').replace("'", '').replace('(', '').replace(')', '')}.png",
            f"sera_{mood_dir.name}_variant_{index + 1:02d}.png",
            f"variant_{index + 1:02d}.png",
            f"{index + 1:02d}.png",
        ]
        
        for pattern in patterns:
            image_file = mood_dir / pattern
            if image_file.exists():
                return image_file
        
        # If no pattern matches, try to find any PNG file
        png_files = list(mood_dir.glob("*.png"))
        if png_files and index < len(png_files):
            return png_files[index]
        
        return None
    
    def _load_and_encode_image(self, image_path: Path) -> bytes:
        """Load image and return as base64-encoded, gzipped bytes."""
        try:
            # Load image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes
                import io
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()
            
            # Encode as base64
            base64_data = base64.b64encode(img_data)
            
            # Compress with gzip
            gzipped_data = gzip.compress(base64_data)
            
            return gzipped_data
            
        except Exception as e:
            raise RuntimeError(f"❌ Error loading image {image_path}: {e}")
    
    def GetCharacter(self, request, context):
        """Return the complete Sera character data."""
        print("📤 Serving GetCharacter request")
        
        if not self.cached_character:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Character not loaded")
            return
        
        return self.cached_character
    
    def StartSession(self, request, context):
        """Start a live session streaming keyframes from the 'helpful' mood."""
        print("📡 Starting live session")
        
        if not self.cached_character:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Character not loaded")
            return
        
        # Find the helpful mood
        helpful_mood = None
        for mood in self.cached_character.character.moods:
            if "helpful" in mood.description.lower():
                helpful_mood = mood
                break
        
        if not helpful_mood:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Helpful mood not found")
            return
        
        # Simple streaming without cancellation check
        for keyframe in helpful_mood.keyframes:
            # Create live cue
            cue = moodsprite_pb2.LiveSpriteKeyframeCue()
            cue.timestamp.FromDatetime(datetime.now())
            cue.duration_valid_ms = 1000  # 1 second
            cue.keyframe_uuid = keyframe.uuid
            cue.explanation = f"Streaming {keyframe.description} from {helpful_mood.description}"
            # alt_cue_text is optional, so we don't set it
            
            print(f"📤 Streaming keyframe: {keyframe.description}")
            yield cue
            
            # Wait 1 second
            time.sleep(1.0)
    
    def GetCharacterHistory(self, request, context):
        """Return character history (stub implementation)."""
        print("📤 Serving GetCharacterHistory request")
        
        if not self.cached_character:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Character not loaded")
            return
        
        # For now, just return the current character as the only version
        history = moodsprite_pb2.SpriteCharacterHistory()
        history.current_name = self.cached_character.character.name
        history.latest_version = self.cached_character.semantic_version
        history.versions.append(self.cached_character.character)
        
        return history


def serve(port: int = 50051):
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Get keyframes directory (now in sera/ directory)
    keyframes_dir = Path(__file__).parent.parent.parent / "sera" / "keyframes"
    keyframes_dir = keyframes_dir.resolve()  # Convert to absolute path
    
    # Add service
    moodsprite_pb2_grpc.add_MoodspriteServiceServicer_to_server(
        MoodspriteService(keyframes_dir), server
    )
    
    # Start server
    listen_addr = f'[::]:{port}'
    server.add_insecure_port(listen_addr)
    
    print(f"🚀 Starting Moodsprite gRPC server on {listen_addr}")
    print(f"📁 Keyframes directory: {keyframes_dir}")
    
    try:
        server.start()
        print("✅ Server started successfully")
        print("Press Ctrl+C to stop...")
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop(0)


if __name__ == "__main__":
    serve()
