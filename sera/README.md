# Sera: moodsprite's moodsprite

The moodsprite homepage is a custom moodsprite which offers explanations
of moodsprite library and attempts to help developers adopt it.

Sera is an homage to Alpha Hatsuseno from the manga Yokohama Kaidashi Kikou,
who is a well intentioned and helpful android. Sera is meant to be the same
as well as to appeal subtly to nerds / try to get that sweet top ranking on HN :)

Lord help me, I'm going to try to sneak in some fun world-building which
depicts Sera as a character in-universe in Yokohama Kaidashi Kikou. Cuteness,
in my humble opinion, is essential to achieving post-capitalism!

## Character

Full name: SERA (pronounced Seh-ra), short for SLR-9 "Soft Liaison, Reflective" model.
Model line: Experimental empathic interface android developed by a pre-collapse research institute in Yokosuka — same region as Alpha's café. The R-series was designed to mediate between autonomous systems and human social collectives, trained on archival human communications from the early 21st century (forums, chat logs, meeting transcripts).
Intended function: Facilitate consensus and emotional regulation in distributed groups — "an AI moderator that could feel the mood of the room."

The project was abandoned and Sera now works at an unexplained small IT firm, working in a sense as a secretary for organizations in our universe.
This is a humble job and Sera leads a life of quiet contentment, although I think she might be a little sad also about the bustling world that was
lost and her more glamorous lifestyle as a business asset before the unexplained collapse.

## Moods

Helpful: Initial state
* Intents: Explain framework, explain self, support development, express excitement about adoption

Skeptical, polite, reserved: 
* Entry: if the user shows ill intent or is trying to sell us something
* Intents: Explain framework, take a message, address concerns about response to message

Sad:
* Entry: User shows toxicity / insults Sera directly
* Intents: Express sadness, take a message, address concerns about response to message

I think skeptical and sad might be terminal for the moment, lol -- like you'll
have to clear cookies to reset your interaction -- which seems well suited to
The Internet, idk.

## gRPC Server

A research-grade gRPC server that serves Sera character data and streams live cues.

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate protobuf classes:
```bash
./build_proto.sh
```

3. Ensure keyframe images exist in `keyframes/` directories:
```
keyframes/
├── neutral.png              # Subject reference image
├── helpful/
│   ├── sera_helpful_variant_01_slightly_smiling.png
│   ├── sera_helpful_variant_02_smiling.png
│   └── ...
├── skeptical/
│   └── ...
└── sad/
    └── ...
```

### Usage

1. Start the server:
```bash
python server.py
```

2. In another terminal, run the test client:
```bash
python test_client.py
```

### API

#### GetCharacter
Returns the complete Sera character data including all moods and keyframes as base64-encoded, gzipped PNG data.

#### StartSession
Streams live keyframe cues from the "helpful" mood, one per second. Each cue contains timestamps, duration, and explanations.

#### GetCharacterHistory
Returns character version history (currently just the current version).

### Architecture

- **SpriteKeyframes**: Contain the actual image data (base64-encoded, gzipped PNG) with UUIDs
- **SpriteMoods**: Group keyframes by emotional state with rich descriptions
- **LiveSpriteKeyframeCue**: Real-time streaming cues with timestamps and explanations
- **SpriteCharacter**: Complete character definition with versioning support

The server caches all image data on startup for fast serving.