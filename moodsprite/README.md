# Sera Keyframe Generator

This directory contains the extended `generate_character.py` script that uses Tencent's InstantCharacter model to generate mood-based keyframes of Sera.

## Overview

The script generates multiple variants for each of Sera's mood states:
- **Helpful**: 5 variants (smiling, waving, etc.)
- **Skeptical**: 4 variants (distant look, frowning, etc.)  
- **Sad**: 3 variants (deflated, teary, etc.)

## Quick Start

### 1. Setup InstantCharacter

Run the setup script to clone the repository and install dependencies:

```bash
python setup_instantcharacter.py
```

This will:
- Clone the InstantCharacter repository
- Install required Python packages
- Download the model files
- Verify the setup

### 2. Generate Keyframes

Ensure you have the neutral reference image at `../sera/neutral.png`, then run:

```bash
python generate_character.py
```

## Manual Setup

If the automated setup doesn't work, follow these steps:

### 1. Clone InstantCharacter

```bash
cd ..
git clone https://github.com/Tencent-Hunyuan/InstantCharacter.git
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Model Files

```bash
cd InstantCharacter
huggingface-cli download --resume-download Tencent/InstantCharacter --local-dir checkpoints --local-dir-use-symlinks False
```

If you have access issues, use the mirror:

```bash
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download --resume-download Tencent/InstantCharacter --local-dir checkpoints --local-dir-use-symlinks False
```

## Output Structure

Generated keyframes are saved in the following structure:

```
sera/
└── keyframes/
    ├── helpful/
    │   ├── sera_helpful_variant_01_slightly_smiling.png
    │   ├── sera_helpful_variant_02_smiling.png
    │   ├── sera_helpful_variant_03_smiling_broadly.png
    │   ├── sera_helpful_variant_04_waving_hello_hand_to_the_left.png
    │   └── sera_helpful_variant_05_waving_hello_hand_to_the_right.png
    ├── skeptical/
    │   ├── sera_skeptical_variant_01_slightly_smiling_with_a_distant_look_in_the_eyes.png
    │   ├── sera_skeptical_variant_02_frowning_slightly.png
    │   ├── sera_skeptical_variant_03_looking_away_with_a_slightly_furrowed_brow.png
    │   └── sera_skeptical_variant_04_looking_directly_at_the_camera_with_a_slightly_furrowed_brow_and_a_look_of_concern.png
    ├── sad/
    │   ├── sera_sad_variant_01_looking_deflated.png
    │   ├── sera_sad_variant_02_looking_about_to_cry.png
    │   └── sera_sad_variant_03_looking_dejectedly_at_the_camera.png
    └── generated_keyframes.json
```

## Configuration

The script automatically detects:
- Reference image: `../sera/neutral.png`
- Output directory: `../sera/keyframes/`
- Model path: `../InstantCharacter/checkpoints/`

You can modify these paths in the `SeraKeyframeGenerator` class if needed.

## Requirements

- Python 3.8+
- CUDA-compatible GPU (recommended, 22GB+ VRAM)
- At least 50GB free disk space for model files

## Troubleshooting

### Model Loading Issues
- Ensure you have sufficient VRAM (22GB+ recommended)
- Try running on CPU by modifying the device parameter
- Check that all model files are downloaded correctly

### Import Errors
- Make sure the InstantCharacter repository is cloned
- Verify that all dependencies are installed
- Check that the pipeline.py file exists in the InstantCharacter directory

### Generation Failures
- Ensure the reference image exists and is readable
- Check that you have write permissions for the output directory
- Verify that the model files are complete

## Character Specification

The mood states are based on Sera's character design:

- **Helpful** (Default): Welcoming, supportive, excited about adoption
- **Skeptical** (Ill intent): Reserved, cautious, concerned
- **Sad** (Toxicity): Deflated, melancholic, dejected

Each mood has multiple visual variants to provide variety in the character's expressions and poses.

## Next Steps

After generating the keyframes:
1. Review the generated images
2. Select the best variants for each mood
3. Integrate them into your moodsprite configuration
4. Use them in your character interface

The generated metadata file (`generated_keyframes.json`) contains information about each variant for easy integration into your application.

