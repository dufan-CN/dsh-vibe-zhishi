#!/usr/bin/env python3
"""make_music.py —— 用 numpy 合成一段 BGM。没有版权问题，因为它是算出来的。

不是「好看的音乐」，是「不空着的底噪」：几组和弦垫着，加一个很轻的底鼓，
音量压低到说话能盖过去。视频里的人声/字幕才是主角。

用法：
    python make_music.py bgm.wav --seconds 12
    python make_music.py bgm.wav --seconds 12 --bpm 80 --key Am --mood calm

mood:
    calm   —— 慢，长音，几乎没有鼓
    pulse  —— 有节拍，适合卡点
"""
import argparse
import wave

import numpy as np

SR = 44100

# 和弦（三音）
CHORDS = {
    "Am": [220.00, 261.63, 329.63],
    "F":  [174.61, 220.00, 261.63],
    "C":  [261.63, 329.63, 392.00],
    "G":  [196.00, 246.94, 293.66],
    "Dm": [146.83, 174.61, 220.00],
    "Em": [164.81, 196.00, 246.94],
}

PROGRESSIONS = {
    "calm":  ["Am", "F", "C", "G"],
    "pulse": ["Am", "F", "C", "G"],
    "sad":   ["Am", "Dm", "Em", "Am"],
}


def tone(freq, dur, amp=0.22, attack=0.35, release=0.6, detune=0.15):
    """一个音：正弦 + 两个泛音 + 轻微失谐，起落很慢，像垫子。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    w = (
        np.sin(2 * np.pi * freq * t) * 0.60
        + np.sin(2 * np.pi * freq * 2 * t) * 0.20
        + np.sin(2 * np.pi * freq * 3 * t) * 0.08
        + np.sin(2 * np.pi * (freq * (1 + detune / 1000)) * t) * 0.12
    )
    env = np.ones(n, dtype=np.float64)
    a = min(int(attack * SR), n // 2)
    r = min(int(release * SR), n // 2)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if r > 0:
        env[-r:] = np.linspace(1, 0, r)
    return w * env * amp


def kick(dur=0.18, amp=0.35):
    """底鼓：频率从 120Hz 迅速掉到 45Hz，短促。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.linspace(120, 45, n)
    phase = 2 * np.pi * np.cumsum(f) / SR
    env = np.exp(-t * 18)
    return np.sin(phase) * env * amp


def build(seconds, bpm, mood, key):
    prog = PROGRESSIONS.get(mood, PROGRESSIONS["calm"])
    if key in CHORDS:
        prog = [key] + prog[1:]

    beat = 60.0 / bpm
    bar = beat * 4  # 一小节四拍
    n_bars = max(1, int(np.ceil(seconds / bar)))

    total = int(n_bars * bar * SR)
    buf = np.zeros(total, dtype=np.float64)

    for i in range(n_bars):
        name = prog[i % len(prog)]
        freqs = CHORDS[name]
        start = int(i * bar * SR)
        length = int(bar * SR)
        # 三个音稍微错开起拍，听起来不那么齐整
        for j, f in enumerate(freqs):
            seg = tone(f, bar, amp=0.16)
            off = start + int(j * 0.04 * SR)
            end = min(off + len(seg), total)
            buf[off:end] += seg[: end - off]

        # 每小节一个低音根音，垫住
        root = tone(freqs[0] / 2, bar, amp=0.12, attack=0.1, release=0.8)
        end = min(start + len(root), total)
        buf[start:end] += root[: end - start]

    if mood == "pulse":
        k = kick()
        for b in range(int(seconds / beat)):
            off = int(b * beat * SR)
            end = min(off + len(k), total)
            if off < total:
                buf[off:end] += k[: end - off]

    # 截到指定长度，两端淡入淡出 0.4 秒
    want = int(seconds * SR)
    buf = buf[:want]
    fade = int(0.4 * SR)
    if len(buf) > 2 * fade:
        buf[:fade] *= np.linspace(0, 1, fade)
        buf[-fade:] *= np.linspace(1, 0, fade)

    # 归一化到 -6 dB 左右，别盖过别的声音
    peak = np.max(np.abs(buf)) or 1.0
    buf = buf / peak * 0.5
    return buf


def write_wav(path, data):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="输出 wav")
    ap.add_argument("--seconds", type=float, default=12.0)
    ap.add_argument("--bpm", type=float, default=76.0)
    ap.add_argument("--mood", default="calm", choices=list(PROGRESSIONS))
    ap.add_argument("--key", default="Am", choices=list(CHORDS))
    a = ap.parse_args()

    data = build(a.seconds, a.bpm, a.mood, a.key)
    write_wav(a.out, data)
    print(f"好了：{a.out}  {a.seconds:.1f} 秒  {a.mood}  {a.key}  {a.bpm:.0f}bpm")


if __name__ == "__main__":
    main()
