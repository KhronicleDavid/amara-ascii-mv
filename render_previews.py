"""将实际终端字符帧导出为 PNG / GIF；播放程序无需安装 Pillow。"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

from amara import Film, PALETTE, ROOT, cell_width, wrap


OUTPUT = ROOT / "previews" / "v2"
MONO_PATH = Path("C:/Windows/Fonts/CascadiaMono.ttf")
CJK_PATH = Path("C:/Windows/Fonts/msyh.ttc")
BACKGROUND = (7, 11, 20)
GALLERY_SHOTS = [
    (2.2,'未知文字入侵'),(10.0,'文明执行未知输入'),
    (18.2,'十二个世界被吞没'),(22.4,'心脏被拖过行星'),
    (25.9,'语言表层剥离'),(27.8,'枪击与未知牢笼'),
    (29.9,'划入月暗'),(31.5,'切开幻想'),(33.1,'逆向声波'),
    (40.0,'即使无光，也愿存在'),(46.3,'现实与虚构争夺坐标'),
    (53.9,'判定卡顿'),(63.6,'无缝导体传回回应'),(67.7,'思考被刻入'),
    (70.8,'姓名索引被删除'),(72.8,'流星与泪掳走记忆'),
    (74.9,'玻璃心被封存'),(86.0,'脊骨神经体俯临旷野'),
    (94.3,'未来窗格逐一熄灭'),(97.7,'预测纸带遭逆向擦除'),
    (101.1,'观测光阑封闭未知'),(102.05,'巨幅 X 接管解释器'),
    (105.7,'理解链条断裂'),(114.0,'翻卷混沌加速坍缩'),
    (123.4,'异质脉冲接通'),(127.3,'机械臂献上电路花束'),
    (130.1,'巨颚吞咽星流'),(132.2,'梦毒污染电路回廊'),
    (135.2,'人形与光冠分级炸散'),(138.5,'夜沿穹顶接缝蔓延'),
    (144.9,'理解请求被拒绝'),(152.0,'文明的铭文解读失步'),
    (156.8,'电路自激烧毁'),(160.8,'全息献花沿光束崩解'),
    (168.7,'重建桥与圣堂内塌'),(172.0,'天国穹顶倒扣坠落'),
    (175.5,'未知文字占据全部权限'),(180.0,'画面坐标瓦解'),
    (187.0,'文明错误转储'),(193.0,'严重系统错误'),
]


class CharacterRenderer:
    """按 Canvas 的字符格逐字绘制；宽字占两格，空续格不重复绘制。"""

    def __init__(self, cell_w=8, cell_h=18, font_size=14):
        self.cell_w, self.cell_h = cell_w, cell_h
        self.mono = ImageFont.truetype(str(MONO_PATH), font_size)
        self.cjk = ImageFont.truetype(str(CJK_PATH), font_size)

    @lru_cache(maxsize=512)
    def glyph(self, char):
        slots = max(1, cell_width(char))
        width = self.cell_w * slots
        font = self.mono if ord(char) < 128 else self.cjk
        baseline = self.cell_h - 4
        left, top, right, bottom = font.getbbox(char, anchor="ls")
        advance = font.getlength(char)
        mask = Image.new("L", (width, self.cell_h))
        # Most glyphs fit naturally. Fit rare ambiguous-width punctuation into
        # its single allocated cell without affecting adjacent characters.
        if right - left <= width:
            x = round((width - advance) / 2)
            x = max(-left, min(x, width - right))
            ImageDraw.Draw(mask).text((x, baseline), char, font=font,
                                      fill=255, anchor="ls")
        else:
            raw = Image.new("L", (right - left, self.cell_h))
            ImageDraw.Draw(raw).text((-left, baseline), char, font=font,
                                     fill=255, anchor="ls")
            mask = raw.resize((width, self.cell_h), Image.Resampling.LANCZOS)
        return mask

    def render(self, canvas):
        result = Image.new("RGB", (canvas.w * self.cell_w,
                                  canvas.h * self.cell_h), BACKGROUND)
        for y, row in enumerate(canvas.chars):
            if canvas.backgrounds[y] is not None:
                ImageDraw.Draw(result).rectangle((0,y*self.cell_h,result.width,(y+1)*self.cell_h-1),
                                                 fill=PALETTE[canvas.backgrounds[y]])
            for x, char in enumerate(row):
                if not char or char == " ":
                    continue
                mask = self.glyph(char)
                result.paste(PALETTE[canvas.colors[y][x]],
                             (x * self.cell_w, y * self.cell_h), mask)
        return result


def stamp(t):
    return f"{int(t) // 60:02}:{t % 60:05.2f}"


def check_subtitles(film):
    """确认每条字幕在所有指定尺寸中完整出现，既不截断也不覆盖。"""
    report = []
    for width, height in [(64, 20), (80, 23), (120, 42), (160,46)]:
        max_rows = 0
        for cue in film.subtitles:
            t = (cue["start"] + cue["end"]) / 2
            canvas = film.frame(t, width, height)
            expected = wrap(cue["zh"], width - 4) + wrap(cue["en"], width - 4)
            subtitle_h = max(4, len(expected) + 2)
            first_row = height - subtitle_h
            assert first_row >= 4, (width, height, cue["ja"])
            assert first_row + len(expected) <= height - 2
            for row_index, line in enumerate(expected, first_row):
                actual = "".join(canvas.chars[row_index]).strip()
                assert actual == line, (width, height, cue["ja"], line, actual)
            assert all(cell_width("".join(row)) == width for row in canvas.chars)
            max_rows = max(max_rows, len(expected))
        report.append({"字符尺寸": f"{width} × {height}",
                       "字幕条数": len(film.subtitles),
                       "最多字幕行数": max_rows,
                       "完整显示": True})
    return report


def size_gallery(film, renderer):
    samples = [(64, 20, 18.2), (80, 23, 18.2),
               (64, 20, 70.6), (80, 23, 70.6)]
    label_font = ImageFont.truetype(str(CJK_PATH), 20)
    images = [renderer.render(film.frame(t, w, h)) for w, h, t in samples]
    panel_w, panel_h, pad = 672, 476, 20
    sheet = Image.new("RGB", (panel_w * 2 + pad * 3,
                              panel_h * 2 + pad * 3), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for i, ((w, h, t), picture) in enumerate(zip(samples, images)):
        x = pad + (i % 2) * (panel_w + pad)
        y = pad + (i // 2) * (panel_h + pad)
        draw.text((x + 8, y + 8), f"{w} × {h} 字符 · {stamp(t)}",
                  fill=PALETTE[4], font=label_font)
        sheet.paste(picture, (x + (panel_w - picture.width) // 2, y + 48))
    sheet.save(OUTPUT / "size-checks.png")


def gallery(film, renderer):
    output_paths = []
    tiles = []
    font = ImageFont.truetype(str(CJK_PATH), 20)
    for index, (t, title) in enumerate(GALLERY_SHOTS, 1):
        picture = renderer.render(film.frame(t, 160, 46))
        path = OUTPUT / f"shot-{index:02}-{t:06.2f}.png"
        picture.save(path)
        output_paths.append(path.name)
        thumbnail = picture.resize((576, 373), Image.Resampling.LANCZOS)
        tiles.append((thumbnail, f"{index:02} · {title} · {stamp(t)}"))
    pad, tile_w, tile_h = 18, 600, 419
    row_count = math.ceil(len(tiles) / 3)
    sheet = Image.new("RGB", (tile_w * 3 + pad * 4,
                              tile_h * row_count + pad * (row_count + 1)), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for i, (picture, title) in enumerate(tiles):
        x = pad + (i % 3) * (tile_w + pad)
        y = pad + (i // 3) * (tile_h + pad)
        draw.rectangle((x, y, x + tile_w, y + tile_h), outline=PALETTE[1])
        draw.text((x + 12, y + 9), title, font=font, fill=PALETTE[4])
        sheet.paste(picture, (x + 12, y + 37))
    sheet.save(OUTPUT / "contact-sheet.png")
    renderer.render(film.frame(10.5, 160, 46)).save(OUTPUT / "cover.png")
    renderer.render(film.frame(175.5, 160, 46)).save(OUTPUT / "unknown.png")
    renderer.render(film.frame(193.0, 160, 46)).save(OUTPUT / "ending.png")
    size_gallery(film, renderer)
    report = {
        "来源": "amara.Film.frame 的实际字符与颜色；未另造示意图",
        "截图尺寸": "160 × 46 字符，1280 × 828 像素",
        "镜头时间": [t for t, _ in GALLERY_SHOTS],
        "字幕检查": check_subtitles(film),
        "截图文件": output_paths,
    }
    (OUTPUT / "preview-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(f"已生成 {len(tiles)} 个实际镜头、总览、封面、未知信号与小窗口字幕检查图：{OUTPUT}")


def animated(film, renderer):
    start, end, fps = 173.218, 179.0, 12
    count = math.ceil((end - start) * fps)
    palette_image = Image.new("P", (1, 1))
    palette = [value for color in [BACKGROUND, *PALETTE] for value in color]
    palette.extend([0] * (768 - len(palette)))
    palette_image.putpalette(palette)
    frames = []
    for i in range(count):
        actual = renderer.render(film.frame(start + i / fps, 160, 46))
        frames.append(actual.quantize(palette=palette_image,
                                     dither=Image.Dither.NONE))
    # GIF has 10 ms clock ticks; carry rounding error so average playback
    # remains 12 fps rather than rounding each frame to a fixed 80 ms.
    durations = [round((i + 1) * 1000 / fps / 10) * 10
                 - round(i * 1000 / fps / 10) * 10 for i in range(count)]
    durations[-1] = round((end - start) * 1000 / 10) * 10 - sum(durations[:-1])
    frames[0].save(OUTPUT / "animated-preview.gif", save_all=True,
                   append_images=frames[1:], duration=durations,
                   loop=0, optimize=False, disposal=1)
    print(f"已生成 {start}–{end} 秒、12 fps 的实际画面动图（无音频）。")


def semantic_montage(film,renderer):
    segments=[(16.635,20.819),(69.798,71.682),(124.777,128.428),
              (133.114,136.774),(173.218,176.3),(190.0,193.0)]
    fps=12
    palette_image=Image.new('P',(1,1))
    palette=[value for color in [BACKGROUND,*PALETTE] for value in color]
    palette.extend([0]*(768-len(palette)))
    palette_image.putpalette(palette)
    frames=[]
    for start,end in segments:
        for i in range(math.ceil((end-start)*fps)):
            actual=renderer.render(film.frame(min(end-.001,start+i/fps),160,46))
            frames.append(actual.quantize(palette=palette_image,dither=Image.Dither.NONE))
    durations=[round((i+1)*1000/fps/10)*10-round(i*1000/fps/10)*10 for i in range(len(frames))]
    frames[0].save(OUTPUT/'semantic-preview.gif',save_all=True,
                   append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=1)
    print('已生成六段语义动作的实际画面剪辑预览（静音）。')


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="导出 ÅMARA 的实际终端画面预览")
    parser.add_argument("--gallery", action="store_true", help="生成 V2 镜头总览与字幕检查图")
    parser.add_argument("--gif", action="store_true", help="生成 V2 整屏未知文字入侵动图")
    args = parser.parse_args(argv)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    film, renderer = Film(), CharacterRenderer()
    if args.gallery or not args.gif:
        gallery(film, renderer)
    if args.gif or not args.gallery:
        animated(film, renderer)
        semantic_montage(film,renderer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
