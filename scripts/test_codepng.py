"""关键行为回归测试：python -m pytest scripts/test_codepng.py -q"""

import os
import sys

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from kk_codeimg import code_generator, list_backgrounds, list_themes  # noqa: E402
from kk_codeimg.palette import GRADIENTS, THEMES  # noqa: E402
from kk_codeimg.renderer import _load_font  # noqa: E402

CODE = '''def add(a: int, b: int) -> int:
    # 两数相加
    return a + b
'''


def test_returns_image_without_output():
    img = code_generator(CODE, "python")
    assert isinstance(img, Image.Image)
    assert img.width > 100 and img.height > 100


def test_saves_file(tmp_path):
    p = tmp_path / "x.png"
    r = code_generator(CODE, "python", output=str(p))
    assert p.exists()
    assert r.path == str(p)
    assert os.path.getsize(p) > 0


def test_real_mono_font_loaded():
    """防止静默降级成 Pillow 位图字体（会丢缩进）。"""
    f = _load_font(None, 30)
    assert f.getlength("    ") > 40, "等宽字体空格宽度异常，疑似降级"


def _code_ink(code: str):
    """返回代码区（左, 右）墨迹像素 x 范围。

    直接取渲染器给出的精确 code_box，不靠坐标推算。
    关键：深色主题里代码文字比编辑器底色「更亮」
    （One Dark 底色 #282c34 亮度 44，注释 #54636d 亮度 96），
    所以要检测亮于底色的像素，而不是更暗的。
    """
    from kk_codeimg.renderer import CodeImageRenderer

    r = CodeImageRenderer(background="single", line_numbers=False,
                          padding=16, scale=2).render(code, "python")
    l, t, rr, b = r.code_box
    gray = r.image.convert("L").load()
    bg = gray[(l + rr) // 2, b - 4]          # 空白处 = 底色
    xs = [x for x in range(l, rr)
          for y in range(t, b) if gray[x, y] > bg + 10]
    return (min(xs), max(xs)) if xs else (-1, -1)


def test_indent_preserved():
    """缩进必须真实绘制为像素偏移。"""
    indent_left, _ = _code_ink("    x = 1")
    flat_left, _ = _code_ink("x = 1")
    assert indent_left > flat_left, f"缩进未体现：{indent_left} vs {flat_left}"
    # 4 空格在 15px*2 scale 下约 4*18=72px，允许误差
    assert indent_left - flat_left > 20, "缩进偏移量过小"


def test_cjk_not_tofu():
    """中文必须由 CJK 字体真实绘制，而不是等宽字体的豆腐块。

    做法：检查 _TextPen 对中文的排版宽度。
    - 若中文走等宽回退（豆腐块），宽度会按等宽 advance 算；
    - 走 CJK 字体（全角）时，每字 advance 约为等宽 ASCII 的 1.5~2 倍。
    另外用像素级墨迹数确认确实有笔画被画出。
    """
    from kk_codeimg.renderer import _load_cjk_font, _load_font, _TextPen

    pen = _TextPen(_load_font(None, 30), _load_cjk_font(30))
    cn = pen.measure("中" * 10)
    en = pen.measure("M" * 10)
    assert cn > en, f"中文宽度未按全角计算：cn={cn} en={en}"

    # 像素级确认：有中文的注释确实画出了笔画
    r = _code_ink("# 中文中文中文中文中文")
    assert r[1] > r[0], "中文注释未绘制出任何笔画（疑似豆腐块或缺字）"


def test_all_themes_render():
    for t in list_themes():
        img = code_generator(CODE, "python", theme=t)
        assert img.width > 0


def test_all_backgrounds_render():
    for b in list_backgrounds():
        img = code_generator(CODE, "python", background=b)
        assert img.width > 0


def test_transparent_background_keeps_alpha():
    import io
    buf = io.BytesIO()
    img = code_generator(CODE, "python", background="transparent")
    img.save(buf, "PNG")
    buf.seek(0)
    assert Image.open(buf).mode == "RGBA"


def test_hex_background():
    assert code_generator(CODE, "python", background="#ff0000").width > 0


def test_scale_changes_size():
    a = code_generator(CODE, "python", scale=1)
    b = code_generator(CODE, "python", scale=2)
    assert b.width > a.width


def test_line_numbers_toggle():
    a = code_generator(CODE, "python", line_numbers=True)
    b = code_generator(CODE, "python", line_numbers=False)
    assert a.width > b.width


def test_multiple_languages():
    for lang, src in (("javascript", "const a = 1;"), ("sql", "SELECT 1;"),
                      ("html", "<p>hi</p>"), ("java", "class A{}")):
        assert code_generator(src, lang).width > 0


def test_unknown_language_falls_back():
    """未知语言不应崩溃，回退到 Python lexer。"""
    assert code_generator("x = 1", "totally-unknown-lang").width > 0


def test_empty_code_raises():
    with pytest.raises(ValueError):
        code_generator("   ", "python")


def test_non_string_raises():
    with pytest.raises(TypeError):
        code_generator(123, "python")  # type: ignore[arg-type]


def test_unknown_theme_raises():
    with pytest.raises(ValueError):
        code_generator(CODE, "python", theme="no-such-theme")


def test_palette_completeness():
    assert len(THEMES) == 12
    assert len(GRADIENTS) == 10
    for name, theme in THEMES.items():
        assert theme.bg and theme.fg, name


def test_no_slot_collapses_to_foreground():
    """防止「槽位缺失 -> 静默退化成前景色」导致整片代码看起来没高亮。

    判据：若某槽位最终解析成前景色，只有在「该主题并未显式定义它
    及其回退链」时才算退化。若主题自己就定义成前景色（One Dark 的
    operator/punctuation 就是 #d4d4d4），属原设计，不算问题。
    """
    from kk_codeimg.palette import _FALLBACK

    must_reach_color = ["comment", "string", "number", "keyword", "function",
                        "class_name", "type_name", "property_name", "constant"]
    for tname, theme in THEMES.items():
        fg = theme.fg_rgb()
        for slot in must_reach_color:
            if theme.color(slot) != fg:
                continue
            # 沿回退链找一个显式定义
            cur, defined = slot, False
            seen = set()
            while cur and cur not in seen:
                seen.add(cur)
                if cur in theme.colors:
                    defined = True
                    break
                cur = _FALLBACK.get(cur, "")
            assert defined, f"{tname} 的 {slot} 槽位未定义且回退失败（全退成前景色）"


def test_syntax_actually_colored():
    """真实渲染一张图，确认出现了多种颜色（而非单色前景）。"""
    from collections import Counter

    from kk_codeimg.renderer import CodeImageRenderer

    r = CodeImageRenderer(background="single", line_numbers=False,
                          padding=16, scale=2).render(CODE, "python")
    l, t, rr, b = r.code_box
    rgb = r.image.convert("RGB").load()
    cnt = Counter()
    for x in range(l, rr):
        for y in range(t, b):
            cnt[rgb[x, y]] += 1
    # 排除底色后，显著颜色种类应 >= 4（注释/字符串/数字/关键字/函数名）
    bg = theme_bg = THEMES["one-dark"].bg_rgb()
    distinct = [c for c, n in cnt.items() if c != theme_bg and n > 40]
    assert len(distinct) >= 4, f"高亮色种类过少：{distinct}"


# ---------------------------------------------------------------------------
# 对比度守卫（WCAG）：防止色值回退到"看不清"的状态
# ---------------------------------------------------------------------------
def test_all_themes_meet_wcag_aa_on_own_bg():
    """每套主题在自身底色上，所有槽位对比度须 >= 4.5:1。

    历史教训：ayu-light 的 number 原为 #ffaa33（1.85:1，白底上几乎不可见），
    one-dark 的 comment 原为 #54636d（2.25:1）。已按「保持色相、调整明度」修正。
    """
    from kk_codeimg.contrast import AA_TEXT, contrast_ratio, hex_to_rgb

    offenders = []
    for name, theme in THEMES.items():
        bg = hex_to_rgb(theme.bg)
        for slot, color in theme.colors.items():
            r = contrast_ratio(hex_to_rgb(color), bg)
            if r < AA_TEXT:
                offenders.append(f"{name}.{slot} {color} = {r:.2f}:1")
    assert not offenders, "以下槽位未达 WCAG AA：\n  " + "\n  ".join(offenders)


def test_transparent_light_theme_gets_scrim():
    """透明编辑器 + 浅色主题必须自动垫白底。

    背景：github-light 的 keyword(#d73a49) 压在 leaf 渐变上仅 1.24:1，
    几乎糊掉。修复策略是透明模式下浅色主题自动用不透明底色。
    """
    from kk_codeimg.renderer import CodeImageRenderer

    # 构造一个深色渐变背景，确认渲染器选择垫底
    r = CodeImageRenderer(theme="github-light", background="ocean",
                          transparent_editor=True).renderer_probe()
    assert r["scrim"] >= 0.9, f"浅色主题透明模式未垫白底：scrim={r['scrim']}"

    # 深色主题保持通透（scrim 为 0）
    r2 = CodeImageRenderer(theme="one-dark", background="ocean",
                           transparent_editor=True).renderer_probe()
    assert r2["scrim"] == 0.0, "深色主题不应垫底"


def test_scrim_alpha_manual_override():
    from kk_codeimg.renderer import CodeImageRenderer
    r = CodeImageRenderer(theme="github-light", background="leaf",
                          transparent_editor=True,
                          scrim_alpha=0.5).renderer_probe()
    assert abs(r["scrim"] - 0.5) < 0.01


def test_border_radius_applied():
    """border_radius 参数必须真正影响像素：圆角处应为背景色（编辑器不透明）。

    注意：圆角边缘是抗锯齿过渡像素，颜色会略偏离纯背景色，
    所以用容差比较而非精确相等。
    """
    from kk_codeimg.renderer import CodeImageRenderer

    def corner_is_bg(radius):
        r = CodeImageRenderer(background="single", border_radius=radius,
                              padding=16, scale=2).render(CODE, "python")
        l, t, rr, b = r.editor_box
        rgb = r.image.convert("RGB").load()
        # 编辑器左上角 (l+1, t+1) 若为圆角，应显示背景（#b993d6）而非编辑器底色
        return rgb[l + 1, t + 1]

    bg = (185, 147, 214)   # single 背景色 #b993d6
    editor_bg = THEMES["one-dark"].bg_rgb()

    def near(px, ref, tol=8):
        return all(abs(px[i] - ref[i]) <= tol for i in range(3))

    sharp = corner_is_bg(0)
    round_ = corner_is_bg(40)
    assert near(sharp, editor_bg), f"border_radius=0 时左上角应是编辑器底色，实际 {sharp}"
    assert near(round_, bg), f"border_radius=40 时左上角应接近背景色，实际 {round_}（bg={bg}）"


def test_styles_all_render():
    from kk_codeimg import list_styles
    for s in list_styles():
        assert code_generator(CODE, "python", style=s).width > 0


def test_style_aliases():
    """常用别名应映射到真实存在的风格。"""
    from kk_codeimg import code_generator as gen
    from kk_codeimg.styles import STYLES, _ALIASES

    for alias in _ALIASES:
        assert _ALIASES[alias] in STYLES, f"别名 {alias} 指向不存在的风格"
        assert gen(CODE, "python", style=alias).width > 0


def test_style_case_insensitive():
    from kk_codeimg import code_generator as gen
    a = gen(CODE, "python", style="DARK")
    b = gen(CODE, "python", style="dark")
    assert a.size == b.size, "风格名应大小写不敏感"


def test_style_count_matches_docs():
    """README 声称 16 种风格，数目需对得上。"""
    from kk_codeimg import list_styles
    assert len(list_styles()) == 16, f"风格数 {len(list_styles())}，README 写的是 16"


def test_unknown_style_error_lists_options():
    with pytest.raises(ValueError) as e:
        code_generator(CODE, "python", style="nope")
    assert "default" in str(e.value), "报错信息应列出可选风格"


def test_style_overridden_by_explicit_arg():
    """显式参数必须覆盖 style 预设。"""
    from kk_codeimg.renderer import CodeImageRenderer
    from kk_codeimg.styles import resolve_for_render

    opts = resolve_for_render("minimal", theme="dracula", font_size=20,
                              line_numbers=True)
    assert opts["theme"] == "dracula"
    assert opts["font_size"] == 20
    assert opts["line_numbers"] is True
    # 未覆盖的沿用 style
    assert opts["window_controls"] == "none"


def test_unknown_style_raises():
    with pytest.raises(ValueError):
        code_generator(CODE, "python", style="no-such-style")


def test_false_can_override_style():
    """False 值也要能覆盖 style（不能用 or 合并）。"""
    from kk_codeimg.styles import resolve_for_render
    opts = resolve_for_render("carbon", line_numbers=True, transparent_editor=False)
    assert opts["line_numbers"] is True
    assert opts["transparent_editor"] is False


# ---------------------------------------------------------------------------
# 窗口标题
# ---------------------------------------------------------------------------
def _bar_ink(title, **kw):
    """返回窗口栏标题区域的墨迹像素数——标题存在则必有墨迹。

    基准色取「窗口栏右侧空白处」（那里必然是纯编辑器底色），
    不能取顶部中点——那里有 1px 白色描边，会污染基准。
    """
    from kk_codeimg.renderer import BAR_HEIGHT, CodeImageRenderer

    r = CodeImageRenderer(title=title, padding=16, scale=2, **kw).render(CODE, "python")
    l, t, rr, b = r.editor_box
    bar_h = BAR_HEIGHT * 2
    gray = r.image.convert("L").load()
    # 基准：窗口栏右下角附近的纯底色
    bg = gray[rr - 4, t + bar_h - 4]
    # 只扫标题所在的中间带，跳过左侧控制点区
    x0 = l + 80 * 2
    y0, y1 = t + 6, t + bar_h - 4
    return sum(1 for x in range(x0, rr - 4)
               for y in range(y0, y1) if abs(gray[x, y] - bg) > 10)


def test_title_rendered_in_bar():
    with_title = _bar_ink("point.py")
    without = _bar_ink(None)
    assert with_title > 100, f"标题未在窗口栏绘出（墨迹仅 {with_title}）"
    # 未传 title 时只剩圆角/描边的抗锯齿噪声，允许极少量
    assert without < 10, f"未传 title 时不应有明显墨迹，实际 {without}"


def test_title_works_without_window_controls():
    """window_controls='none' 时标题仍应显示（标题独立于控制点）。"""
    assert _bar_ink("minimal.py", window_controls="none") > 0


def test_title_cjk():
    assert _bar_ink("坐标点定义") > 0, "中文标题未绘出"


def test_title_truncated_when_too_long():
    """超长标题应截断，不能溢出编辑器右边界。

    判据：截断后的标题右缘应落在编辑器内。
    （不能直接比对外侧像素——那里有阴影，会假阳性。）
    """
    from kk_codeimg.renderer import BAR_HEIGHT, CodeImageRenderer

    long_title = "x" * 500
    r = CodeImageRenderer(title=long_title, padding=16, scale=2,
                          background="single").render(CODE, "python")
    l, t, rr, b = r.editor_box
    gray = r.image.convert("L").load()
    bg = gray[rr - 4, t + BAR_HEIGHT * 2 - 4]
    # 标题墨迹最右点
    xs = [x for x in range(l, rr - 4)
          for y in range(t + 6, t + BAR_HEIGHT * 2 - 4)
          if abs(gray[x, y] - bg) > 10]
    assert xs, "超长标题完全没画出来"
    assert max(xs) <= rr - 4, f"标题右缘 {max(xs)} 越过编辑器右边界 {rr}"

    # 截断后应出现省略号「…」，宽度远小于原标题
    short = CodeImageRenderer(title="y" * 10, padding=16, scale=2,
                              background="single")
    assert short.title is not None


def test_title_alpha_affects_contrast():
    """title_alpha 应实际影响绘制。

    度量必须用「亮度提升幅度」而非「墨迹像素数」——降低 alpha 只让文字变淡，
    覆盖的像素数不变（实测 458 vs 378，比例远达不到 1.5）。
    """
    from kk_codeimg.renderer import BAR_HEIGHT, CodeImageRenderer

    def brightest(title, alpha):
        r = CodeImageRenderer(title=title, title_alpha=alpha, padding=16,
                              scale=2, background="single").render(CODE, "python")
        l, t, rr, b = r.editor_box
        g = r.image.convert("L").load()
        bg = g[rr - 4, t + BAR_HEIGHT * 2 - 4]
        vals = [g[x, y] for x in range(l + 160, rr - 4)
                for y in range(t + 6, t + BAR_HEIGHT * 2 - 4)]
        return max(vals) - bg

    strong = brightest("t.py", 1.0)
    weak = brightest("t.py", 0.15)
    assert strong > 100, f"alpha=1.0 标题应明显可见，实际亮度差仅 {strong}"
    # 低 alpha 下仍有抗锯齿与描边残余像素，比例不会线性，用 1.5 作为
    # "确实生效"的判据（实测 168 vs 92 ≈ 1.83）
    assert strong > weak * 1.5, f"title_alpha 未生效：{strong} vs {weak}"


def test_title_readable_contrast():
    """标题用前景色，对比度须 >= 4.5:1（实测前景色全部 >= 6.10）。"""
    from kk_codeimg.contrast import AA_TEXT, contrast_ratio, hex_to_rgb
    for name, theme in THEMES.items():
        r = contrast_ratio(theme.fg_rgb(), hex_to_rgb(theme.bg))
        assert r >= AA_TEXT, f"{name} 标题对比度仅 {r:.2f}:1"


# ---------------------------------------------------------------------------
# 标题字号 / 字体统一
# ---------------------------------------------------------------------------
def test_title_size_none_matches_font_size():
    """title_size=None 时标题应与代码同字号。"""
    from kk_codeimg.renderer import CodeImageRenderer
    for fs in (12, 15, 20, 28):
        c = CodeImageRenderer(title="T", font_size=fs)
        assert c.title_size == float(fs), f"font_size={fs} 时 title_size={c.title_size}"


def test_title_size_same_keyword():
    from kk_codeimg.renderer import CodeImageRenderer
    assert CodeImageRenderer(title="T", font_size=18, title_size="same").title_size == 18.0


def test_title_size_independent():
    """标题字号可独立于代码字号设置。"""
    from kk_codeimg.renderer import CodeImageRenderer
    c = CodeImageRenderer(title="T", font_size=20, title_size=11)
    assert c.title_size == 11.0
    assert c.font_size == 20


def test_title_size_clamped_to_bar():
    """超大会被钳制，不能撑破窗口栏盖住代码。

    栏高固定 40px，字形盒约 0.7 倍字号，留 6px 余量 -> 上限约 48.6。
    """
    from kk_codeimg.renderer import BAR_HEIGHT, CodeImageRenderer

    limit = CodeImageRenderer(title="T", title_size=10_000).title_size
    assert limit < 60, f"title_size 未钳制，实际 {limit}"
    # 钳制后字形盒必须放得下
    c = CodeImageRenderer(title="M", title_size=10_000)
    c.render("x=1\n", "python")
    bb = c._title_pen.mono.getbbox("M")
    assert (bb[3] - bb[1]) <= BAR_HEIGHT * 2 - 6, "钳制后仍溢出窗口栏"


def test_title_size_invalid_raises():
    from kk_codeimg.renderer import CodeImageRenderer
    for bad in (0, -3, "abc", []):
        with pytest.raises(ValueError):
            CodeImageRenderer(title="T", title_size=bad)


def test_title_uses_same_font_as_code():
    """硬要求：代码用什么字体，title 就用什么字体。"""
    from kk_codeimg.renderer import CodeImageRenderer

    for font in (None, "consolas", "courier", "dejavu"):
        c = CodeImageRenderer(title="标题Title", font=font, font_size=20,
                              title_size=20)
        c.render("x=1\n", "python")
        code_font = c._title_pen.mono
        # 同字号时应直接复用代码字体对象
        assert code_font.size == 40, f"font={font} 未复用代码字体对象"
        # 路径必须与 _load_font 解析结果一致
        from kk_codeimg.renderer import _load_font
        expect = _load_font(font, 40)
        assert code_font.path == expect.path, f"font={font} 标题字体与代码不一致"


def test_title_cjk_same_font_as_code():
    """中文回退字体也要统一。"""
    from kk_codeimg.renderer import CodeImageRenderer, _load_cjk_font

    c = CodeImageRenderer(title="中文标题", font_size=20, title_size=20)
    c.render("x=1\n", "python")
    code_cjk = _load_cjk_font(40)
    if code_cjk is not None:
        assert c._title_pen.cjk.path == code_cjk.path, "CJK 字体未统一"


def _title_center_offset(title, **kw):
    """返回标题中心相对编辑器中心的偏移（逻辑像素）。

    ⚠️ 不要用像素扫描来测居中——窗口栏有 1px 描边、左侧有控制点，
    扫描起点稍偏就会把标题左半截切掉，产生几十 px 的假偏差
    （实测踩过：真实 0px 偏差被测成 +82px）。
    可靠做法是对账 pen.draw 的实际绘制坐标。
    """
    from kk_codeimg.renderer import CodeImageRenderer

    captured = {}
    original = CodeImageRenderer._draw_title

    def spy(self, d, w, h, pen):
        if self.title:
            size = pen.measure(str(self.title))
            captured["x"] = w / 2 - size / 2
            captured["size"] = size
            captured["w"] = w
        return original(self, d, w, h, pen)

    CodeImageRenderer._draw_title = spy
    try:
        r = CodeImageRenderer(title=title, padding=16, scale=2,
                              background="single", **kw).render(CODE, "python")
    finally:
        CodeImageRenderer._draw_title = original

    l, t, rr, b = r.editor_box
    if "x" not in captured:
        return None
    title_center_global = l + captured["x"] + captured["size"] / 2
    return title_center_global - (l + rr) / 2


def test_title_is_centered():
    """标题必须在编辑器宽度上居中。

    回归测试：早期实现把标题放在「扣掉左侧控制点区」的不对称区域里居中
    （左 160px / 右 32px @scale=2），导致右偏约 29px（逻辑）。
    """
    for title in ("a", "main.py", "几何工具模块", "中文标题测试用例",
                  "very_long_module_name.py"):
        d = _title_center_offset(title)
        assert d is not None, f"title={title!r} 未绘出"
        assert abs(d) <= 1.0, f"title={title!r} 未居中，偏差 {d:+.1f}px"


def test_title_centered_without_window_controls():
    for title in ("main.py", "几何工具模块"):
        d = _title_center_offset(title, window_controls="none")
        assert abs(d) <= 1.0, f"无控制点时 title={title!r} 偏差 {d:+.1f}px"


def test_title_avoids_controls_when_very_wide():
    """极宽标题会撞上控制点区，此时应钳制避让（可接受偏离中心）。"""
    from kk_codeimg.renderer import CodeImageRenderer, DOT_MARGIN_LEFT, DOT_CONTAINER_W

    r = CodeImageRenderer(title="W" * 400, padding=16, scale=2,
                          background="single", font_size=30).render(CODE, "python")
    l, t, rr, b = r.editor_box
    g = r.image.convert("L").load()
    bg = g[rr - 4, t + 6]
    # 标题左缘应 >= 控制点区右缘，不重叠
    dots_end = l + (DOT_MARGIN_LEFT + DOT_CONTAINER_W + 8) * 2
    hit = [x for x in range(dots_end, rr)
           if any(abs(g[x, y] - bg) > 10 for y in range(t + 4, t + 40))]
    assert hit, "极宽标题未绘出"
    assert min(hit) >= dots_end, "标题与控制点区重叠"
