İva 

İva is an open-source desk robot that takes AI out of the browser and puts it on your desk.

I started building İva because I wanted an AI assistant that felt less like another app and more like something that actually lived in the room with me.

You talk to it. It listens, answers, changes its expression, takes notes, starts timers, controls music and can use tools running on your computer.

İva is being developed with the help of AI tools as well. Claude has been part of the development process, especially while working through architecture decisions, firmware and backend problems, debugging, documentation, and new feature ideas. I still design, test and maintain the project myself, but Claude has become one of the tools I use while building it.

It is still a prototype, and there is a lot I want to add.

→ See İva in action: https://iva-web-concept.vercel.app/
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

That separation is intentional.

I don't want İva to be tied to one AI company or one model.

The robot should be the interface.  
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

"Not al: proje teslimi cumaya çekildi."

"25 dakika odaklanacağım."

"Spotify'da çalışma listemi aç."

"Bugün iki saat çalıştım, alışkanlığa ekle."

"Google'ı aç."
```

And yes, it has a face.

Sometimes that's the most important feature.

---

## Why build this?

Most AI assistants still live inside a tab.

You open a browser, find the right service, type something, switch applications and repeat the same process again later.

I wanted to experiment with a different idea:

> What if the AI was simply sitting on your desk?

Something you could talk to without reaching for your phone.

Eventually I want İva to be able to connect the different parts of my digital and physical environment.

For example:

- control Home Assistant devices
- change the lights when I start working
- start a focus playlist
- start a Pomodoro at the same time
- tell me when a server or deployment fails
- notify me about developer tools
- warn me when an AI service is approaching a usage or quota limit

Most of those integrations are not implemented yet.

That's where I want to take the project.

---

## Architecture

There are currently three main pieces.

### 1. The robot

```text
firmware/
```

Runs on the ESP32-S3.

It handles things like:

- microphone and speaker
- wake word
- OLED face
- expressions
- listening / talking states
- sleep mode
- audio playback

---

### 2. The AI server

```text
server/
```

Handles the voice pipeline.

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

I'm currently experimenting with Groq Whisper and Turkish Edge TTS, but the idea is to keep this layer replaceable.

---

### 3. The bridge

```text
bridge/
```

This is probably my favorite part of the project.

The bridge exposes tools to the AI using MCP.

Instead of teaching the ESP32 how to do everything, the robot can ask the computer to perform an action.

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
- browser / PC interaction
- small utilities and games

Adding a new ability usually means adding another tool here rather than rebuilding the entire device.

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

I'm using a 4 MB ESP32-S3 Zero at the moment.

It works, but I'm planning to move to a board with more flash as the firmware grows.

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

The setup script installs the Python dependencies, prepares the environment file and sets up the bridge.

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

The goal is to keep the parts I've written or changed readable instead of committing roughly a gigabyte of unrelated firmware source.

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

One thing I specifically want to explore is letting İva react to events instead of only waiting for commands.

For example, I want it to eventually be able to say:

> "Claude kullanım limitin azalıyor."

or:

> "Deployment başarısız oldu."

without me checking another dashboard first.

---

## Build your own

İva is not meant to be a closed product.

If you want to build one, modify it, give it a different face, connect another model or write your own MCP tools, that's exactly the kind of thing I'd like to see people do with the project.

Issues and pull requests are welcome.

If you build your own version, please show me. :)

---

## Demo

There is an interactive web version of the current concept here:

### https://iva-web-concept.vercel.app/

You can rotate the model, look at the current product concept and try the browser simulation of İva's screen.

The physical project is still under development, so the site changes along with the prototype.

---

## Open-source projects behind İva

İva wouldn't exist without a few other open-source projects.

It currently builds on or takes inspiration from:

- [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32) — base ESP32 firmware
- [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server) — self-hosted server foundation
- [TechTalkies/Face-for-Xiaozhi](https://github.com/TechTalkies/Face-for-Xiaozhi) — early inspiration for the face system

The face also takes some design inspiration from robots such as Anki Cozmo and Vector.

İva is released under the MIT License.

---

İva currently lives on my desk.

Hopefully someone builds one for theirs too. 🤖
