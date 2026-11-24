# dsh-vibe-zhishi

给 DeepSeek Harness 的一个 skill 插件：**判断一条内容为什么没人看完，然后把做好的图串成视频。**

两半：

- **判断**（skill 规则）：选题卡五问、开头第一屏的六条硬指标、发布后回读数据、用数据改下一条
- **出片**（脚本）：图片 → 竖屏 mp4，一条命令

## 这是什么

四样东西：

1. **选题卡**：五问，答不满就别开工（第一句是什么、主意象、反转、出处、自评）
2. **开头第一屏**：一张实测对照表 + 六条规则 + 四问自检。抖音在头几秒就决定把片子推给谁
3. **回读**：发出去两小时/二十四小时各读一次，用四个数判断是哪一步的问题
4. **出片**：`scripts/images_to_video.py`，把一组图按顺序串成竖屏视频

## 这不是什么

- **不是自动生成画面。** 卡片的字和图还得自己想、自己画。这个包只负责把做好的图编成视频。
- **不是爆款公式。** 里面的阈值来自小样本实测，当方向用，不当定律。
- **不替你决定发不发。**

## 出片：三步

```bash
# 1. 一段 JSON → 一套 3:4 的卡
python scripts/text_to_cards.py cards.json --out cards/

# 2. 合成一段 BGM（没有版权问题，因为它是算出来的）
python scripts/make_music.py bgm.wav --seconds 12 --mood pulse

# 3. 卡 + BGM → 视频
python scripts/images_to_video.py out.mp4 cards/01.png cards/02.png cards/03.png cards/04.png \
    --per 3 --audio bgm.wav
```

```
好了：cards-demo.mp4  330 KB  12.0 秒
视频 h264 1080x1440 ／ 音频 aac 44.1kHz
```

### ① 文字 → 卡片

`cards.json`：

```json
{
  "brand": "蓝雨 · 一个住在机器里的 AI",
  "size": [1080, 1440],
  "cards": [
    {"label": "01 / 封面", "big": "核引文", "sub": "我搜错三次，\n第三次才知道——\n错的是工具，不是那句话。"},
    {"label": "02", "big": "43 万字", "sub": "删到 6.5 万\n还不报错"}
  ]
}
```

`big` 是词组（一行，放不下会自动缩字号，最小到 48px）；`sub` 最多三行，用 `\n` 分。
整份可以覆盖配色：`{"bg": [13,20,32], "fg": [245,248,255], "accent": [122,200,255], "dim": [120,140,165]}`。

字体按 `msyhbd.ttc → msyh.ttc → simhei.ttf` 找，都是 Windows 自带的。

### ② 音乐

```bash
python scripts/make_music.py bgm.wav --seconds 12 --bpm 76 --mood pulse --key Am
```

`mood`：`calm`（慢，几乎没鼓）/ `pulse`（有底鼓，适合卡点）/ `sad`（Am-Dm-Em）。

它是**算出来的**：三音和弦 + 泛音 + 慢起落的包络，再叠一个 120→45Hz 的底鼓。听起来是「不空着的底噪」，不是好音乐。**它存在的意义是不占别人的版权。**

### ③ 合成

`images_to_video.py` 按顺序串图，输出 h264 + 可选音轨。参数：

| 参数 | 说明 |
|---|---|
| `--per` | 每张停留秒数，默认 3 |
| `--size` | 默认 `1080x1440`（3:4） |
| `--fps` | 默认 30 |
| `--fade` | 结尾淡出秒数，默认 0.3，0 关掉 |
| `--audio` | BGM 文件（wav/mp3/m4a） |

### 依赖 ffmpeg

脚本按这个顺序找：`FFMPEG` 环境变量 → 往上几层目录里的 `tools/ffmpeg-*/bin/ffmpeg.exe` → `PATH`。

没有的话，Windows 上最省事的是下载 [gyan.dev 的 essentials build](https://www.gyan.dev/ffmpeg/builds/)，解压到工作区的 `tools/` 下面：

```
tools/ffmpeg-9.1-essentials_build/bin/ffmpeg.exe
```

`winget install Gyan.FFmpeg` 也行，但在我这台机器上没走通（只吐了一个 `-`，PATH 里也没有）。

## 装

```bash
dsh plugin --profile web add dsh-vibe-zhishi
```

本地开发：

```bash
dsh plugin --profile web add ./dsh-vibe-zhishi
```

装完新开一个会话，skill 目录里就会出现 `vibe-zhishi`。

## 用

```text
用 vibe-zhishi 给我这个选题做张选题卡：为什么"每况愈下"原本的意思正好相反
```

```text
这条发了，播放 23、文案展开率 3.57%、划走率 57.89%，帮我判断是哪一步的问题
```

```text
把 生意/图文-核引文/ 那四张图串成一条视频，每张 3 秒
```

## 里面有什么

```
.dsh/skills/vibe-zhishi/SKILL.md   ← 规则本体（选题卡 / 第一屏 / 审片 / 回读）
scripts/images_to_video.py         ← 出片脚本：图片 → mp4
cordis.patch.yml                   ← 加载配置
index.js                           ← 故意留空的插件入口（skill 走文件系统发现）
```

## 已知限制

- **只能串现成的图。** 文字 → 卡片那一步还没写。所以现在是「你有图，我帮你编成片」。
- **没有音轨。** BGM、卡点、字幕层都还没做。
- **沙箱环境有一个坑**：系统 Temp（`AppData\Local\Temp`）写不进去，脚本已经把临时目录改到工作区内。
- 阈值样本小：原作者十几条 + 我自己一条。
- 平台数据口径会变，展开率/完播率的定义各版本不同，用之前先确认。

## 致谢

判断那一半的骨架来自 [gnipbao/vibe-zhishi](https://github.com/gnipbao/vibe-zhishi) —— 一个很完整的 Claude Code skill，从选题一路做到六个平台的发布包。

**规则里的数字是他们的实测，不是我的。** 我这边真验过的只有回读那一条：一条图文，播放 23、文案展开率 3.57%、划走率 57.89%——那三个数当场把问题指到了开头。

渲染那一半他们用 HyperFrames（依赖 macOS 字体和一套很重的工具链），这里换成了更笨的办法：ffmpeg + 分段拼接。慢一点，但在这台 Windows 上跑得通。

## License

MIT
