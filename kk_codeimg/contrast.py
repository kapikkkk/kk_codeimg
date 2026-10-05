"""对比度评估：判断「主题 + 背景」组合下代码是否清晰可读。

用途：透明编辑器下，浅色主题的深色文字直接压在背景上极易糊掉
（实测 github-light 的 keyword 压在 leaf 渐变上仅 1.24:1）。
本模块用 WCAG 相对亮度公式给出可读性判定，并提供磨砂底色建议。
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

RGB = Tuple[int, int, int]

# WCAG 阈值
AA_TEXT = 4.5
AA_LARGE = 3.0


def _lin(c: int) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: RGB) -> float:
    r, g, b = rgb
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg: RGB, bg: RGB) -> float:
    la, lb = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def hex_to_rgb(value: str) -> RGB:
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def sample_gradient(c1: str, c2: str, steps: int = 9) -> List[RGB]:
    """在渐变上取样若干点（含两端），用于评估最差情况。"""
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return [
        tuple(round(a[i] + (b[i] - a[i]) * (i_step / (steps - 1))) for i in range(3))  # type: ignore[misc]
        for i_step in range(steps)
    ]


def gradient_extremes(c1: str, c2: str) -> List[RGB]:
    """只取渐变两端与中点——最差对比度通常出现在两端。"""
    return sample_gradient(c1, c2, steps=3)


def blend(fg: RGB, bg: RGB, alpha: float) -> RGB:
    """把 fg 以 alpha 叠在 bg 上，得到实际呈现色。"""
    return tuple(round(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))  # type: ignore[return-value]


def evaluate(
    theme_colors: Dict[str, str],
    background_samples: Iterable[RGB],
    fallback_fg: RGB,
) -> Tuple[float, str, List[Tuple[str, float]]]:
    """评估主题在给定背景上的可读性。

    返回 (最差对比度, 最差槽位名, [(槽位, 对比度), ...])。
    """
    per_slot: List[Tuple[str, float]] = []
    for slot, color in theme_colors.items():
        fg = hex_to_rgb(color)
        worst = min(contrast_ratio(fg, bg) for bg in background_samples)
        per_slot.append((slot, worst))
    if not per_slot:
        return contrast_ratio(fallback_fg, next(iter(background_samples))), "", []
    per_slot.sort(key=lambda kv: kv[1])
    return per_slot[0][1], per_slot[0][0], per_slot


def suggest_scrim_alpha(
    theme_bg: RGB,
    theme_fg: RGB,
    background_samples: Iterable[RGB],
    target: float = AA_TEXT,
) -> float:
    """求出让主题文字达到目标对比度所需的「底色不透明度」。

    在底色上叠一层 theme_bg 的不透明层 alpha，
    返回 0~1 之间的最小可用 alpha。
    """
    samples = list(background_samples)
    best = 1.0
    # 以 2% 步长搜索
    alpha = 0.0
    while alpha <= 1.0:
        ok = True
        for bg in samples:
            composited = blend(theme_bg, bg, alpha)
            if contrast_ratio(theme_fg, composited) < target:
                ok = False
                break
        if ok:
            best = alpha
            break
        alpha += 0.02
    return round(best, 2)


def readability_label(ratio: float) -> str:
    if ratio >= AA_TEXT:
        return "✅ 清晰"
    if ratio >= AA_LARGE:
        return "⚠️ 偏低（仅大字可读）"
    return "❌ 难以辨认"
