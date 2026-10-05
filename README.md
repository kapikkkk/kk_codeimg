# kk_codeimg

<p align="center">
  <b>🌟【Python卡皮巴拉】—— 你的Python修炼秘籍，代码界的"神兽"驾到！🌟</b>
</p>

<p align="center">
  <b>🌟 [Python Capybara] — Your Python cultivation manual; the coding realm's "mythical beast" has arrived! 🌟</b>
</p>

<p align="center">
  <a href="#中文">🇨🇳 中文</a> · <a href="#english">🇬🇧 English</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/kk_codeimg/"><img src="https://img.shields.io/pypi/v/kk_codeimg.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/kk_codeimg/"><img src="https://img.shields.io/pypi/l/kk_codeimg.svg" alt="License"></a>
  <a href="https://pypi.org/project/kk_codeimg/"><img src="https://img.shields.io/pypi/pyversions/kk_codeimg.svg" alt="Python versions"></a>
</p>

---

<a name="中文"></a>

## 中文

把代码渲染成精美的代码图片。纯 Python（`Pillow` + `Pygments`），
**离线运行**，不依赖浏览器、不启动 headless Chrome、不联网。

### 特点

- 🎨 **12 套主题** —— 全部通过 WCAG AA 对比度校验，不是"看着差不多"
- 🖼️ **16 种预设风格** —— 一行代码切换整套视觉配置
- 🏷️ **窗口标题** —— 显示文件名，支持中文，字体与代码自动统一
- 🇨🇳 **中英文混排** —— 等宽字体没有中文字形？自动回退到系统 CJK 字体
- 🔒 **对比度达标** —— 按 WCAG 标准实算，注释不再"灰到看不见"
- 🐍 **纯离线** —— CI 里也能跑，不发起任何网络请求
- 🪶 **零重型依赖** —— 只用 `Pillow` + `Pygments`
- 🧩 **主题可扩展** —— 加一套主题只需往 `palette.py` 里加一组色值

### 安装

```bash
pip install kk_codeimg
```

### 快速开始

```python
from kk_codeimg import code_generator

code_generator(code, 'python', output='out.png')
```

不传 `output` 时返回 `PIL.Image.Image`，可自行 `.save()` 或做后处理。

### 效果预览

<table>
<tr>
<td width="50%"><img src="docs/preview-dark.png" alt="深色主题 + 窗口标题"></td>
<td width="50%"><img src="docs/preview-light.png" alt="浅色主题"></td>
</tr>
<tr>
<td align="center"><sub>One Dark + 渐变背景（默认）</sub></td>
<td align="center"><sub>GitHub Light 浅色主题</sub></td>
</tr>
<tr>
<td><img src="docs/preview-neon.png" alt="neon 风格"></td>
<td><img src="docs/preview-ocean.png" alt="ocean 风格"></td>
</tr>
<tr>
<td align="center"><sub><code>style='neon'</code> 大圆角霓虹</sub></td>
<td align="center"><sub><code>style='ocean'</code> 冷色克制</sub></td>
</tr>
<tr>
<td><img src="docs/preview-sticker.png" alt="sticker 风格"></td>
<td><img src="docs/preview-grid.png" alt="grid 风格"></td>
</tr>
<tr>
<td align="center"><sub><code>style='sticker'</code> 贴纸风大圆角</sub></td>
<td align="center"><sub><code>style='grid'</code> 零圆角网格纸</sub></td>
</tr>
</table>

生成全套样图：

```bash
python scripts/make_samples.py   # 输出到 out/
```

### 预设风格

不想逐个记参数就用 `style`，一次套用一整套视觉配置：

```python
code_generator(code, 'python', style='tokyo', output='out.png')
```

| 风格 | 说明 |
|---|---|
| `default` | 深色经典：One Dark 主题 + 柔和渐变 |
| `carbon` | 极简纯色底、无窗口控制点、方正小圆角 |
| `dracula` | Dracula 紫调 + 极光渐变 |
| `tokyo` | Tokyo Night 夜色 + 深海渐变 |
| `github` | GitHub 浅色 + 淡雅渐变（不透明底，可读性最佳） |
| `light-frosted` | 浅色磨砂：保留渐变氛围但垫白底，深字清晰 |
| `frosted` | 深色磨砂玻璃：大圆角，背景隐约透出 |
| `minimal` | 极简：无行号、无控制点、大留白 |
| `neon` | 霓虹酷炫：Cool Glow + 大圆角 |
| `share` | 社交分享：大字号、大圆角、宽留白 |
| `print` | 打印友好：白底黑字、无干扰 |
| `ocean` | 深海蓝：冷色调、克制圆角 |
| `sunset` | 日落暖橙：亮色系、适合长代码 |
| `forest` | 森林绿：护眼低饱和 |
| `grid` | 网格纸：零圆角、细边框控制点、代码排版感 |
| `sticker` | 贴纸风：浅色、夸张圆角、紧凑 |

还有一批顺手加的**别名**，记不住名字也能用：
`dark` / `light` / `plain` / `classic` / `night` / `big` / `rounded` / `sharp` / `matrix` / `frost`

```python
code_generator(code, 'python', style='dark')    # 等同 default
code_generator(code, 'python', style='plain')   # 等同 minimal
```

显式传入的参数**优先级高于** `style`：

```python
# style 提供预设，再用 theme 覆盖其中一项
code_generator(code, 'python', style='minimal', theme='dracula')
```

### 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `code` | 必填 | 代码文本 |
| `language` | `'python'` | Pygments 语言名：`python` / `javascript` / `sql` / `java` / `go`… |
| `output` | `None` | PNG 路径；`None` 则只返回 Image |
| `style` | `None` | 预设风格名，见上表 |
| `theme` | 随 style | 12 套主题，见下表 |
| `background` | 随 style | 渐变名 / `single` / `transparent` / 任意 `#hex` |
| `font` | `None` | 字体名或 `.ttf` 路径；`None` 自动探测 |
| `font_size` | `15` | 字号（逻辑像素） |
| `border_radius` | `9` | 编辑器圆角 |
| `window_controls` | `'color'` | `color` / `gray` / `gray-light` / `outline` / `none` |
| `line_height` | `1.45` | 行高倍数 |
| `padding` | `64` | 图片四周留白 |
| `line_numbers` | `True` | 是否显示行号 |
| `transparent_editor` | `False` | 编辑器区域透明 |
| `scrim_alpha` | `None` | 透明模式下的底色不透明度 `0~1`；`None` 时按主题明暗自动决定 |
| `title` | `None` | 窗口标题，显示在窗口栏居中，支持中文 |
| `title_alpha` | `0.72` | 标题不透明度，调低可让标题退居次要 |
| `title_size` | `None` | 标题字号。`None`/`'same'` = 与代码同字号；传数字则单独指定 |
| `scale` | `2` | 渲染倍率，`2` 适合高清分享 |

传了 `output` 时返回 `RenderResult`，带 `.image`、`.path`、`.editor_box`、`.code_box`。

### 窗口标题

`title` 显示在窗口栏居中位置：

```python
code_generator(code, 'python', title='point.py', output='out.png')
code_generator(code, 'python', title='几何工具 · 坐标计算', output='out.png')  # 支持中文
```

**字体始终与代码一致**，只有字号可以不同：

```python
# 标题与代码同字号同字体（默认）
code_generator(code, 'python', title='main.py')

# 标题小一号
code_generator(code, 'python', title='main.py', font_size=20, title_size=13)

# 换个字体，标题自动跟随
code_generator(code, 'python', title='main.py', font='consolas')
```

细节：

- 字体统一是硬约束——代码用什么字体，标题就用同一个字体文件
  （同字号时直接复用同一个字体对象）；中文回退字体同样统一
- `title_size` 超过窗口栏容量（40px 栏高，约 48.6px 上限）会**自动钳制**，
  不会出现标题盖住代码的情况；`0` / 负数 / 非数字会抛 `ValueError`
- 超长标题自动截断加省略号，不溢出窗口
- `window_controls='none'` 时标题仍然显示（标题独立于控制点）
- 配色用主题**前景色**而非行号色——实测行号色在部分主题上对比度仅 2.76:1，
  前景色全部 ≥ 6.10:1
- 标题在**整个编辑器宽度上居中**

### 主题（12 套）

`one-dark`（默认）、`dracula`、`vscode`、`ayu-light`、`github-light`、
`github-dark`、`tokyo-night`、`xcode-dark`、`xcode-light`、`amy`、`aura`、`cool-glow`

```python
code_generator(code, 'python', output='a.png', theme='dracula', background='aurora')
```

### 背景

10 套渐变：`mystic`（默认）、`aruba`、`jungle`、`tropical`、`aurora`、`candy`、
`peach`、`bananas`、`leaf`、`ocean`

外加 `single`（单色）、`transparent`（透明）、以及任意 `#hex` 值：

```python
code_generator(code, 'python', output='a.png', background='#1d976c')
```

### 完整示例

```python
from kk_codeimg import code_generator

code = '''def greet(name: str) -> str:
    # 生成问候语
    return f"Hello, {name}!"
'''

# 默认风格
code_generator(code, 'python', output='out.png')

# 换主题与背景
code_generator(code, 'python', output='dracula.png',
               theme='dracula', background='ocean')

# 带窗口标题
code_generator(code, 'python', output='titled.png', title='greet.py')

# 浅色主题 + 无行号
code_generator(code, 'python', output='light.png',
               theme='github-light', background='leaf', line_numbers=False)

# 不落盘，直接拿 Image 做后处理
img = code_generator(code, 'python', font_size=18)
```

### 设计说明

**对比度是算出来的，不是看出来的。** 早期直接采用现成配色，实测发现一批槽位
达不到 WCAG AA 标准（4.5:1），实际观感问题例如：

- 某浅色主题的 `number` 仅 **1.85:1** —— 白底上几乎看不见
- 某深色主题的 `comment` 仅 **2.25:1** —— 注释难以辨认

修正方式是**保持色相与饱和度、只调整明度**，直到达到 4.5:1，观感不跑偏。
现 12 套主题全部达标（最差 4.50:1，最好 6.74:1）。`kk_codeimg/contrast.py`
提供 WCAG 计算与评估工具，`test_all_themes_meet_wcag_aa_on_own_bg` 做回归守卫。

原主题未定义的槽位（如 Xcode 系列的数字/运算符）按其编辑器默认配色补齐，
并配 `_FALLBACK` 语义回退链，避免整片 token 退化成前景色。

**透明模式下的可读性**：浅色主题（深色文字）若抽掉底色直接压到饱和背景上，
文字会糊掉——实测某组合仅 **1.24:1**。因此透明模式下浅色主题会自动垫一层
不透明底色（磨砂效果，背景氛围仍在）。深色主题文字本身够亮，保持全透明。
手动控制用 `scrim_alpha`（0~1）。

**中英文混排**：等宽字体普遍无中文字形，`_TextPen` 会按字符切分，
CJK 交给系统 CJK 字体（微软雅黑 / Noto Sans SC 等）绘制并按全角宽度计算 advance。

**字体**：默认按 `Cascadia Mono`（SIL OFL 1.1）→ `JetBrains Mono`（OFL 1.1）→
`DejaVu Sans Mono`（Bitstream Vera）顺序探测，**均为免费商用字体**。

**圆角**：编辑器圆角通过 alpha 遮罩真实生效（不是只改描边），可用
`border_radius` 自由调整，`0` 即直角。

### 测试

```bash
python -m pytest scripts/test_codepng.py -q
```

47 项测试，覆盖缩进保留、中文出字、12 主题 / 12 背景 / 16 风格 / 10 别名渲染、
**WCAG 对比度守卫**、透明模式垫底、圆角生效、槽位退化防护、参数覆盖优先级、
窗口标题（中文/截断/无控制点/透明度/字号独立/字体统一/居中）、多语言、异常输入等。

### 已知限制

- 超长单行不自动换行（长代码建议调大 `font_size` 或分屏）
- 粗体/斜体未实现，部分主题原设计里关键字是加粗的
- 透明模式 + 浅色主题时，背景渐变基本透不出来（实测需 100% 不透明才达 AA），
  想要通透感建议用深色主题配 `style='frosted'`

### 发布

见 [`PUBLISH.md`](PUBLISH.md)。

### 许可证

[MIT](LICENSE) © 2026 Python卡皮巴拉

---

<a name="english"></a>

## English

Turn your code into beautiful, share-ready code images.
Pure Python (`Pillow` + `Pygments`) — **fully offline**: no browser, no headless
Chrome, no network calls.

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

<table>
<tr>
<td width="50%"><img src="docs/preview-dark.png" alt="Dark theme with window title"></td>
<td width="50%"><img src="docs/preview-light.png" alt="Light theme"></td>
</tr>
<tr>
<td align="center"><sub>One Dark + gradient (default)</sub></td>
<td align="center"><sub>GitHub Light theme</sub></td>
</tr>
<tr>
<td><img src="docs/preview-neon.png" alt="neon style"></td>
<td><img src="docs/preview-ocean.png" alt="ocean style"></td>
</tr>
<tr>
<td align="center"><sub><code>style='neon'</code> — large radius, neon</sub></td>
<td align="center"><sub><code>style='ocean'</code> — cool, restrained</sub></td>
</tr>
<tr>
<td><img src="docs/preview-sticker.png" alt="sticker style"></td>
<td><img src="docs/preview-grid.png" alt="grid style"></td>
</tr>
<tr>
<td align="center"><sub><code>style='sticker'</code> — big rounded corners</sub></td>
<td align="center"><sub><code>style='grid'</code> — square, monospace feel</sub></td>
</tr>
</table>

Generate the full sample set:

```bash
python scripts/make_samples.py   # writes to out/
```

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
python -m pytest scripts/test_codepng.py -q
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
