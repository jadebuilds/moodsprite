# moodsprite: cheap'n'cheerful animated AI avatars for groups

moodsprite aims to be a simple first pass at creating animated avatars
for trustworthy AI agents.

Trust is about prediction confidence of future behavior; moodsprite is intended
to tap in to this effect by communicating clues about future behavior through
simulated "body language".

# How it works

## Basic architecture

1. Uses [Rasa](https://github.com/RasaHQ/rasa) for procedural chatbot flows;
2. Implements a thin "mood" adapter which modulates Rasa expressions based on
  higher-level / asynchronous evaluation of intent which modulates Rasa
  (e.g. by enabling or disabling intents)
3. Generates sprite keyframe images using InstantCharacter for consistency;
4. Offers real-time audio chat using [TEN](https://github.com/TEN-framework/ten-framework)
   and Coqui TTS;
5. Streams real-time mood-based "body language" using FastAPI and WebSockets,
   with keyframe pre-fetching and decent time-to-paint;
6. Is embeddable as an iframe or React component.

## Hardware requirements

moodsprite is designed with local operation in mind; my development server
is a 24 GB VRAM gaming-level NVIDA graphics card.


# Use of cookies

moodsprite requires cookies to maintain memory per user.


# Getting started

moodsprites are currently totally hand-spun and the process is completely custom.

See `sera/` for a working example.

Talk to Sera here: `https://moodsprite.dev`.

