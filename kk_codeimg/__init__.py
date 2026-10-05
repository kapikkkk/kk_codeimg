"""kk_codeimg —— 把代码渲染成精美的代码图片。

最简用法：

    from kk_codeimg import code_generator
    code_generator(code, 'python', output='out.png')
    code_generator(code, 'python', style='tokyo', output='out.png')

不传 output 时返回 PIL.Image.Image。
"""

from __future__ import annotations

from typing import Optional, Union

from PIL import Image

from .palette import BACKGROUND_CHOICES, GRADIENTS, THEMES
from .renderer import CodeImageRenderer, RenderResult
from .styles import STYLES, Style, get_style, list_styles, resolve, resolve_for_render

__all__ = [
    "code_generator",
    "CodeImageRenderer",
    "RenderResult",
    "STYLES",
    "Style",
    "get_style",
    "list_styles",
    "THEMES",
    "GRADIENTS",
    "BACKGROUND_CHOICES",
    "list_themes",
    "list_backgrounds",
]

__version__ = "0.0.1"


def list_themes() -> list:
    """列出全部主题名。"""
    return sorted(THEMES)


def list_backgrounds() -> list:
    """列出全部背景名（含 single / transparent）。"""
    return list(GRADIENTS) + ["single", "transparent"]


def code_generator(
    code: str,
    language: str = "python",
    output: Optional[str] = None,
    *,
    style: Optional[str] = None,
    theme: Optional[str] = None,
    background: Optional[str] = None,
    window_controls: Optional[str] = None,
    font: Optional[str] = None,
    font_size: Optional[int] = None,
    line_height: Optional[float] = None,
    padding: Optional[int] = None,
    line_numbers: Optional[bool] = None,
    transparent_editor: Optional[bool] = None,
    border_radius: Optional[int] = None,
    scrim_alpha: Optional[float] = None,
    title: Optional[str] = None,
    title_alpha: float = 0.72,
    title_size: Optional[Union[int, str]] = None,
    scale: Optional[int] = None,
) -> Union[Image.Image, RenderResult]:
    """把代码渲染成一张精美的代码图片。

    参数
    ----
    code : 源代码文本
    language : 语言名，如 'python' / 'javascript' / 'sql'（Pygments 别名）
    output : PNG 保存路径；None 则只返回 Image

    style : 预设风格名，一次套用一组参数；显式参数优先级更高。
            可选：default / carbon / dracula / tokyo / github / light-frosted /
                  frosted / minimal / neon / share / print

    theme : 12 套主题之一，默认随 style（default 风格为 'one-dark'）
    background : 渐变名 / 'single' / 'transparent' / '#hex'
    window_controls : 'color' / 'gray' / 'gray-light' / 'outline' / 'none'
    font : 字体名或 .ttf 路径；None 时按 Cascadia → JetBrains → DejaVu 顺序探测
    font_size : 字号，默认 15
    line_height : 行高倍数，默认 1.45
    padding : 图片四周留白，默认 64
    line_numbers : 是否显示行号，默认 True
    transparent_editor : 编辑器区域透明，默认 False
    border_radius : 编辑器圆角，默认 9
    scrim_alpha : 透明模式下的底色不透明度 0~1；None 时按主题明暗自动决定
                  （浅色主题自动垫白底，保证深字可读）
    title : 窗口标题，显示在窗口栏居中（控制点右侧）
    title_alpha : 标题不透明度，默认 0.72（退居次要，不与代码抢焦点）
    title_size : 标题字号。`None`（默认）/`'same'` = 与代码同字号；
                  传数字则单独指定（超出窗口栏容量会自动钳制）。
                  **字体始终与代码一致**，只有字号可不同。
    scale : 渲染倍率，默认 2（高清输出）

    返回
    ----
    传了 output -> RenderResult（.image / .path / .editor_box / .code_box）；
    否则 -> PIL.Image.Image
    """
    if not isinstance(code, str):
        raise TypeError("code 必须是字符串")
    if not code.strip():
        raise ValueError("code 不能为空")

    opts = resolve_for_render(
        style,
        theme=theme, background=background, window_controls=window_controls,
        border_radius=border_radius, font=font, font_size=font_size,
        line_height=line_height, padding=padding, line_numbers=line_numbers,
        transparent_editor=transparent_editor, scale=scale,
    )

    renderer = CodeImageRenderer(
        title=title, scrim_alpha=scrim_alpha,
        title_alpha=title_alpha, title_size=title_size, **opts
    )
    result = renderer.render(code, language, output=output)
    return result if output else result.image
