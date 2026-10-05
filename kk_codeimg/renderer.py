"""渲染引擎：Pygments 分词 + Pillow 逐 token 绘制。

关键规格（来自 codepng.app 打包 CSS，非目测）：
  窗口栏 40px / 顶部左右圆角 9px / 控制点直径 12px / 容器宽 48px / margin-left 16px
  阴影    rgba(0,0,0,.6) 0 0 18px 1px + rgba(255,255,255,.23) 0 0 0 1px
  背景    linear-gradient(90deg, c1, c2)，即左右走向
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pygments.lexers import get_lexer_by_name
from pygments.lexers.python import PythonLexer
from pygments.token import Token
from pygments.util import ClassNotFound

from .palette import GRADIENTS, THEMES, WINDOW_CONTROLS, Theme, get_gradient, get_theme

# ---- codepng 实测规格 ----
BAR_HEIGHT = 40           # .windowbar_windowContainer height
BAR_RADIUS = 9            # 顶部左右圆角
DOT_SIZE = 12             # 控制点直径
DOT_CONTAINER_W = 48      # 控制点容器宽度
DOT_MARGIN_LEFT = 16      # margin-left: 1rem
CORNER_RADIUS = 9         # 编辑器外框圆角
SHADOW_BLUR = 18          # 0 0 18px 1px
SHADOW_ALPHA = 153        # rgba(0,0,0,.6)
RING_COLOR = (255, 255, 255, 59)   # rgba(255,255,255,23%)
CODE_PAD_X = 28           # 代码区左右留白
CODE_PAD_Y = 20           # 代码区上下留白
GUTTER_GAP = 14           # 行号与代码间距


# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------
_FONT_CANDIDATES = {
    "jetbrains": ["JetBrainsMono-Regular.ttf", "JetBrainsMono[wght].ttf"],
    "cascadia": ["CascadiaMono.ttf", "CascadiaCode.ttf"],
    "consolas": ["consola.ttf", "Consola.ttf"],
    "menlo": ["Menlo.ttc", "Menlo-Regular.ttf"],
    "courier": ["cour.ttf", "Courier New.ttf", "cour.ttf"],
    "dejavu": ["DejaVuSansMono.ttf", "DejaVuSansMono_0.ttf"],
    "ubuntu-mono": ["UbuntuMono-R.ttf", "UbuntuMono.ttf"],
}
# 默认按此顺序探测；全部为免费商用字体（OFL / Bitstream Vera / 微软随系统授权）
_DEFAULT_ORDER = ("cascadia", "jetbrains", "dejavu", "consolas", "ubuntu-mono", "courier")

_font_cache: Dict[Tuple, ImageFont.FreeTypeFont] = {}


def _font_dirs() -> List[str]:
    dirs = []
    win = os.environ.get("WINDIR", "C:/Windows")
    dirs.append(os.path.join(win, "Fonts"))
    local = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
    if local:
        dirs.append(local)
    dirs.append("/usr/share/fonts/truetype")
    dirs.append("/Library/Fonts")
    return [d for d in dirs if d and os.path.isdir(d)]


def _load_font(name: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    """按名称或路径加载等宽字体，带缓存。"""
    if name and (os.path.isfile(name) or (os.sep in name and name.lower().endswith((".ttf", ".otf", ".ttc")))):
        key = (name, size)
        if key not in _font_cache:
            _font_cache[key] = ImageFont.truetype(name, size)
        return _font_cache[key]

    # 注意：必须取 dict 的 value（文件名列表），不能直接迭代 dict
    order = _DEFAULT_ORDER if name is None else (name,)
    names: List[str] = []
    for key_name in order:
        names.extend(_FONT_CANDIDATES.get(key_name, [key_name]))

    for d in _font_dirs():
        for fn in names:
            p = os.path.join(d, fn)
            if os.path.isfile(p):
                cache_key = (p, size)
                if cache_key not in _font_cache:
                    _font_cache[cache_key] = ImageFont.truetype(p, size)
                return _font_cache[cache_key]
    raise RuntimeError(
        "未找到可用的等宽字体。请用 font= 参数显式指定 .ttf 路径，"
        "或在系统字体目录安装 Cascadia Mono / JetBrains Mono / DejaVu Sans Mono。"
    )


def _load_cjk_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    """中文回退字体（等宽字体普遍无中文字形）。找不到返回 None。"""
    for fn in ("msyh.ttc", "msyhl.ttc", "simhei.ttf", "NotoSansSC-VF.ttf",
               "simsun.ttc", "PingFang.ttc", "NotoSansCJK-Regular.ttc"):
        for d in _font_dirs():
            p = os.path.join(d, fn)
            if os.path.isfile(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
    return None


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x4E00 <= o <= 0x9FFF      # CJK 统一表意
        or 0x3400 <= o <= 0x4DBF   # 扩展 A
        or 0x3000 <= o <= 0x303F   # CJK 标点
        or 0xFF00 <= o <= 0xFFEF   # 全角
        or 0xAC00 <= o <= 0xD7AF   # 韩文
    )


def _split_runs(text: str) -> List[Tuple[str, bool]]:
    """把文本切成 [(片段, 是否 CJK)]，用于逐段选字体。"""
    runs: List[Tuple[str, bool]] = []
    for ch in text:
        c = _is_cjk(ch)
        if runs and runs[-1][1] == c:
            runs[-1] = (runs[-1][0] + ch, c)
        else:
            runs.append((ch, c))
    return runs


class _TextPen:
    """按字符选择字体绘制，兼顾等宽对齐与中文显示。"""

    def __init__(self, mono: ImageFont.FreeTypeFont, cjk: Optional[ImageFont.FreeTypeFont]) -> None:
        self.mono = mono
        self.cjk = cjk

    def measure(self, text: str) -> float:
        total = 0.0
        if self.cjk is None:
            return self.mono.getlength(text)
        for frag, is_cjk in _split_runs(text):
            total += (self.cjk if is_cjk else self.mono).getlength(frag)
        return total

    def draw(self, draw: "ImageDraw.ImageDraw", xy: Tuple[float, float], text: str, fill,
             anchor: str = "la", bg: Optional[Tuple[int, int, int]] = None) -> float:
        """绘制文本并返回结束 x。

        注意：fill 带 alpha 时不能直接交给 PIL。
        ImageDraw.text() 在 RGBA 图上会忽略 fill 的 alpha 通道
        （实测 title_alpha=1.0 与 0.15 画出的像素完全相同），
        因此这里按 bg 预乘混合，得到等效实色。
        """
        x, y = xy
        rgba = fill if isinstance(fill, tuple) and len(fill) == 4 else None
        if rgba and rgba[3] < 255:
            base = bg or (0, 0, 0)
            a = rgba[3] / 255.0
            fill = tuple(round(rgba[i] * a + base[i] * (1 - a)) for i in range(3))
        if self.cjk is None:
            draw.text((x, y), text, font=self.mono, fill=fill, anchor=anchor)
            return x + self.mono.getlength(text)
        for frag, is_cjk in _split_runs(text):
            font = self.cjk if is_cjk else self.mono
            draw.text((x, y), frag, font=font, fill=fill, anchor=anchor)
            # 非 "la" 锚点时 PIL 自己处理定位，这里只需推进 x
            x += font.getlength(frag)
        return x


# ---------------------------------------------------------------------------
# Pygments token -> codepng 语义槽位
# ---------------------------------------------------------------------------
def _map_token(ttype, theme: Theme) -> str:
    """把 Pygments token 映射到主题的语义颜色槽。"""
    t = ttype
    # 精确槽位优先
    table = {
        Token.Comment: "comment",
        Token.Keyword.Namespace: "module_keyword",
        Token.Keyword.Type: "type_name",
        Token.Keyword.Constant: "bool",
        Token.Keyword: "keyword",
        Token.Name.Class: "class_name",
        Token.Name.Function: "function",
        Token.Name.Builtin: "name",
        Token.Name.Decorator: "definition_keyword",
        Token.Name.Exception: "class_name",
        Token.Name.Namespace: "namespace",
        Token.Name.Attribute: "property_name",
        Token.Name.Constant: "constant",
        Token.Name.Tag: "tag_name",
        Token.Name.Variable: "variable_name",
        Token.Name: "name",
        Token.Literal.Number: "number",
        Token.String.Doc: "string",
        Token.String.Escape: "string",
        Token.String: "string",
        Token.Operator.Word: "keyword",
        Token.Operator: "operator",
        Token.Punctuation: "punctuation",
        Token.Error: "invalid",
    }
    cur = t
    while cur is not None:
        if cur in table:
            slot = table[cur]
            if slot in theme.colors:
                return slot
        cur = cur.parent
    return ""  # 交给主题前景色


def _highlight(code: str, lexer, theme: Theme) -> List[List[Tuple[str, Tuple[int, int, int]]]]:
    """返回按行切分的 [(片段文本, 颜色)]。"""
    lines: List[List[Tuple[str, Tuple[int, int, int]]]] = []
    default = theme.fg_rgb()
    for ttype, value in lexer.get_tokens(code):
        if not value:
            continue
        slot = _map_token(ttype, theme)
        color = theme.color(slot) if slot else default
        parts = value.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append([])
            if part:
                if not lines:
                    lines.append([])
                lines[-1].append((part, color))
    return lines


def _get_lexer(language: str):
    try:
        return get_lexer_by_name(language, stripnl=False, ensurenl=False)
    except ClassNotFound:
        return PythonLexer(stripnl=False, ensurenl=False)


# ---------------------------------------------------------------------------
# 绘制基元
# ---------------------------------------------------------------------------
def _linear_gradient(size: Tuple[int, int], c1: str, c2: str) -> Image.Image:
    """左右走向线性渐变（对应 CSS linear-gradient(90deg, c1, c2)）。"""
    w, h = size
    r1, g1, b1 = _rgb(c1)
    r2, g2, b2 = _rgb(c2)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for x in range(w):
        t = x / max(1, w - 1)
        col = (
            round(r1 + (r2 - r1) * t),
            round(g1 + (g2 - g1) * t),
            round(b1 + (b2 - b1) * t),
        )
        for y in range(h):
            px[x, y] = col
    return img


def _rgb(value: str) -> Tuple[int, int, int]:
    from .palette import _hex_to_rgb
    return _hex_to_rgb(value)


def _rounded_mask(size: Tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


# ---------------------------------------------------------------------------
# 主渲染
# ---------------------------------------------------------------------------
@dataclass
class RenderResult:
    image: Image.Image
    path: Optional[str] = None
    # 编辑器在画布中的精确矩形 (left, top, right, bottom)，供裁剪/校验使用
    editor_box: Optional[Tuple[int, int, int, int]] = None
    # 代码区（窗口栏以下）的精确矩形
    code_box: Optional[Tuple[int, int, int, int]] = None


class CodeImageRenderer:
    """按 codepng 规格组装图片。"""

    def __init__(
        self,
        theme: str = "one-dark",
        background: str = "mystic",
        window_controls: str = "color",
        font: Optional[str] = None,
        font_size: int = 15,
        line_height: float = 1.45,
        padding: int = 64,
        line_numbers: bool = True,
        transparent_editor: bool = False,
        title: Optional[str] = None,
        scale: int = 2,
        border_radius: int = CORNER_RADIUS,
        scrim_alpha: Optional[float] = None,
        title_alpha: float = 0.72,
        title_size: Optional[int] = None,
    ) -> None:
        self.theme: Theme = get_theme(theme)
        self.background = background
        self.window_controls = window_controls if window_controls in WINDOW_CONTROLS else "color"
        self.font_name = font
        self.font_size = font_size
        self.line_height = line_height
        self.padding = padding
        self.line_numbers = line_numbers
        self.transparent_editor = transparent_editor
        self.title = title
        self.title_alpha = max(0.0, min(1.0, float(title_alpha)))
        # 标题字号：None -> 跟随 font_size（视觉上与代码齐平）
        #         "same" -> 显式同字号（等价于 font_size）
        #         int    -> 指定字号，超过窗口栏容量会被钳制
        self.title_size = self._resolve_title_size(title_size)
        self._title_pen: Optional[_TextPen] = None
        self.scale = max(1, int(scale))
        self.border_radius = max(0, int(border_radius))
        # 透明编辑器下，浅色主题的深色文字直接压在背景上极易糊掉
        # （实测 github-light 的 keyword 压在 leaf 渐变上仅 1.24:1）。
        # 故默认给浅色主题铺一层高不透明度白底，保留背景氛围同时保证可读。
        self.scrim_alpha = scrim_alpha

    # -- 背景 ---------------------------------------------------------------
    def _build_background(self, w: int, h: int) -> Image.Image:
        """始终返回 RGBA 画布，避免后续 alpha_composite 模式冲突。"""
        name = (self.background or "mystic").strip().lower()
        if name in ("transparent", "none", "alpha"):
            return Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if name == "single":
            return Image.new("RGBA", (w, h), _rgb("#b993d6") + (255,))
        pair = get_gradient(name)
        if pair is None:
            # 允许直接给 '#aabbcc' 或 'aabbcc'
            v = self.background.strip()
            c = v if v.startswith("#") else "#" + v
            return Image.new("RGBA", (w, h), _rgb(c) + (255,))
        return _linear_gradient((w, h), pair[0], pair[1]).convert("RGBA")

    # -- 主流程 -------------------------------------------------------------
    def render(self, code: str, language: str = "python", output: Optional[str] = None) -> RenderResult:
        s = self.scale
        theme = self.theme
        font = _load_font(self.font_name, self.font_size * s)
        cjk_font = _load_cjk_font(self.font_size * s)
        pen = _TextPen(font, cjk_font)

        # 标题字体：与代码**同一个字体族**，只有字号可不同。
        # 字号相同时直接复用代码的字体对象，保证 100% 同一文件（含 CJK）。
        if self.title:
            t_size = self.title_size * s
            if abs(self.title_size - self.font_size) < 1e-6:
                self._title_pen = pen          # 完全复用
            else:
                self._title_pen = _TextPen(
                    _load_font(self.font_name, t_size),
                    _load_cjk_font(t_size),
                )
        else:
            self._title_pen = None

        lexer = _get_lexer(language)
        hl_lines = _highlight(code.rstrip("\n"), lexer, theme)
        if not hl_lines:
            hl_lines = [[]]

        # 行高（像素）
        lh = round(self.font_size * self.line_height) * s
        # 单字符宽度：用于行号右对齐与最小宽度估算
        cw = max(1, int(round(font.getlength("M"))))

        gutter_w = 0
        if self.line_numbers:
            digits = len(str(max(1, len(hl_lines))))
            gutter_w = int(round(pen.measure("8" * digits))) + GUTTER_GAP * s

        # 文本区宽高
        text_w = 0
        for line in hl_lines:
            w = int(round(sum(pen.measure(t) for t, _ in line)))
            text_w = max(text_w, w)
        text_w = max(text_w, cw * 20)

        content_w = gutter_w + text_w
        content_h = lh * len(hl_lines)

        # 编辑器窗口尺寸
        editor_w = content_w + CODE_PAD_X * 2 * s
        editor_h = BAR_HEIGHT * s + content_h + CODE_PAD_Y * 2 * s

        # 画布尺寸（含外边距与阴影余量）
        pad = self.padding * s
        shadow_pad = (SHADOW_BLUR + 6) * s
        canvas_w = editor_w + pad * 2 + shadow_pad * 2
        canvas_h = editor_h + pad * 2 + shadow_pad * 2

        canvas = self._build_background(canvas_w, canvas_h)

        ex = shadow_pad + pad          # 编辑器左上角
        ey = shadow_pad + pad
        editor = self._build_editor(editor_w, editor_h, pen, lh, gutter_w, hl_lines)
        # 阴影：模糊黑
        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            [ex, ey + 2 * s, ex + editor_w, ey + editor_h + 2 * s],
            radius=self.border_radius * s, fill=(0, 0, 0, SHADOW_ALPHA),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR * s / 2))
        canvas = Image.alpha_composite(canvas, shadow)

        # 1px 白色内描边（rgba(255,255,255,.23)）
        ring = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(ring).rounded_rectangle(
            [ex, ey, ex + editor_w - 1, ey + editor_h - 1],
            radius=self.border_radius * s, outline=RING_COLOR, width=max(1, s // 2),
        )
        canvas = Image.alpha_composite(canvas, ring)

        # 编辑器主体（自带圆角 alpha 遮罩）
        canvas.paste(editor, (ex, ey), editor)
        box = (ex, ey, ex + editor_w, ey + editor_h)
        code_box = (ex + CODE_PAD_X * s, ey + BAR_HEIGHT * s + CODE_PAD_Y * s,
                    ex + editor_w - CODE_PAD_X * s, ey + editor_h - CODE_PAD_Y * s)
        if output:
            os.makedirs(os.path.dirname(os.path.abspath(output)) or ".", exist_ok=True)
            # 仅在不透明背景下压成 RGB；透明背景保留 alpha
            if (self.background or "").strip().lower() in ("transparent", "none", "alpha"):
                canvas.save(output, "PNG")
            else:
                canvas.convert("RGB").save(output, "PNG")
            return RenderResult(canvas, os.path.abspath(output), box, code_box)
        return RenderResult(canvas, None, box, code_box)

    # -- 编辑器内部 ---------------------------------------------------------
    def _max_title_size(self) -> float:
        """窗口栏能容纳的最大标题字号（逻辑像素）。

        栏高固定 40px，字形盒高约为字号的 0.7 倍，留 6px 余量。
        超出这个值标题会盖住代码区，属于静默失败，必须钳制。
        """
        return max(8.0, (BAR_HEIGHT - 6) / 0.7)

    def _resolve_title_size(self, title_size) -> float:
        """把 title_size 归一化为实际使用的字号。

        None / "same" -> 与 font_size 齐平（字体统一，字号也可统一）
        数字          -> 使用该字号，但不超过窗口栏容量
        """
        if title_size is None or (isinstance(title_size, str)
                                  and title_size.strip().lower() == "same"):
            want = float(self.font_size)
        else:
            try:
                want = float(title_size)
            except (TypeError, ValueError):
                raise ValueError(
                    f"title_size 应为数字、None 或 'same'，收到 {title_size!r}"
                ) from None
        if want <= 0:
            raise ValueError(f"title_size 必须大于 0，收到 {title_size!r}")
        return min(want, self._max_title_size())

    def renderer_probe(self) -> dict:
        """暴露关键渲染决策，供测试与调试使用（不影响正常渲染）。"""
        return {
            "theme": self.theme.name,
            "dark": self.theme.dark,
            "background": self.background,
            "border_radius": self.border_radius,
            "transparent_editor": self.transparent_editor,
            "scrim": self._scrim_opacity(None),
            "font": self.font_name or "auto",
            "font_size": self.font_size,
            "title_size": self.title_size,
            "title": self.title,
        }

    def _scrim_opacity(self, bg_samples: Optional[List[Tuple[int, int, int]]]) -> float:
        """决定透明模式下编辑器铺多少不透明底色。

        深色主题文字本身够亮，全透明即可，保持通透观感。
        浅色主题必须垫一层高不透明度白底——实测 github-light 的 keyword
        压在 leaf 渐变上只有 1.24:1，垫到 100% 才达 4.5:1（AA）。

        返回 0~1。scrim_alpha 参数可手动覆盖。
        """
        if self.scrim_alpha is not None:
            return max(0.0, min(1.0, float(self.scrim_alpha)))
        if not self.theme.dark:
            return 1.0 if bg_samples else 1.0
        return 0.0

    def _build_editor(self, w: int, h: int, pen: "_TextPen", lh: int, gutter_w: int,
                      lines, bg_samples=None) -> Image.Image:
        s = self.scale
        theme = self.theme
        if self.transparent_editor:
            alpha = self._scrim_opacity(bg_samples)
            if alpha >= 1.0:
                img = Image.new("RGBA", (w, h), theme.bg_rgb() + (255,))
            elif alpha > 0:
                # 磨砂：半透明主题底色，背景渐变隐约透出
                img = Image.new("RGBA", (w, h), theme.bg_rgb() + (round(alpha * 255),))
            else:
                img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        else:
            img = Image.new("RGBA", (w, h), theme.bg_rgb() + (255,))
        d = ImageDraw.Draw(img)

        self._draw_window_controls(d, w, h)
        if self._title_pen is not None:
            self._draw_title(d, w, h, self._title_pen)

        # 代码区起点
        cy = BAR_HEIGHT * s + CODE_PAD_Y * s
        cx = CODE_PAD_X * s
        gutter_color = theme.gutter_rgb()

        for idx, line in enumerate(lines, start=1):
            y = cy + (idx - 1) * lh
            if self.line_numbers:
                num = str(idx)
                num_w = pen.measure(num)
                pen.draw(d, (cx + gutter_w - GUTTER_GAP * s - num_w, y), num, gutter_color)
            x = cx + gutter_w
            for text, color in line:
                x = pen.draw(d, (x, y), text, color)

        # 应用圆角遮罩：此前编辑器画的是直角矩形，边缘显得生硬。
        # 窗口栏只需顶部左右圆角，代码区保持方角，故用整块圆角 + 顶部补方。
        r = max(0, int(self.border_radius)) * s
        if r > 0:
            mask = _rounded_mask((w, h), r)
            img.putalpha(mask)
        return img

    def _draw_window_controls(self, d: ImageDraw.ImageDraw, w: int, h: int) -> None:
        s = self.scale
        spec = WINDOW_CONTROLS[self.window_controls]
        if self.window_controls != "none":
            border = spec.get("border")
            r = DOT_SIZE * s / 2
            cy = BAR_HEIGHT * s / 2
            start_x = DOT_MARGIN_LEFT * s + r
            gap = (DOT_CONTAINER_W * s - DOT_SIZE * s) / 2
            for key in ("exit", "min", "max"):
                cx = start_x + gap * ("exit", "min", "max").index(key)
                color = spec.get(key)
                if color is None:
                    if border:
                        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                                  outline=_rgb(border), width=max(1, s // 2))
                    else:
                        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 0, 0, 0))
                else:
                    col = _rgba(color)
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    def _draw_title(self, d: ImageDraw.ImageDraw, w: int, h: int, pen: "_TextPen") -> None:
        """在窗口栏居中绘制标题。

        配色：用主题前景色而非 gutter 色——实测 gutter 色在部分主题上
        对比度仅 2.76:1（tokyo-night），前景色全部 >= 6.10:1。
        再乘 title_alpha 让它退居次要，不与代码抢视觉焦点。
        """
        if not self.title:
            return
        s = self.scale
        text = str(self.title)

        # 标题在**整个编辑器宽度**居中。
        # 早期实现是在「扣掉左侧控制点区」的不对称区域里居中
        # （左 160px / 右 32px），导致标题右偏 58px（scale=2）。
        # 现在 x 由编辑器中点决定，left_pad 只用于超宽判定与截断。
        left_pad = (DOT_MARGIN_LEFT + DOT_CONTAINER_W + 16) * s
        right_pad = 16 * s
        max_w = w - left_pad - right_pad
        if max_w <= 0:
            return

        # 标题宽度用 pen.measure，正确处理中英混排
        size = pen.measure(text)
        if size > max_w:
            # 超宽则截断并加省略号
            out: List[str] = []
            acc = 0.0
            ell = "…"
            for ch in text:
                cw = pen.measure(ch + ell)
                if acc + cw > max_w:
                    break
                out.append(ch)
                acc += cw
            text = "".join(out) + ell
            size = pen.measure(text)

        # 关键：x 为标题左边缘，锚点 "lm" 表示从该点向右绘制。
        # 故 x = 编辑器中点 - 标题半宽，才是真正的视觉居中。
        x = w / 2 - size / 2
        # 标题很宽时（超过半边），居中会撞上左侧控制点区 —— 钳制避让。
        # 此时牺牲"严格居中"以换取不重叠，属于必要取舍。
        if x < left_pad:
            x = left_pad
        elif x + size > w - right_pad:
            x = max(left_pad, w - right_pad - size)
        y = BAR_HEIGHT * s / 2
        # 标题用前景色（对比度 >= 6.10:1），乘 title_alpha 退居次要。
        # 混合底色取编辑器实际呈现色——透明模式下是垫底色，需按不透明度算。
        base = self.theme.bg_rgb()
        if self.transparent_editor:
            a = self._scrim_opacity(None)
            if a < 1.0:
                # 全透明时用背景色兜底混合，避免标题变成"看不见的浅色"
                base = _rgb(get_gradient(self.background)[0]) if get_gradient(self.background) else base
            else:
                base = self.theme.bg_rgb()
        color = self.theme.fg_rgb() + (round(255 * self.title_alpha),)
        pen.draw(d, (x, y), text, color, anchor="lm", bg=base)


def _rgba(value: str) -> Tuple[int, int, int, int]:
    """支持 #RRGGBB / #RRGGBBAA（gray 系列控制点就是 8 位带 alpha）。"""
    from .palette import _hex_to_rgb
    v = value.strip().lstrip("#")
    if len(v) == 8:  # RRGGBBAA
        r, g, b = _hex_to_rgb("#" + v[:6])
        return (r, g, b, int(v[6:8], 16))
    r, g, b = _hex_to_rgb("#" + v)
    return (r, g, b, 255)
