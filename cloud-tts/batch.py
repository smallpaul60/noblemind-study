#!/usr/bin/env python3
"""
Batch-generate MP3s from a folder of .txt files using Chatterbox TTS.
Loads the model ONCE and processes every file, saving the per-chapter
model-load overhead our shell loop pays.

Usage:
    python batch.py INPUT_DIR --reference REF.wav --out-dir OUT_DIR
    python batch.py file1.txt file2.txt --reference REF.wav --out-dir OUT_DIR
    python batch.py *.txt --reference REF.wav --out-dir OUT_DIR --rename strip-suffix

Output filenames match input stems by default:
    chapter-01.txt   ->  chapter-01.mp3
    dedication.txt   ->  dedication.mp3

With --rename strip-suffix, "*-AUDIO" gets removed:
    FromTheBeginning_Ch1-AUDIO.txt  ->  FromTheBeginning_Ch1.mp3

Skips files where the output MP3 already exists (resume-friendly).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS


def split_into_chunks(text, max_chars=280):
    """Same chunker as generate.py — paragraph then sentence boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    for para in paragraphs:
        if len(para) <= max_chars:
            chunks.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        buf = ""
        for s in sentences:
            if len(buf) + len(s) + 1 <= max_chars:
                buf = (buf + " " + s).strip()
            else:
                if buf:
                    chunks.append(buf)
                if len(s) <= max_chars:
                    buf = s
                else:
                    for i in range(0, len(s), max_chars):
                        chunks.append(s[i : i + max_chars])
                    buf = ""
        if buf:
            chunks.append(buf)
    return chunks


def output_name(input_path, rename_mode):
    stem = input_path.stem
    if rename_mode == "strip-suffix":
        stem = re.sub(r"-AUDIO$", "", stem)
    return f"{stem}.mp3"


def expand_inputs(args_inputs):
    """Accept files, dirs, or a mix. Dirs expand to *.txt inside."""
    paths = []
    for p in args_inputs:
        path = Path(p)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.txt")))
        elif path.is_file():
            paths.append(path)
        else:
            print(f"Warning: {p} not found, skipping", file=sys.stderr)
    return paths


def generate_one(model, text, reference, gap_ms, exaggeration, cfg_weight):
    chunks = split_into_chunks(text)
    sr = model.sr
    gap = torch.zeros(1, int(sr * gap_ms / 1000))
    pieces = []
    for i, chunk in enumerate(chunks, 1):
        print(f"    [{i}/{len(chunks)}] {chunk[:60]!r}{'...' if len(chunk) > 60 else ''}")
        wav = model.generate(
            chunk,
            audio_prompt_path=reference,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )
        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        pieces.append(wav)
        if i < len(chunks):
            pieces.append(gap)
    return torch.cat(pieces, dim=1), sr


def encode_mp3(wav, sr, out_path):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = tmp.name
    torchaudio.save(tmp_wav, wav, sr)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", tmp_wav,
            "-ac", "1", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "96k",
            str(out_path),
        ],
        check=True,
    )
    os.unlink(tmp_wav)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="Text files or a directory")
    ap.add_argument("--reference", required=True, help="Reference voice WAV")
    ap.add_argument("--out-dir", required=True, help="Output directory for MP3s")
    ap.add_argument("--rename", choices=["none", "strip-suffix"], default="none",
                    help="strip-suffix removes trailing -AUDIO from output names")
    ap.add_argument("--max-chunk", type=int, default=280)
    ap.add_argument("--gap-ms", type=int, default=350)
    ap.add_argument("--exaggeration", type=float, default=0.5)
    ap.add_argument("--cfg-weight", type=float, default=0.5)
    args = ap.parse_args()

    inputs = expand_inputs(args.inputs)
    if not inputs:
        print("No input files found.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    todo = []
    skipped = []
    for p in inputs:
        out_path = out_dir / output_name(p, args.rename)
        if out_path.exists():
            skipped.append(p.name)
        else:
            todo.append((p, out_path))

    print(f"Reference: {args.reference}")
    print(f"Output dir: {out_dir}")
    print(f"To generate: {len(todo)}")
    if skipped:
        print(f"Skipping (already done): {len(skipped)} -> {', '.join(skipped)}")
    if not todo:
        print("Nothing to do.")
        return

    print("\nLoading Chatterbox (one-time)...")
    t0 = time.time()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)
    print(f"  loaded in {time.time() - t0:.1f}s on {device}")

    overall_t0 = time.time()
    for idx, (in_path, out_path) in enumerate(todo, 1):
        print(f"\n[{idx}/{len(todo)}] {in_path.name} -> {out_path.name}")
        text = in_path.read_text(encoding="utf-8")
        t = time.time()
        wav, sr = generate_one(
            model, text,
            reference=args.reference,
            gap_ms=args.gap_ms,
            exaggeration=args.exaggeration,
            cfg_weight=args.cfg_weight,
        )
        encode_mp3(wav, sr, out_path)
        dur = wav.shape[1] / sr
        print(f"  -> {dur/60:.1f} min audio, {time.time() - t:.1f}s wall")

    total = time.time() - overall_t0
    print(f"\nAll done. {len(todo)} files in {total/60:.1f} min ({total/len(todo):.0f}s avg).")


if __name__ == "__main__":
    main()
