# Conversational Video MVP — Architecture (Task 11, v0.5+ build target)

This document captures the architecture for the conversational-video pipeline.
Building the actual MVP requires a GPU-backed inference endpoint + a WebRTC
peer + a browser client — none of which we ship in v0.4. What we DO ship:
this doc, plus the contract (`Capability.LIP_SYNC` already exists, plus a
new conversational-session capability slot we reserve here).

## Why we want it

Synthesia 3.0's "Video Agents" — real-time two-way conversational video —
is the 2026 wow feature no open-source has touched. Even a basic version
wins us the headline demo.

## The end-to-end loop (what the user sees)

```
1. User opens the live URL (cuts.dreytools.com/converse).
2. Browser asks for mic + (optional) camera.
3. User speaks: "What's the weather in St. Pete today?"
4. WebRTC peer streams audio to our server.
5. Server runs WhisperX → text in 200ms.
6. LLM answers in 600ms (Claude Haiku 4.5 stream).
7. Kokoro TTS synthesizes the voiceover in 300ms.
8. Wan 2.2-TI2V-5B renders a 2-3s talking-head clip in 1.5-2.5s.
9. Clip streams back over WebRTC to the browser.
10. Browser displays the avatar speaking the answer.
11. Loop on user's next utterance.
```

Total round-trip target: **3-4 seconds.** Not real-time-real-time. Real-time-ish.

## Component breakdown

### Frontend — `apps/converse-mvp/`
- Next.js 16 page at `/converse` (separate from timeline UI).
- WebRTC peer using `RTCPeerConnection`.
- Microphone capture, voice-activity detection (VAD) to chunk utterances.
- Render the streamed clip as a `<video>` element.
- Display rolling chat history (user utterances + agent replies as text).

### Signaling server — `apps/converse-server/`
- Python FastAPI + `aiortc` for WebRTC peering.
- Accepts SDP offer, answers, manages ICE candidates.
- Connection lifecycle: connect → first utterance → render loop → disconnect.

### Inference workers — `apps/converse-worker/`
- One worker per active session (Modal or RunPod backed in production).
- Pre-loaded models in GPU memory: WhisperX `large-v3`, Kokoro-82M,
  Wan 2.2-TI2V-5B, an LLM (Claude Haiku 4.5 via API or local Llama 3.3).
- Conversation state: rolling 4-utterance history for LLM context.
- Character anchor: the avatar uses the same source image (and Higgsfield
  `character_id` if keyed) for every clip in the session.

### Pipeline manifest — `agentic_cuts/pipelines/conversational.yaml`
A new pipeline conformant to the existing schema. Stages:

```
ingest_utterance     (microphone audio chunk + VAD)
transcribe_utterance (WhisperX)
respond              (LLM, chat-completion with rolling context)
synthesize_voice     (Kokoro TTS, fast voice)
render_clip          (Wan 2.2-TI2V-5B, image-to-video, 2-3s)
stream_back          (WebRTC send)
```

Every stage runs per-utterance. State persists in a session-scoped
`Checkpoint`. A 5-minute idle timer kills the session and frees GPU memory.

## Latency budget (target 3.5s round-trip)

| Stage | Budget | How we hit it |
|---|---:|---|
| transcribe_utterance | 200ms | WhisperX on a warm GPU, batch_size 1 |
| respond | 600ms | Haiku streams; we cut at first sentence |
| synthesize_voice | 300ms | Kokoro is sub-300ms by default |
| render_clip | 1.8s | Wan 2.2-TI2V-5B 24fps × 2.5s on 4090 |
| network round-trip | 600ms | WebRTC over UDP, regional servers |

If we miss budget by >500ms two utterances in a row, drop the avatar render
and stream voice-only with a static portrait. User notices but session keeps
flowing.

## Cost reality

Per session minute: roughly $0.04 GPU + $0.005 LLM = **$0.045/min** on
Modal/RunPod with a warm L4 GPU. A 5-minute conversation costs ~$0.25.
Higgsfield Speak v2 path costs more (1.50/clip × ~10 clips = $15) but wins
on lip-sync quality if the user has burned credits.

## Why this is the wedge

Three closed tools own conversational video right now: **Synthesia 3.0,
HeyGen Interactive, D-ID Real-Time.** None are open-source. Even a v0.5
basic version of this MVP gives Drey:

- A demo that nobody else can ship at the open-source HN-level.
- A real product wedge for client/agency upsell ("your private avatar that
  answers your students' questions in real-time").
- Distribution muscle — a conversational landing on cuts.dreytools.com is
  the kind of thing that gets posted to X 200 times in 24 hours.

## What v0.5 ships

The minimum path to a working demo:
1. Single-page browser client at `cuts.dreytools.com/converse`.
2. One Modal-deployed worker pre-loaded with Kokoro + Wan + Whisper.
3. Python signaling server on Fly.io or Modal.
4. Hard 5-min session cap, 3 concurrent sessions max.
5. Drey's face as the only avatar (start with one, expand to brand-kit-driven later).

What v0.5 explicitly does NOT ship:
- Multi-avatar.
- Voice clone (uses Kokoro default voices).
- Streaming partial-utterance interruption (full-utterance only).
- Persistent sessions (every refresh restarts).
- Authenticated sessions (open URL until DDOS protection is in place).

## Risk register

| Risk | Mitigation |
|---|---|
| GPU cold start blows the latency budget | Keep one worker warm per region; pre-warm before user clicks "start." |
| WebRTC NAT traversal fails | TURN server fallback (Twilio or Cloudflare TURN). |
| Wan 2.2-TI2V-5B occasionally renders garbage frames | Detect via post-render frame variance check; re-render with seed+1, fall back to static avatar. |
| Cost runaway | Budget cap per IP per day (CostTracker pattern from main engine, persisted to Redis). |
| Liability of putting words in someone's mouth | Disclaimer on the page; no celebrity / public-figure avatars without consent. |

---

**Next step:** in v0.5 we build `apps/converse-mvp/` from this doc. v0.4
ships the doc + the architecture wedge claim. Drey can post the doc itself
on launch — the architecture is the marketing.
