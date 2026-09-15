# RavenClip V0.1

A runnable video-clipping agent prototype. It accepts one long-form video, creates a saved brief from its transcript, scores genuine highlight candidates, removes overlapping picks, renders platform-ready clips, and writes a JSON rationale report.

## What this V0.1 proves

- One unattended command goes from source video to finished clips plus report.
- Highlight choice is content-based, not arbitrary timestamps: questions, numbers, contrast, insight language, speaking pace, context, and sentence endings affect ranking.
- YouTube retention/rewatch data is treated as optional. If unavailable, the report records the content-based fallback instead of pretending analytics were used.
- Destination presets: vertical 9:16, square 1:1, and landscape 16:9.

## Run

Install ffmpeg/ffprobe and Python 3.10+. Optional automatic transcription:

```bash
pip install -r 3-requirements.txt
python 2-ravenclip.py input.mp4 --count 3 --length 45 --format vertical --out output
```

For a deterministic test, pass timestamped transcript segments:

```bash
python 2-ravenclip.py input.mp4 --transcript transcript.json --count 2 --length 30 --out output
python 4-test_selection.py
```

Transcript shape:

```json
[{"start":0,"end":8,"text":"Why do most product launches fail?"}]
```

The output folder contains MP4 clips and `report.json`, including timestamps, scores, transcript text, and selection reasons.

## Selection logic

Sliding windows gain points for questions, concrete numbers, contrast, insight language, clear speaking pace, enough context, and a clean sentence ending. Top candidates are selected with overlap suppression. A production version can add authorized YouTube retention curves as another score term.

## Known limits

- V0.1 uses center crop; subject-aware tracking is a production upgrade.
- Automatic transcription downloads a Whisper model on first run.
- It never fabricates retention analytics.
- Clip-worthiness is subjective, so scoring reasons remain visible for review.
