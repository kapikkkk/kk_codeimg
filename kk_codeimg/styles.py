"""预设风格：把常用视觉参数打包成具名方案。

新增 `style` 参数后，一种风格 = 一组参数默认值。
未显式传入的参数以 style 为准，显式传入的覆盖 style。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional


@dataclass(frozen=True)
class Style:
    """一组视觉默认值。字段与 CodeImageRenderer 构造参数同名。"""
    name: str
    description: str
    theme: str = "one-dark"
    background: str = "mystic"
    window_controls: str = "color"
    border_radius: int = 9
    font: Optional[str] = None
    font_size: int = 15
    line_height: float = 1.45
    padding: int = 64
    line_numbers: bool = True
    transparent_editor: bool = False
    scale: int = 2


STYLES: Dict[str, Style] = {}


def _add(s: Style) -> Style:
    STYLES[s.name] = s
    return s


# ---- 基础风格 ----
_add(Style(
    name="default",
    description="深色经典：One Dark 主题 + 柔和渐变",
))

_add(Style(
    name="carbon",
    description="经典 Carbon 味：纯色底、无控制点、方正小圆角",
    theme="one-dark", background="single",
    window_controls="none", border_radius=4,
    font_size=15, padding=48,
))

_add(Style(
    name="dracula",
    description="Dracula 紫调 + 极光渐变",
    theme="dracula", background="aurora",
))

_add(Style(
    name="tokyo",
    description="Tokyo Night 夜色 + 深海渐变",
    theme="tokyo-night", background="ocean",
))

_add(Style(
    name="github",
    description="GitHub 浅色 + 淡雅渐变（不透明底，可读性最佳）",
    theme="github-light", background="tropical",
    border_radius=6, padding=56,
))

_add(Style(
    name="light-frosted",
    description="浅色磨砂：保留渐变氛围但垫白底，保证深字清晰",
    theme="github-light", background="leaf",
    transparent_editor=True, border_radius=12, padding=56,
))

_add(Style(
    name="frosted",
    description="深色磨砂玻璃：深色主题铺半透明层，背景隐约透出",
    theme="one-dark", background="mystic",
    transparent_editor=True, border_radius=16,
))

_add(Style(
    name="minimal",
    description="极简：无行号、无控制点、大留白",
    theme="one-dark", background="single",
    window_controls="none", line_numbers=False,
    border_radius=6, padding=80, font_size=16,
))

_add(Style(
    name="neon",
    description="霓虹酷炫：Cool Glow + 香蕉黄渐变 + 大圆角",
    theme="cool-glow", background="bananas",
    border_radius=20, padding=56,
))

_add(Style(
    name="share",
    description="社交分享：大字号、大圆角、宽留白",
    theme="one-dark", background="candy",
    font_size=20, line_height=1.55, border_radius=14, padding=72,
))

_add(Style(
    name="print",
    description="打印友好：白底、黑字、无阴影干扰",
    theme="xcode-light", background="single",
    window_controls="none", border_radius=2,
    padding=40, font_size=14,
))

_add(Style(
    name="ocean",
    description="深海蓝：冷色调、克制圆角",
    theme="vscode", background="ocean",
    border_radius=10, padding=56,
))

_add(Style(
    name="sunset",
    description="日落暖橙：亮色系、适合长代码",
    theme="ayu-light", background="peach",
    border_radius=10, padding=56, font_size=14,
))

_add(Style(
    name="forest",
    description="森林绿：护眼低饱和",
    theme="github-dark", background="leaf",
    border_radius=10, padding=56,
))

_add(Style(
    name="grid",
    description="网格纸：极细边框、零圆角、代码排版感",
    theme="one-dark", background="#1e2128",
    window_controls="outline", border_radius=0,
    padding=48, font_size=14, line_height=1.6,
))

_add(Style(
    name="sticker",
    description="贴纸风：浅色、夸张圆角、紧凑",
    theme="github-light", background="bananas",
    border_radius=24, padding=44, font_size=15,
))


# 常用别名，避免用户因记不住确切名字而报错
_ALIASES = {
    "dark": "default",
    "light": "github",
    "plain": "minimal",
    "classic": "carbon",
    "frost": "frosted",
    "rounded": "sticker",
    "sharp": "grid",
    "big": "share",
    "night": "tokyo",
    "matrix": "forest",
}


def get_style(name: str) -> Style:
    """按名称取风格。

    支持大小写、下划线/空格差异，以及 `dark` / `light` / `plain` 等常用别名。
    """
    key = (name or "").strip().lower().replace("_", "-").replace(" ", "-")
    key = _ALIASES.get(key, key)
    if key not in STYLES:
        raise ValueError(
            f"未知风格 {name!r}；可选：{', '.join(sorted(STYLES))}"
            f"（可用别名：{', '.join(sorted(_ALIASES))}）"
        )
    return STYLES[key]


def list_styles() -> list:
    return sorted(STYLES)


def resolve(
    style: Optional[str],
    *,
    theme: Optional[str] = None,
    background: Optional[str] = None,
    window_controls: Optional[str] = None,
    border_radius: Optional[int] = None,
    font: Optional[str] = None,
    font_size: Optional[int] = None,
    line_height: Optional[float] = None,
    padding: Optional[int] = None,
    line_numbers: Optional[bool] = None,
    transparent_editor: Optional[bool] = None,
    scale: Optional[int] = None,
) -> dict:
    """把 style 预设与显式参数合并，显式参数优先。

    判定「是否显式传入」用哨兵值——这样 `line_numbers=False`、
    `transparent_editor=False` 这类 False 值也能正确覆盖 style。
    """
    base = get_style(style) if style else Style(
        name="__default__", description="内置默认"
    )
    kw = dict(
        theme=theme, background=background, window_controls=window_controls,
        border_radius=border_radius, font=font, font_size=font_size,
        line_height=line_height, padding=padding, line_numbers=line_numbers,
        transparent_editor=transparent_editor, scale=scale,
    )
    resolved = {}
    for key, override in kw.items():
        resolved[key] = override if override is not None else getattr(base, key)
    return resolved


# 允许透传给 CodeImageRenderer 的字段白名单
RENDERER_FIELDS = (
    "theme", "background", "window_controls", "font", "font_size",
    "line_height", "padding", "line_numbers", "transparent_editor",
    "border_radius", "scale",
)


def resolve_for_render(style: Optional[str] = None, **overrides) -> dict:
    """resolve() + 白名单过滤，可直接展开给 CodeImageRenderer(**kwargs)。"""
    opts = resolve(style, **overrides)
    return {k: opts[k] for k in RENDERER_FIELDS if k in opts}
