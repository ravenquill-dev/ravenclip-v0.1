# RavenClip V0.1

A small, runnable video-clipping agent prototype. It accepts one long-form video, creates a saved brief from its transcript, scores genuine highlight candidates, removes overlapping picks, renders platform-ready clips, and writes a JSON rationale report.

## What this V0.1 proves

- One unattended command goes from source video to finished clips plus report.
- Highlight choice is content-based, not arbitrary timestamps: questions, numbers, contrast, insight language, speaking pace, context, and sentence endings all affect ranking.
- YouTube retention/rewatch data is treated as an optional signal. If it is unavailable, the report explicitly records the content-based fallback instead of pretending analytics were used.
- Destination presets: vertical 9:16, square 1:1, and landscape 16:9.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe`
- Optional automatic transcription: `pip install -r requirements.txt`

## Run

With automatic local transcription:

```bash
python ravenclip.py input.mp4 --count 3 --length 45 --format vertical --out output
```

For a deterministic/test run, provide timestamped transcript segments:

```bash
python ravenclip.py input.mp4 --transcript transcript.json --count 2 --length 30 --out output
```

Transcript shape:

```json
[
  {"start": 0, "end": 8, "text": "Why do most product launches fail?"},
  {"start": 8, "end": 22, "text": "The key mistake is starting with features instead of a painful customer problem."}
]
```

The output folder contains MP4 clips and `report.json`, including each candidate's timestamps, score, transcript, and reasons.

## Selection logic

The transcript is evaluated in sliding windows. Each window gains points for:

- a question or strong hook;
- numbers or specific claims;
- contrast language;
- insight language such as "reason", "mistake", "how", or "why";
- a clear speaking pace;
- enough context to stand alone;
- a clean sentence ending.

The top candidates are selected with overlap suppression. This is intentionally transparent and easy to tune. A production version can add real YouTube retention/rewatch curves as another score term when the creator authorizes analytics access.

## Test

```bash
bash sample/make_sample.sh
python ravenclip.py sample/sample.mp4 --transcript sample/transcript.json --count 2 --length 24 --stride 8 --out sample/output
python -m unittest discover -s tests -v
```

## Known limits

- The V0.1 uses center crop for destination formatting; subject-aware tracking is a production upgrade.
- Automatic transcription requires downloading a Whisper model on first run.
- It does not fabricate retention analytics. When none are provided, it uses content signals and says so.
- Clip-worthiness is subjective, so the report keeps the scoring reasons visible for review.
