English | [简体中文](docs/README.zh-CN.md)

# kk_codeimg

**🌟【Python卡皮巴拉】—— 你的Python修炼秘籍，代码界的"神兽"驾到！🌟**

**🌟 [Python Capybara] — Your Python cultivation manual; the coding realm's "mythical beast" has arrived! 🌟**

[PyPI](https://pypi.org/project/kk_codeimg/) · [MIT License](LICENSE) · [Python 3.8+](https://pypi.org/project/kk_codeimg/)


---

Turn your code into beautiful, share-ready code images.
Pure Python (`Pillow` + `Pygments`) — **fully offline**: no browser, no headless
Chrome, no network calls.

## English

### Features

- 🎨 **12 themes** — every one verified against WCAG AA contrast, not "close enough"
- 🖼️ **16 preset styles** — switch an entire look with a single argument
- 🏷️ **Window title** — file name in the title bar, CJK-ready, font always
  matches the code
- 🇨🇳 **Mixed CJK + Latin** — monospace fonts lack Chinese glyphs? We fall back
  to a system CJK font automatically
- 🔒 **Accessible by default** — contrast ratios are *computed*, so comments
  are never too faint to read
- 🐍 **100% offline** — no network requests, so it works in CI
- 🪶 **Light dependencies** — just `Pillow` + `Pygments`
- 🧩 **Extensible** — adding a theme means adding one dict of colours

### Installation

```bash
pip install kk_codeimg
```

### Quick start

```python
from kk_codeimg import code_generator

code_generator(code, 'python', output='out.png')
```

Without `output`, a `PIL.Image.Image` is returned so you can post-process it yourself.

### Preview

**One Dark theme + gradient (default `default`)**

![One Dark theme + gradient (default `default`)](docs/preview-dark.png)

**GitHub Light theme (`github`)**

![GitHub Light theme (`github`)](docs/preview-light.png)

**`neon`: large radius + Cool Glow**

![`neon`: large radius + Cool Glow](docs/preview-neon.png)

**`ocean`: cool and restrained**

![`ocean`: cool and restrained](docs/preview-ocean.png)

**`sticker`: exaggerated radius**

![`sticker`: exaggerated radius](docs/preview-sticker.png)

**`grid`: square grid paper**

![`grid`: square grid paper](docs/preview-grid.png)

Generate the full sample set:/n/n```bash
python scripts/make_samples.py
```

Writes to `out/`.

### Preset styles

Don't want to memorise parameters? Use `style` to apply a whole look at once:

```python
code_generator(code, 'python', style='tokyo', output='out.png')
```

| Style | Description |
|---|---|
| `default` | Dark classic: One Dark theme with a soft gradient |
| `carbon` | Minimal solid background, no window controls, small radius |
| `dracula` | Dracula purple tones with an aurora gradient |
| `tokyo` | Tokyo Night on a deep-ocean gradient |
| `github` | GitHub Light on a soft gradient (opaque, most readable) |
| `light-frosted` | Light frosted glass: keeps the ambience, adds a white base for legibility |
| `frosted` | Dark frosted glass: large radius, background softly shows through |
| `minimal` | Minimal: no line numbers, no window controls, generous padding |
| `neon` | Neon: Cool Glow theme with a large corner radius |
| `share` | Social sharing: large font, large radius, wide padding |
| `print` | Print-friendly: black on white, no distractions |
| `ocean` | Deep ocean: cool tones, restrained radius |
| `sunset` | Sunset: warm and bright, good for long snippets |
| `forest` | Forest: low-saturation greens, easy on the eyes |
| `grid` | Grid paper: square corners, outlined controls, typographic feel |
| `sticker` | Sticker: light background, exaggerated radius, compact |

Handy **aliases** so you don't have to memorise exact names:
`dark` / `light` / `plain` / `classic` / `night` / `big` / `rounded` / `sharp` / `matrix` / `frost`

```python
code_generator(code, 'python', style='dark')    # same as default
code_generator(code, 'python', style='plain')   # same as minimal
```

Explicit arguments always **override** `style`:

```python
code_generator(code, 'python', style='minimal', theme='dracula')
```

### Parameters

| Parameter | Default | Description |
|---|---|---|
| `code` | required | Source code text |
| `language` | `'python'` | Pygments lexer name: `python` / `javascript` / `sql` / `java` / `go`… |
| `output` | `None` | Path to save the PNG; `None` returns the Image instead |
| `style` | `None` | Preset style name (see table above) |
| `theme` | follows `style` | One of 12 themes (see below) |
| `background` | follows `style` | Gradient name / `single` / `transparent` / any `#hex` |
| `font` | `None` | Font name or `.ttf` path; auto-detected when `None` |
| `font_size` | `15` | Font size (logical pixels) |
| `border_radius` | `9` | Editor corner radius |
| `window_controls` | `'color'` | `color` / `gray` / `gray-light` / `outline` / `none` |
| `line_height` | `1.45` | Line height multiplier |
| `padding` | `64` | Outer margin |
| `line_numbers` | `True` | Show line numbers |
| `transparent_editor` | `False` | Make the editor area transparent |
| `scrim_alpha` | `None` | Base opacity (`0`–`1`) in transparent mode; auto-decided from theme brightness when `None` |
| `title` | `None` | Window title, centred in the title bar; CJK supported |
| `title_alpha` | `0.72` | Title opacity — lower it to make the title recede |
| `title_size` | `None` | Title font size. `None`/`'same'` = same as code; pass a number to set it independently |
| `scale` | `2` | Render scale; `2` is good for sharing |

When `output` is given, a `RenderResult` is returned with `.image`, `.path`,
`.editor_box` and `.code_box`.

### Window title

`title` renders in the centre of the title bar:

```python
code_generator(code, 'python', title='point.py', output='out.png')
code_generator(code, 'python', title='几何工具 · 坐标计算', output='out.png')  # CJK OK
```

**The font always matches the code** — only the size may differ:

```python
# Same font, same size (default)
code_generator(code, 'python', title='main.py')

# Smaller title
code_generator(code, 'python', title='main.py', font_size=20, title_size=13)

# Change the font — the title follows automatically
code_generator(code, 'python', title='main.py', font='consolas')
```

Details:

- Font unification is a hard constraint — whatever the code uses, the title uses
  the exact same font file (the very same font object when sizes match); the CJK
  fallback is unified too
- A `title_size` larger than the title bar can hold (40 px bar, ~48.6 px limit)
  is **clamped automatically**, so the title never covers the code;
  `0` / negative / non-numeric values raise `ValueError`
- Overlong titles are truncated with an ellipsis and never overflow
- The title still shows when `window_controls='none'`
- Colours come from the theme's **foreground**, not the gutter colour — the
  gutter measures only 2.76:1 on some themes, while every foreground is ≥ 6.10:1
- The title is centred across the **entire editor width**

### Themes (12)

`one-dark` (default), `dracula`, `vscode`, `ayu-light`, `github-light`,
`github-dark`, `tokyo-night`, `xcode-dark`, `xcode-light`, `amy`, `aura`,
`cool-glow`

```python
code_generator(code, 'python', output='a.png', theme='dracula', background='aurora')
```

### Backgrounds

10 gradients: `mystic` (default), `aruba`, `jungle`, `tropical`, `aurora`,
`candy`, `peach`, `bananas`, `leaf`, `ocean`

Plus `single` (solid), `transparent`, and any `#hex` value:

```python
code_generator(code, 'python', output='a.png', background='#1d976c')
```

### Full example

```python
from kk_codeimg import code_generator

code = '''def greet(name: str) -> str:
    # say hello
    return f"Hello, {name}!"
'''

# Default look
code_generator(code, 'python', output='out.png')

# Different theme and background
code_generator(code, 'python', output='dracula.png',
               theme='dracula', background='ocean')

# With a window title
code_generator(code, 'python', output='titled.png', title='greet.py')

# Light theme without line numbers
code_generator(code, 'python', output='light.png',
               theme='github-light', background='leaf', line_numbers=False)

# No file written — grab the Image and post-process it
img = code_generator(code, 'python', font_size=18)
```

### Design notes

**Contrast is computed, not eyeballed.** Early on we shipped off-the-shelf
palettes, then measured them and found a number of slots below WCAG AA (4.5:1):

- one light theme's `number` measured only **1.85:1** — effectively invisible
- one dark theme's `comment` measured only **2.25:1** — hard to read

The fix keeps **hue and saturation, adjusting only lightness** until 4.5:1 is
reached, so each palette still looks like itself. All 12 themes now pass (worst
4.50:1, best 6.74:1). `kk_codeimg/contrast.py` provides the WCAG maths and
`test_all_themes_meet_wcag_aa_on_own_bg` guards against regressions.

Slots the original themes never defined (e.g. numbers and operators in the Xcode
family) are filled in from those editors' own defaults, plus a `_FALLBACK`
semantic chain so whole regions never collapse to the foreground colour.

**Readability in transparent mode**: a light theme (dark text) loses its
background and lands directly on a saturated gradient — one combination measured
only **1.24:1**. So in transparent mode light themes automatically get an opaque
base (a frosted effect that keeps the ambience). Dark themes stay fully
transparent. Override with `scrim_alpha` (0–1).

**Mixed CJK + Latin**: monospace fonts rarely carry Chinese glyphs, so
`_TextPen` splits runs per character and hands CJK to a system CJK font
(Microsoft YaHei / Noto Sans SC, …), advancing by full-width metrics.

**Fonts**: probed in the order `Cascadia Mono` (SIL OFL 1.1) → `JetBrains Mono`
(OFL 1.1) → `DejaVu Sans Mono` (Bitstream Vera) — **all free for commercial use**.

**Corner radius** is applied through a real alpha mask (not just the outline),
so `border_radius=0` gives you genuinely square corners.

### Tests

```bash
python -m pytest scripts/test_kk_codeimg.py -q
```

47 tests covering indentation preservation, CJK rendering, all 12 themes /
12 backgrounds / 16 styles, **WCAG contrast guards**, transparent-mode base
fill, corner radius, slot-collapse prevention, parameter override precedence,
window titles (CJK / truncation / no controls / opacity / independent size /
unified font / centring), multiple languages and invalid input.

### Known limitations

- Very long single lines are not wrapped (try a larger `font_size` or split the
  snippet)
- Bold/italic are not implemented; some original themes bold their keywords
- In transparent mode a light theme hides the gradient almost completely
  (measured: 100% opacity is required to reach AA). For a translucent look,
  use a dark theme with `style='frosted'`

### License

[MIT](LICENSE) © 2026 Python Capybara
