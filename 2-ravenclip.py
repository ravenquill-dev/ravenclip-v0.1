#!/usr/bin/env python3
"""RavenClip V0.1 - turn one long-form video into ranked vertical clips."""
from __future__ import annotations
import argparse, json, math, re, subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

HOOKS = {
    "question": re.compile(r"\?"),
    "numbers": re.compile(r"\b\d+(?:\.\d+)?%?\b"),
    "contrast": re.compile(r"\b(but|however|instead|actually|yet|surprisingly)\b", re.I),
    "insight": re.compile(r"\b(secret|lesson|reason|mistake|best|worst|important|key|how|why)\b", re.I),
}

@dataclass
class Segment:
    start: float
    end: float
    text: str

@dataclass
class Candidate:
    start: float
    end: float
    score: float
    text: str
    reasons: list[str]


def media_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ], text=True).strip()
    return float(out)


def transcribe(path: Path, model: str) -> list[Segment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("Install transcription support: pip install -r requirements.txt") from exc
    engine = WhisperModel(model, device="cpu", compute_type="int8")
    parts, _ = engine.transcribe(str(path), vad_filter=True, word_timestamps=False)
    return [Segment(float(p.start), float(p.end), p.text.strip()) for p in parts if p.text.strip()]


def load_transcript(path: Path) -> list[Segment]:
    raw = json.loads(path.read_text())
    return [Segment(float(x["start"]), float(x["end"]), x["text"].strip()) for x in raw]


def score_window(items: list[Segment], start: float, end: float) -> Candidate:
    picked = [s for s in items if s.end > start and s.start < end]
    text = " ".join(s.text for s in picked).strip()
    words = re.findall(r"[\w'-]+", text)
    duration = max(1.0, end - start)
    wpm = len(words) * 60 / duration
    reasons, score = [], 0.0
    for label, rx in HOOKS.items():
        hits = len(rx.findall(text))
        if hits:
            score += min(hits, 3) * (1.4 if label in {"question", "insight"} else 1.0)
            reasons.append(f"{label} hook ({hits})")
    if 105 <= wpm <= 205:
        score += 2.0
        reasons.append(f"clear speaking pace ({wpm:.0f} wpm)")
    if len(words) >= 55:
        score += 1.0
        reasons.append("self-contained amount of context")
    if text and text[-1] in ".!?":
        score += 0.8
        reasons.append("clean sentence ending")
    if picked and picked[0].text and picked[0].text[0].isupper():
        score += 0.4
    return Candidate(round(start, 2), round(end, 2), round(score, 2), text, reasons or ["content-dense passage"])


def candidates(items: list[Segment], total: float, target: float, stride: float) -> list[Candidate]:
    if total <= target:
        return [score_window(items, 0, total)]
    starts = [x * stride for x in range(math.floor((total-target)/stride)+1)]
    return [score_window(items, s, min(total, s+target)) for s in starts]


def overlap(a: Candidate, b: Candidate) -> float:
    inter = max(0.0, min(a.end,b.end)-max(a.start,b.start))
    return inter / max(1.0, min(a.end-a.start,b.end-b.start))


def choose(ranked: Iterable[Candidate], count: int) -> list[Candidate]:
    out = []
    for item in sorted(ranked, key=lambda x: x.score, reverse=True):
        if all(overlap(item, old) < 0.35 for old in out):
            out.append(item)
        if len(out) == count:
            break
    return sorted(out, key=lambda x: x.start)


def render(src: Path, dst: Path, c: Candidate, width: int, height: int, burn_subtitles: bool) -> None:
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},fps=30"
    )
    cmd = ["ffmpeg", "-y", "-ss", str(c.start), "-to", str(c.end), "-i", str(src),
           "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank highlights and render vertical clips from one video")
    ap.add_argument("video", type=Path)
    ap.add_argument("--transcript", type=Path, help="JSON segments [{start,end,text}]; otherwise Whisper transcribes")
    ap.add_argument("--model", default="tiny.en")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--length", type=float, default=45)
    ap.add_argument("--stride", type=float, default=15)
    ap.add_argument("--format", choices=["vertical", "square", "landscape"], default="vertical")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--dry-run", action="store_true", help="rank and report without rendering clips")
    args = ap.parse_args()
    dims = {"vertical":(1080,1920), "square":(1080,1080), "landscape":(1920,1080)}[args.format]
    args.out.mkdir(parents=True, exist_ok=True)
    duration = media_duration(args.video)
    segments = load_transcript(args.transcript) if args.transcript else transcribe(args.video,args.model)
    selected = choose(candidates(segments,duration,args.length,args.stride),args.count)
    report = {"source":str(args.video),"duration":round(duration,2),"format":args.format,
              "selection_method":"transcript hooks + speech pace + context + clean endings; overlap suppression",
              "retention_data":"not provided; content-based fallback used",
              "clips":[]}
    for i,c in enumerate(selected,1):
        filename = f"clip-{i:02d}-{int(c.start):04d}s.mp4"
        if not args.dry_run:
            render(args.video,args.out/filename,c,*dims,False)
        row = asdict(c); row["file"] = filename; report["clips"].append(row)
    (args.out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__ == "__main__":
    main()
