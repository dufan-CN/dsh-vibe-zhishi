#!/usr/bin/env python3
"""images_to_video.py —— 把一组图片串成一条竖屏视频。

做法刻意笨：每张图先单独编成一小段，再用 concat 拼起来。
不用 filter_complex 一把梭——那条路在 ffmpeg 9 上这里跑不通
（`Could not open encoder before EOF`），而分段每步都能单独验。

用法：
    python images_to_video.py out.mp4 01.png 02.png 03.png --per 3

ffmpeg 按这个顺序找：环境变量 FFMPEG → 往上几层的 tools/ffmpeg-*/bin → PATH。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def find_ffmpeg():
    env = os.environ.get("FFMPEG")
    if env and os.path.isfile(env):
        return env
    cur = HERE
    for _ in range(4):
        hits = sorted(glob.glob(os.path.join(cur, "tools", "ffmpeg-*", "bin", "ffmpeg.exe")))
        if hits:
            return hits[-1]
        cur = os.path.dirname(cur)
    found = shutil.which("ffmpeg")
    if found:
        return found
    return None


def run(cmd, what):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{what} 失败：\n" + (r.stderr or "")[-1500:])


def build(images, out, per, size, fps, fade):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        sys.exit("找不到 ffmpeg：设环境变量 FFMPEG，或把 ffmpeg 放到 tools/ 下")
    for p in images:
        if not os.path.isfile(p):
            sys.exit(f"图片不存在：{p}")

    w, h = size.split("x")
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p"
    )

    # 临时目录必须放在工作区里：系统 Temp（AppData\Local\Temp）在沙箱下写不进去，
    # 会报 Permission denied。踩过。
    tmp = tempfile.mkdtemp(prefix=".vz-", dir=os.path.dirname(os.path.abspath(out)) or ".")
    segs = []
    n = len(images)
    try:
        for i, p in enumerate(images):
            seg = os.path.join(tmp, f"seg{i:03d}.mp4")
            cmd = [ffmpeg, "-y", "-loglevel", "error", "-loop", "1", "-t", str(per), "-i", p]
            if fade > 0 and i == n - 1:
                vf2 = vf + f",fade=t=out:st={max(0.0, per - fade):.3f}:d={fade}"
            else:
                vf2 = vf
            cmd += ["-vf", vf2, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", seg]
            run(cmd, f"第 {i+1} 张")
            segs.append(seg)

        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w", encoding="utf-8") as fh:
            for s in segs:
                fh.write("file '{}'\n".format(s.replace("\\", "/")))
        run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", lst, "-c", "copy", "-movflags", "+faststart", out], "拼接")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="输出 mp4")
    ap.add_argument("images", nargs="+", help="按顺序的图片")
    ap.add_argument("--per", type=float, default=3.0, help="每张停留秒数（默认 3）")
    ap.add_argument("--size", default="1080x1440", help="输出尺寸，默认 1080x1440（3:4）")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--fade", type=float, default=0.3, help="结尾淡出秒数，0 关掉")
    a = ap.parse_args()

    out = build(a.images, a.out, a.per, a.size, a.fps, a.fade)
    print(f"好了：{out}  {os.path.getsize(out)/1024:.0f} KB  {a.per*len(a.images):.1f} 秒")


if __name__ == "__main__":
    main()
