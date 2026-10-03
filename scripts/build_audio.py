"""Build one ~30 minute practice MP3 per theme from data/themes.json.

Each theme plays four rounds:
  1. Learn:  English x3 (with a pause to repeat after each), then Chinese once
  2. Recall: Chinese, pause to say it in English yourself, then English
  3. Learn again
  4. Recall again
  then shuffled bonus recall until the track reaches about 30 minutes

Outputs audio/<theme_id>.mp3 and audio/<theme_id>.json (timeline used by the
app to show the current sentence). Requires ffmpeg and edge-tts.

Usage:
  python scripts/build_audio.py           # real voices (needs internet)
  python scripts/build_audio.py --fake    # beeps instead of voices, for testing
"""

import argparse
import asyncio
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "themes.json"
OUT = ROOT / "audio"
CACHE = ROOT / ".tts-cache"

VOICE_EN = "en-US-AriaNeural"
VOICE_ZH = "zh-TW-HsiaoChenNeural"
RATE = 24000
TARGET_SECS = 30 * 60

ROUNDS = [
    ("learn", "第一輪，跟著唸。"),
    ("recall", "第二輪，聽中文，說英文。"),
    ("learn", "第三輪，再跟著唸一次。"),
    ("recall", "最後一輪，聽中文，說英文。"),
]


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return float(out.strip())


async def tts(text, voice, dest):
    import edge_tts

    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, voice).save(str(dest))
            if dest.stat().st_size > 0:
                return
        except Exception:
            if attempt == 3:
                raise
        await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"TTS produced no audio for: {text}")


def clip(text, voice, fake):
    """Return a cached mono WAV for this text and its duration in seconds."""
    key = hashlib.sha1(f"{voice}|{text}|{fake}".encode()).hexdigest()[:16]
    wav = CACHE / f"{key}.wav"
    if not wav.exists():
        CACHE.mkdir(exist_ok=True)
        if fake:
            secs = max(0.6, len(text) * (0.06 if voice == VOICE_EN else 0.2))
            freq = 660 if voice == VOICE_EN else 440
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={secs}",
                 "-ar", str(RATE), "-ac", "1", str(wav)])
        else:
            mp3 = CACHE / f"{key}.mp3"
            asyncio.run(tts(text, voice, mp3))
            run(["ffmpeg", "-y", "-i", str(mp3), "-ar", str(RATE), "-ac", "1", str(wav)])
            mp3.unlink()
    return wav, duration(wav)


def silence(secs, tmp):
    secs = round(secs, 1)
    wav = Path(tmp) / f"sil_{secs}.wav"
    if not wav.exists():
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={RATE}:cl=mono",
             "-t", str(secs), str(wav)])
    return wav, secs


def build_theme(theme, fake):
    with tempfile.TemporaryDirectory() as tmp:
        parts, timeline, t = [], [], 0.0

        def add(item):
            nonlocal t
            wav, secs = item
            parts.append(wav)
            t += secs

        add(clip(f"今天的主題：{theme['title']}。", VOICE_ZH, fake))
        add(silence(1.5, tmp))

        rounds = list(ROUNDS) + [("recall", "加強練習，順序打亂。")] * 3
        for r, (kind, intro) in enumerate(rounds):
            bonus = r >= len(ROUNDS)
            order = list(range(len(theme["sentences"])))
            if bonus:
                if t > TARGET_SECS - 60:
                    break
                random.Random(f"{theme['id']}{r}").shuffle(order)
            add(clip(intro, VOICE_ZH, fake))
            add(silence(2, tmp))
            for i in order:
                if bonus and t >= TARGET_SECS - 10:
                    break
                en, zh = theme["sentences"][i]
                timeline.append({"t": round(t, 2), "i": i, "round": r, "kind": kind})
                en_clip = clip(en, VOICE_EN, fake)
                zh_clip = clip(zh, VOICE_ZH, fake)
                if kind == "learn":
                    for _ in range(3):
                        add(en_clip)
                        add(silence(max(2.5, en_clip[1] + 1.2), tmp))
                    add(zh_clip)
                    add(silence(2, tmp))
                else:
                    add(zh_clip)
                    add(silence(max(4, en_clip[1] * 1.5 + 2), tmp))
                    add(en_clip)
                    add(silence(2.5, tmp))
            add(silence(1.5, tmp))

        add(clip("今天的練習結束，辛苦了！", VOICE_ZH, fake))

        listfile = Path(tmp) / "list.txt"
        listfile.write_text("".join(f"file '{p}'\n" for p in parts))
        mp3 = OUT / f"{theme['id']}.mp3"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
             "-ac", "1", "-b:a", "48k", str(mp3)])

    meta = {"id": theme["id"], "duration": round(t, 1), "timeline": timeline}
    (OUT / f"{theme['id']}.json").write_text(json.dumps(meta, ensure_ascii=False))
    print(f"{theme['id']}: {t / 60:.1f} min -> {mp3.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fake", action="store_true", help="use beeps instead of TTS")
    parser.add_argument("--only", help="build a single theme id")
    args = parser.parse_args()

    OUT.mkdir(exist_ok=True)
    for theme in json.loads(DATA.read_text())["themes"]:
        if args.only and theme["id"] != args.only:
            continue
        build_theme(theme, args.fake)


if __name__ == "__main__":
    main()
