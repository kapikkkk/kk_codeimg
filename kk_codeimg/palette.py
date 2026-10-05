"""配色预设。

色值取自社区公开的编辑器主题方案（MIT / CC 授权），
并在此基础上按 WCAG 对比度标准做了修正，非目测近似。
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


def _hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """'#rrggbb' / '#rgb' -> (r, g, b)；也接受 'rgb(r,g,b)'。"""
    value = value.strip()
    if value.startswith("rgb"):
        inner = value[value.index("(") + 1:value.rindex(")")]
        parts = [p for p in inner.replace("/", ",").split(",") if p.strip()]
        out = []
        for p in parts[:3]:
            p = p.strip()
            out.append(int(float(p[: p.index("%")]) * 255 / 100) if "%" in p else int(float(p)))
        return tuple(out)  # type: ignore[return-value]
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i: i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _hsl_to_rgb(h: int, s: int, l: int) -> Tuple[int, int, int]:
    """部分主题用了 hsl(...) 字面量，这里做等价换算。"""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return round(r * 255), round(g * 255), round(b * 255)


# --------------------------------------------------------------------------
# 语义 token：把 CodeMirror 的 tag 体系收敛成 Pygments 能映射的一套 key
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Theme:
    name: str
    dark: bool
    bg: str
    fg: str
    gutter: str
    # 语义槽位 -> CSS 颜色（hsl 字面量已预先换算成 hex）
    colors: Dict[str, str] = field(default_factory=dict)

    def bg_rgb(self) -> Tuple[int, int, int]:
        return _hex_to_rgb(self.bg)

    def fg_rgb(self) -> Tuple[int, int, int]:
        return _hex_to_rgb(self.fg)

    def gutter_rgb(self) -> Tuple[int, int, int]:
        return _hex_to_rgb(self.gutter)

    def color(self, slot: str) -> Tuple[int, int, int]:
        """取槽位颜色。

        并非每套主题都定义了全部槽位（如 Xcode 系列只定义了 7 个），
        缺槽时按语义近邻回退，避免整片 token 退化成前景色（看起来像没高亮）。
        """
        seen = set()
        cur = slot
        while cur and cur not in seen:
            seen.add(cur)
            v = self.colors.get(cur)
            if v:
                return _hex_to_rgb(v)
            cur = _FALLBACK.get(cur, "")
        return _hex_to_rgb(self.fg)


# 槽位缺失时的语义回退链：左列缺了就用右列的值。
# 依据 CodeMirror 默认高亮语义（keyword/name/string/number/comment 五大类）。
_FALLBACK = {
    "module_keyword": "keyword",
    "definition_keyword": "keyword",
    "definition_variable": "variable_name",
    "definition_type": "type_name",
    "definition_property": "property_name",
    "control_keyword": "keyword",
    "operator_keyword": "keyword",
    "type_name": "class_name",
    "class_name": "type_name",
    "namespace": "class_name",
    "tag_name": "class_name",
    "label_name": "name",
    "name": "variable_name",
    "variable_name": "name",
    "property_name": "attribute_name",
    "attribute_name": "property_name",
    "constant": "number",
    "bool": "number",
    "null": "number",
    "modifier": "keyword",
    "meta": "comment",
    "invalid": "comment",
    "function": "name",
    "angle_bracket": "punctuation",
    "punctuation": "operator",
    "separator": "punctuation",
    "brace": "string",
    "quote": "string",
    "regexp": "string",
    "link": "string",
    "special_property": "string",
    "special_brace": "string",
    "atom": "constant",
    "bracket": "punctuation",
    "heading": "keyword",
    "deleted": "invalid",
    "character": "string",
    "macro_name": "string",
    "annotation": "comment",
    "changed": "number",
    "color": "constant",
    "self": "keyword",
    "deref_operator": "operator",
    "square_bracket": "punctuation",
    "process_instruction": "string",
    "inserted": "string",
}


def _t(name, dark, bg, fg, gutter, colors) -> Theme:
    return Theme(name, dark, bg, fg, gutter, colors)


# 12 套主题，字段与各编辑器的 CodeMirror styles 数组一一对应
THEMES: Dict[str, Theme] = {
    "dracula": _t(
        "Dracula", True, "#282a36", "#f8f8f2", "#7d8799",
        {
            # comment 原为 #6272a4（对比度 3.03），提亮至 #8390b7 达 AA
            "comment": "#8390b7", "string": "#f1fa8c", "brace": "#f1fa8c",
            "number": "#bd93f9", "bool": "#bd93f9", "null": "#bd93f9",
            "keyword": "#ff79c6", "operator": "#ff79c6",
            "definition_keyword": "#8be9fd", "type_name": "#8be9fd",
            "definition_type": "#f8f8f2", "class_name": "#50fa7b",
            "function": "#50fa7b", "attribute_name": "#50fa7b",
        },
    ),
    "one-dark": _t(
        "One Dark", True, "#282c34", "#d4d4d4", "#7d8799",
        {
            "function": "#61afef", "tag_name": "#e17078", "heading": "#e17078",
            "operator": "#d4d4d4", "punctuation": "#d4d4d4", "regexp": "#d4d4d4",
            # comment 原为 #54636d（对比度仅 2.25，注释几乎不可读），提亮至 #8495a0
            "comment": "#8495a0", "property_name": "#abb2bf",  # hsl(220,14%,71%)
            "attribute_name": "#d19a66", "number": "#d19a66",  # hsl(29,54%,61%)
            "class_name": "#e5c07b", "keyword": "#c678dd",      # hsl(39/286,...)
            "string": "#98c379", "special_property": "#98c379",
        },
    ),
    "vscode": _t(
        "VS Code", True, "#1e1e1e", "#9cdcfe", "#838383",
        {
            "keyword": "#569cd6", "operator_keyword": "#569cd6", "modifier": "#569cd6",
            "constant": "#569cd6", "bool": "#569cd6", "special_brace": "#569cd6",
            "control_keyword": "#c586c0", "module_keyword": "#c586c0",
            "name": "#9cdcfe", "property_name": "#9cdcfe", "variable_name": "#9cdcfe",
            "type_name": "#4ec9b0", "class_name": "#4ec9b0", "tag_name": "#4ec9b0",
            "namespace": "#4ec9b0", "annotation": "#4ec9b0",
            "function": "#dcdcaa", "number": "#b5cea8",
            "operator": "#d4d4d4", "punctuation": "#d4d4d4",
            "regexp": "#d16969", "string": "#ce9178", "meta": "#ce9178",
            "angle_bracket": "#858585", "comment": "#6a9955", "link": "#6a9955",
            "invalid": "#ff2e2e",
        },
    ),
    "ayu-light": _t(
        "Ayu Light", False, "#fcfcfc", "#5c6166", "#8a919966",
        {
            # 原配色为亮色系（number 1.85:1），在白底上几乎不可读。
            # 保持色相、压暗明度至 WCAG AA。
            "comment": "#72757a", "string": "#5f7f00", "regexp": "#2f8267",
            "number": "#aa6300", "bool": "#aa6300", "null": "#aa6300",
            "variable_name": "#5c6166", "definition_keyword": "#c15405",
            "modifier": "#c15405", "keyword": "#c15405",
            "operator": "#c45117", "punctuation": "#5c6166",
            "function": "#a5670c", "attribute_name": "#a5670c",
            "class_name": "#147cb1", "definition_type": "#147cb1",
            "type_name": "#277e9b", "tag_name": "#277e9b", "label_name": "#277e9b",
        },
    ),
    "github-light": _t(
        "Github Light", False, "#ffffff", "#24292e", "#6a737d",
        {
            "tag_name": "#116329", "comment": "#6a737d", "bracket": "#6a737d",
            "class_name": "#6f42c1", "property_name": "#6f42c1",
            "variable_name": "#005cc5", "attribute_name": "#005cc5",
            "number": "#005cc5", "operator": "#005cc5",
            "keyword": "#d73a49", "type_name": "#d73a49",
            "string": "#032f62", "meta": "#032f62", "regexp": "#032f62",
            "name": "#22863a", "bool": "#c45508", "null": "#c45508",
            "link": "#032f62", "invalid": "#b31d28",
        },
    ),
    "github-dark": _t(
        "GitHub Dark", True, "#0d1117", "#c9d1d9", "#8b949e",
        {
            "tag_name": "#7ee787", "comment": "#8b949e", "bracket": "#8b949e",
            "class_name": "#d2a8ff", "property_name": "#d2a8ff",
            "variable_name": "#79c0ff", "attribute_name": "#79c0ff",
            "number": "#79c0ff", "operator": "#79c0ff",
            "keyword": "#ff7b72", "type_name": "#ff7b72",
            "string": "#a5d6ff", "meta": "#a5d6ff", "regexp": "#a5d6ff",
            "name": "#7ee787", "bool": "#ffab70", "null": "#ffab70",
            "invalid": "#ffdcd7",
        },
    ),
    "tokyo-night": _t(
        "Tokyo Night", True, "#1a1b26", "#c0caf5", "#565f89",
        {
            "keyword": "#bb9af7", "name": "#c0caf5", "property_name": "#7aa2f7",
            "string": "#9ece6a", "function": "#7aa2f7", "label_name": "#7aa2f7",
            "constant": "#bb9af7", "separator": "#c0caf5",
            "class_name": "#c0caf5", "number": "#ff9e64", "modifier": "#ff9e64",
            "type_name": "#0db9d7", "operator": "#bb9af7", "operator_keyword": "#bb9af7",
            "regexp": "#b4f9f8", "link": "#b4f9f8",
            "comment": "#7981ab", "meta": "#7981ab", "invalid": "#ff5370",
        },
    ),
    "xcode-dark": _t(
        "Xcode Dark", True, "#1f1f24", "#ACF2E4", "#7F8C98",
        {
            "comment": "#7F8C98", "quote": "#7F8C98", "meta": "#7F8C98",
            "keyword": "#FF7AB2", "string": "#FF8170",
            "type_name": "#DABAFF", "definition_variable": "#6BDFFF",
            "name": "#6BAA9F", "variable_name": "#ACF2E4",
            # 原主题未定义以下槽位，这里按 Xcode 默认配色补齐，
            # 避免数字/运算符等退化成前景色（视觉上像没高亮）
            "number": "#DABAFF", "bool": "#DABAFF", "null": "#DABAFF",
            "operator": "#ACF2E4", "punctuation": "#ACF2E4",
            "class_name": "#DABAFF", "function": "#6BDFFF",
            "property_name": "#6BAA9F", "attribute_name": "#6BAA9F",
        },
    ),
    "xcode-light": _t(
        "Xcode Light", False, "#ffffff", "#3D3D3D", "#707F8D",
        {
            "comment": "#6a7886", "quote": "#6a7886", "meta": "#6a7886",
            "type_name": "#522BB2", "keyword": "#aa0d91",
            "string": "#D23423", "name": "#032f62",
            "variable_name": "#23575C", "definition_variable": "#327A9E",
            # 同上，补齐原主题未定义的基础槽位
            "number": "#1C00CF", "bool": "#1C00CF", "null": "#1C00CF",
            "operator": "#3D3D3D", "punctuation": "#3D3D3D",
            "class_name": "#522BB2", "function": "#327A9E",
            "property_name": "#032f62", "attribute_name": "#032f62",
        },
    ),
    "amy": _t(
        "Amy", True, "#200020", "#D0D0FF", "#C080C0",
        {
            "comment": "#7373b9", "string": "#999999", "regexp": "#999999",
            "number": "#7090B0", "bool": "#8080A0", "null": "#8080A0",
            "punctuation": "#9f669f", "keyword": "#60B0FF",
            "definition_keyword": "#B0FFF0", "module_keyword": "#60B0FF",
            "operator": "#A0A0FF", "operator_keyword": "#A0A0FF",
            "variable_name": "#008888", "control_keyword": "#80A0FF",
            "class_name": "#70E080", "property_name": "#50A0A0",
            "function": "#50A0A0", "tag_name": "#009090", "modifier": "#B0FFF0",
        },
    ),
    "aura": _t(
        "Aura", True, "#21202e", "#edecee", "#edecee",
        {
            "keyword": "#a277ff", "name": "#edecee", "property_name": "#ffca85",
            "string": "#61ffca", "function": "#ffca85", "label_name": "#ffca85",
            "constant": "#61ffca", "separator": "#edecee",
            "class_name": "#82e2ff", "number": "#61ffca", "modifier": "#61ffca",
            "type_name": "#82e2ff", "operator": "#a277ff",
            "operator_keyword": "#a277ff", "regexp": "#61ffca",
            "comment": "#888888", "meta": "#888888", "invalid": "#ff6767",
        },
    ),
    "cool-glow": _t(
        "Cool Glow", True, "#060521", "#E0E0E0", "#E0E0E090",
        {
            "comment": "#AEAEAE", "string": "#8DFF8E", "special_brace": "#8DFF8E",
            "regexp": "#8DFF8E", "class_name": "#A3EBFF", "function": "#A3EBFF",
            "definition_type": "#A3EBFF", "number": "#62E9BD",
            "bool": "#62E9BD", "null": "#62E9BD",
            "keyword": "#2BF1DC", "operator": "#2BF1DC",
            "definition_keyword": "#F8FBB1", "modifier": "#F8FBB1",
            "variable_name": "#B683CA", "type_name": "#60A4F1",
            "property_name": "#60A4F1", "tag_name": "#60A4F1",
        },
    ),
}

# 10 套社区常用渐变，值为 linear-gradient(90deg, c1, c2)
GRADIENTS: Dict[str, Tuple[str, str]] = {
    "mystic":   ("#b993d6", "#8ca6db"),   # 默认背景
    "aruba":    ("#42afa1", "#78d4a8"),
    "jungle":   ("#c1b777", "#79c08d"),
    "tropical": ("#2bc0e4", "#eaecc6"),
    "aurora":   ("#5ee7df", "#b490ca"),
    "candy":    ("#d8848b", "#cb96da"),
    "peach":    ("#de6262", "#ffb88c"),
    "bananas":  ("#f9de70", "#fffbab"),
    "leaf":     ("#1d976c", "#93f9b9"),
    "ocean":    ("#24c6dc", "#514a9d"),
}

# 窗口控制点配色（对应 CSS 的 win-ctrl-style-*）
WINDOW_CONTROLS: Dict[str, Dict[str, Optional[str]]] = {
    "color":   {"exit": "#ff5f56", "min": "#ffbd2e", "max": "#27c93f", "border": None},
    "gray":    {"exit": "#ffffff40", "min": "#ffffff40", "max": "#ffffff40", "border": None},
    "gray-light": {"exit": "#00000018", "min": "#00000018", "max": "#00000018", "border": None},
    "outline": {"exit": None, "min": None, "max": None, "border": "#ffffff40"},
    "none":    {"exit": None, "min": None, "max": None, "border": None},
}

# 背景可选取值
BACKGROUND_CHOICES = tuple(GRADIENTS) + ("single", "transparent")


def get_theme(name: str) -> Theme:
    """按名称取主题，接受大小写与空格/下划线差异。"""
    key = name.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "one-dark": "one-dark", "onedark": "one-dark", "dark": "one-dark",
        "dracula": "dracula", "vscode": "vscode", "vs-code": "vscode",
        "ayu-light": "ayu-light", "ayulight": "ayu-light", "light": "github-light",
        "github-light": "github-light", "githublight": "github-light",
        "github-dark": "github-dark", "githubdark": "github-dark",
        "tokyo-night": "tokyo-night", "tokyonight": "tokyo-night", "tokyo": "tokyo-night",
        "xcode-dark": "xcode-dark", "xcodedark": "xcode-dark",
        "xcode-light": "xcode-light", "xcodelight": "xcode-light",
        "amy": "amy", "aura": "aura", "cool-glow": "cool-glow", "coolglow": "cool-glow",
    }
    resolved = aliases.get(key, key)
    if resolved not in THEMES:
        raise ValueError(
            f"未知主题 {name!r}；可选：{', '.join(sorted(THEMES))}"
        )
    return THEMES[resolved]


def get_gradient(name: str) -> Optional[Tuple[str, str]]:
    key = name.strip().lower()
    return GRADIENTS.get(key)
