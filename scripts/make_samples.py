"""生成全套样图，用于人工比对与回归验证。"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from kk_codeimg import code_generator, list_backgrounds, list_themes

OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

PY = '''from dataclasses import dataclass


@dataclass
class Point:
    """一个二维坐标点。"""
    x: float
    y: float

    def dist(self, other: "Point") -> float:
        # 欧氏距离
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


def centroid(points: list[Point]) -> Point:
    if not points:
        raise ValueError("空列表没有重心")
    n = len(points)
    return Point(sum(p.x for p in points) / n, sum(p.y for p in points) / n)
'''

JS = """const multiply = (x, y) => {
  return x * y;
}

console.log(multiply(2, 3));
"""

SQL = """SELECT u.id, u.name, COUNT(o.id) AS orders
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at >= '2026-01-01'
GROUP BY u.id
HAVING COUNT(o.id) > 3
ORDER BY orders DESC;"""


def main() -> None:
    # 1. 全部主题（默认背景下）
    for t in list_themes():
        p = os.path.join(OUT, f"theme_{t}.png")
        code_generator(PY, "python", output=p, theme=t)
        print("theme  ", t)

    # 2. 全部渐变背景（One Dark 主题）
    for b in list_backgrounds():
        p = os.path.join(OUT, f"bg_{b}.png")
        code_generator(PY, "python", output=p, background=b)
        print("bg     ", b)

    # 3. 窗口控制点样式
    for wc in ("color", "gray", "outline", "none"):
        p = os.path.join(OUT, f"ctrl_{wc}.png")
        code_generator(PY, "python", output=p, window_controls=wc)
        print("ctrl   ", wc)

    # 4. 多语言
    for lang, code in (("javascript", JS), ("sql", SQL)):
        p = os.path.join(OUT, f"lang_{lang}.png")
        code_generator(code, lang, output=p)
        print("lang   ", lang)

    # 5. 变体：透明编辑器 / 无行号 / 小留白 / 单色背景 / 1x
    code_generator(PY, "python", output=os.path.join(OUT, "var_transparent_editor.png"),
                   transparent_editor=True, background="ocean")
    code_generator(PY, "python", output=os.path.join(OUT, "var_no_linenumbers.png"),
                   line_numbers=False)
    code_generator(PY, "python", output=os.path.join(OUT, "var_pad16.png"), padding=16)
    code_generator(PY, "python", output=os.path.join(OUT, "var_scale1.png"), scale=1)
    code_generator(PY, "python", output=os.path.join(OUT, "var_hex_bg.png"),
                   background="#1d976c", theme="tokyo-night")
    code_generator(PY, "python", output=os.path.join(OUT, "var_font_size.png"), font_size=20)
    print("variants ok")

    # 6. 边界情况
    code_generator("x = 1", "python", output=os.path.join(OUT, "edge_oneline.png"))
    code_generator("a" * 200, "python", output=os.path.join(OUT, "edge_longline.png"))
    code_generator("SELECT 1", "nonexistent-lang", output=os.path.join(OUT, "edge_badlang.png"))
    # 空代码应报错（预期行为）
    try:
        code_generator("   ", "python", output=os.path.join(OUT, "edge_blank.png"))
        print("edges  !! 空代码未报错")
    except ValueError:
        print("edges   空代码正确抛 ValueError")
    print("edges  ok")
    print("\n样图目录:", OUT)


if __name__ == "__main__":
    main()
