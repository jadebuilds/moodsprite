#!/usr/bin/env python3
"""
Setup script for InstantCharacter integration.

This script helps set up the InstantCharacter environment and downloads
the necessary model files for generating Sera keyframes.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, cwd: str = None) -> bool:
    """Run a shell command and return success status."""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        print("✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def setup_instantcharacter():
    """Set up InstantCharacter environment."""
    print("🤖 Setting up InstantCharacter for Sera keyframe generation")
    print("=" * 60)
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    instant_character_dir = project_root / "InstantCharacter"
    
    # Step 1: Clone InstantCharacter repository
    if not instant_character_dir.exists():
        print("\n📥 Cloning InstantCharacter repository...")
        clone_cmd = "git clone https://github.com/Tencent-Hunyuan/InstantCharacter.git"
        if not run_command(clone_cmd, str(project_root)):
            print("❌ Failed to clone InstantCharacter repository")
            return False
    else:
        print("✅ InstantCharacter repository already exists")
    
    # Step 2: Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        install_cmd = f"pip install -r {requirements_file}"
        if not run_command(install_cmd):
            print("❌ Failed to install Python dependencies")
            return False
    else:
        print("⚠️  Requirements file not found, installing basic dependencies...")
        basic_deps = [
            "torch>=2.0.0",
            "torchvision>=0.15.0", 
            "transformers>=4.30.0",
            "diffusers>=0.20.0",
            "accelerate>=0.20.0",
            "Pillow>=9.0.0",
            "huggingface-hub>=0.16.0"
        ]
        for dep in basic_deps:
            if not run_command(f"pip install {dep}"):
                print(f"❌ Failed to install {dep}")
                return False
    
    # Step 3: Download model files
    print("\n📥 Downloading InstantCharacter model files...")
    checkpoints_dir = instant_character_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    
    # Try downloading from Hugging Face
    download_cmd = "huggingface-cli download --resume-download Tencent/InstantCharacter --local-dir checkpoints --local-dir-use-symlinks False"
    if not run_command(download_cmd, str(instant_character_dir)):
        print("⚠️  Failed to download from Hugging Face, trying mirror...")
        # Try mirror
        mirror_cmd = "HF_ENDPOINT=https://hf-mirror.com " + download_cmd
        if not run_command(mirror_cmd, str(instant_character_dir)):
            print("❌ Failed to download model files")
            print("Please manually download the model files to the checkpoints directory")
            return False
    
    # Step 4: Verify setup
    print("\n🔍 Verifying setup...")
    
    # Check if key files exist
    required_files = [
        "checkpoints/instantcharacter_ip-adapter.bin",
        "pipeline.py"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = instant_character_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing!")
            all_files_exist = False
    
    if all_files_exist:
        print("\n🎉 Setup complete! You can now run generate_character.py")
        print("\nNext steps:")
        print("1. Ensure sera/neutral.png exists")
        print("2. Run: python generate_character.py")
    else:
        print("\n⚠️  Setup incomplete. Some files are missing.")
        print("Please check the InstantCharacter repository for additional setup steps.")
    
    return all_files_exist


def main():
    """Main setup function."""
    try:
        success = setup_instantcharacter()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
