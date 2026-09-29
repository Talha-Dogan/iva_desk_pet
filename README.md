# İva 🤖

**İva is an open-source desk robot that takes AI out of the browser and puts it on your desk.**

I started working on İva because I was getting tired of AI assistants always being stuck inside a browser window. I wanted something I could actually keep on my desk and talk to without opening another app first.

You talk to it. It listens, answers, changes its expression, takes notes, starts timers, controls music and can use tools running on your computer.

Claude has also been part of the way I build İva. I use it while thinking through architecture, debugging firmware and backend problems, improving documentation and trying out new ideas. I still design, test and maintain the project myself, but Claude has become one of the tools I regularly work with.

İva is still a prototype, and there is a lot I want to add.

**→ See İva in action:** https://iva-web-concept.vercel.app/

---

## What is İva?

İva is built around an ESP32-S3 with a microphone, speaker and small OLED screen.

The ESP32 handles the physical side of the robot — wake word detection, audio, its face and device state.

The heavier AI work can run on another computer or server.

```text
You
 ↓
İva / ESP32-S3
 ↓
ASR → LLM → TTS
 ↓
MCP tools
 ↓
Your computer / services / devices
```

I designed it this way on purpose.

I don't want İva to depend on one AI company or one model.

The robot should stay the interface.  
The brain behind it should be replaceable.

---

## What can it do right now?

The current prototype can already:

- wake up by voice
- speak Turkish
- be interrupted while speaking
- show expressions on its OLED face
- move its mouth based on the audio being played
- take and search notes
- create persistent reminders
- manage simple tasks
- start Pomodoro sessions
- keep a small journal
- track habits and streaks
- remember project updates
- send notes through Telegram
- check the weather
- control Spotify
- open websites and applications on the computer
- search the web
- play simple voice games
- use MCP tools running on the computer

For example:

```text
"Jarvis"

"Take a note: the project deadline has been moved to Friday."

"I'm going to focus for 25 minutes."

"Open my focus playlist on Spotify."

"I worked for two hours today, add it to my habit tracker."

"Open Google."
```

And yes, it has a face.

Sometimes that's the most important part.

---

## Why build this?

Most AI assistants still live inside a tab.

You open a browser, find the right service, type something, switch applications and repeat the same process again later.

I wanted to try something different:

> What if the AI was simply sitting on your desk?

Something you could talk to without reaching for your phone or opening another window.

Long term, I want İva to connect more of the digital and physical things around me.

For example:

- control Home Assistant devices
- change the lights when I start working
- start a focus playlist
- start a Pomodoro at the same time
- tell me when a server or deployment fails
- notify me about developer tools
- warn me when an AI service is getting close to a usage or quota limit

Most of those integrations are not implemented yet.

That's the direction I want to take the project.

---

## Architecture

There are currently three main parts.

- 1. The robot

```text
firmware/
```

This is the ESP32-S3 side.

It handles things like:

- microphone and speaker
- wake word detection
- OLED face
- expressions
- listening and talking states
- sleep mode
- audio playback

---

- 2. The AI server

```text
server/
```

This handles the voice pipeline.

```text
speech
  ↓
ASR
  ↓
LLM
  ↓
TTS
  ↓
İva
```

There is also a self-hosted setup using Docker.

Right now I'm experimenting with Groq Whisper and Turkish Edge TTS, but I want this layer to stay replaceable.

The idea is simple: if I want to change the model, speech service or TTS provider later, I shouldn't have to redesign the robot.

---

- 3. The bridge

```text
bridge/
```

The bridge is what connects the AI to tools running on the computer.

Instead of teaching the ESP32 how to do everything directly, İva can ask the computer to perform an action through MCP.

Right now the bridge contains 27+ tools around things like:

- notes
- tasks
- reminders
- Pomodoro
- journal
- habits
- project memory
- Telegram
- weather
- Spotify
- browser and PC interaction
- small utilities and games

This has turned out to be one of the parts I like most about the project.

If I want to give İva a new ability, I usually don't need to rebuild the firmware. I can add another tool to the bridge and let the AI use it.

---

## Hardware

My current prototype uses:

| Part | Model |
|---|---|
| Board | ESP32-S3 Zero |
| Microphone | INMP441 |
| Amplifier | MAX98357A |
| Screen | SSD1306 OLED 128×64 |

Current pin mapping:

| Part | GPIO |
|---|---|
| INMP441 SD | 6 |
| INMP441 WS | 7 |
| INMP441 SCK | 8 |
| MAX98357 DIN | 12 |
| MAX98357 BCLK | 11 |
| MAX98357 LRC | 10 |
| OLED SDA | 4 |
| OLED SCL | 3 |
| RGB LED | 21 |

The board I'm using right now is a 4 MB ESP32-S3 Zero.

It's been enough for the prototype so far, but I'm already starting to run into its limits. I'll probably move to a board with more flash once I start adding more to the firmware.

---

## Running it

Clone the repository:

```bash
git clone https://github.com/Talha-Dogan/iva_desk_pet.git
cd iva_desk_pet
```

On Windows:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

I made a small setup script so I wouldn't have to repeat the same installation steps every time I set İva up on a new machine.

It creates the Python environment, installs the dependencies, prepares the `.env` file and gets the bridge ready to run.

Then configure:

```text
bridge/.env
```

There are more detailed notes in:

```text
docs/kurulum.md
docs/donanim.md
docs/mimari.md
firmware/README.md
bridge/README.md
server/README.md
```

---

## Repository structure

```text
iva_desk_pet/
├── firmware/   ESP32 changes, face and hardware code
├── bridge/     MCP tools and desktop integrations
├── server/     self-hosted voice / AI server
├── scripts/    setup and helper scripts
└── docs/       hardware and architecture notes
```

I don't keep the entire upstream firmware tree in this repository.

The original firmware tree is large, and most of it isn't something I changed. I prefer keeping this repository focused on the parts I've actually written, modified or documented for İva.

That makes it much easier for me to understand what belongs to this project and what comes from upstream.

---

## What's next?

Things I'd like to work on next:

- [ ] Home Assistant support
- [ ] AI/API quota notifications
- [ ] server and deployment notifications
- [ ] better music workflows
- [ ] meeting and lecture summaries
- [ ] more MCP tools
- [ ] custom "İva" wake word
- [ ] 16 MB ESP32-S3 version
- [ ] 3D printable enclosure
- [ ] easier Linux/macOS setup
- [ ] more AI provider options

One thing I specifically want to experiment with is making İva react to events instead of only waiting for me to speak first.

For example, I want it to eventually be able to say:

> "You're getting close to your Claude usage limit."

or:

> "The deployment failed."

without me opening another dashboard first.

I think that's where a physical assistant starts becoming more interesting than a normal chatbot.

---

## Build your own

İva is not meant to be a closed product.

If you want to build one, modify it, give it a different face, connect another model or write your own MCP tools, that's exactly the kind of thing I'd like people to do with the project.

You should be able to change the parts you don't like and replace the parts that don't make sense for your setup.

Issues and pull requests are welcome.

If you build your own version, I'd genuinely like to see it. :)

---

## Demo

There is an interactive web version of the current concept here:

### https://iva-web-concept.vercel.app/

You can rotate the model, look at the current product concept and try the browser simulation of İva's screen.

The physical project is still under development, so the site changes as the prototype changes.

---

## Open-source projects behind İva

İva also depends on a few open-source projects that saved me from having to build everything from scratch.

- [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) — this is where the base ESP32 firmware comes from. I built İva's hardware behavior and changes on top of it.
- [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) — I used this as the starting point for the self-hosted server side.
- [TechTalkies/Face-for-Xiaozhi](https://github.com/TechTalkies/Face-for-Xiaozhi) — this helped inspire some of the early ideas around the face system.

The face also takes some design inspiration from expressive robots like Anki Cozmo and Vector.

I've changed and added quite a bit around these projects, but they're an important part of what İva is built on.

İva is released under the MIT License.

---

İva currently lives on my desk.

Hopefully someone builds one for theirs too. 🤖
