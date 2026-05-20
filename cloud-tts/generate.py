#!/usr/bin/env python3
"""
Generate an audiobook MP3 from a text file using Chatterbox TTS with a
reference voice clip.

Usage:
    python generate.py INPUT.txt --reference REF.wav --output OUT.mp3
    python generate.py INPUT.txt --reference REF.wav --output OUT.mp3 --max-chunk 280

Long inputs are split on paragraph/sentence boundaries; each chunk is
generated separately and concatenated with a short silence buffer.
The final WAV is encoded to MP3 with ffmpeg (libmp3lame, 96 kbps mono).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS


def split_into_chunks(text, max_chars=280):
    """Split on paragraphs first; if a paragraph is too long, split on sentences."""
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Text file to narrate")
    ap.add_argument("--reference", required=True, help="Reference voice WAV (15-30s, mono)")
    ap.add_argument("--output", required=True, help="Output MP3 path")
    ap.add_argument("--max-chunk", type=int, default=280, help="Max characters per generation")
    ap.add_argument("--gap-ms", type=int, default=350, help="Silence between paragraphs (ms)")
    ap.add_argument("--exaggeration", type=float, default=0.5, help="Chatterbox exaggeration (0-1)")
    ap.add_argument("--cfg-weight", type=float, default=0.5, help="Chatterbox cfg_weight (0-1)")
    args = ap.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    chunks = split_into_chunks(text, args.max_chunk)
    print(f"Input: {args.input} ({len(text)} chars, {len(chunks)} chunks)")
    print(f"Reference: {args.reference}")
    print(f"Output: {args.output}")

    print("Loading Chatterbox...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    gap = torch.zeros(1, int(sr * args.gap_ms / 1000))

    pieces = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  [{i}/{len(chunks)}] {chunk[:70]!r}{'...' if len(chunk) > 70 else ''}")
        wav = model.generate(
            chunk,
            audio_prompt_path=args.reference,
            exaggeration=args.exaggeration,
            cfg_weight=args.cfg_weight,
        )
        if wav.dim() == 1:
            wav = wav.unsqueeze(0)
        pieces.append(wav)
        if i < len(chunks):
            pieces.append(gap)

    full = torch.cat(pieces, dim=1)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_wav = tmp.name
    torchaudio.save(tmp_wav, full, sr)

    print(f"Encoding MP3 -> {args.output}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", tmp_wav,
            "-ac", "1", "-ar", "44100",
            "-c:a", "libmp3lame", "-b:a", "96k",
            args.output,
        ],
        check=True,
    )
    os.unlink(tmp_wav)

    duration_s = full.shape[1] / sr
    mins = int(duration_s // 60)
    secs = int(duration_s % 60)
    print(f"Done. {mins}:{secs:02d} of audio.")


if __name__ == "__main__":
    main()
