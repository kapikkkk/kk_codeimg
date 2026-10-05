# 发布到 PyPI 指南

包名：**kk_codeimg**　当前版本：**0.0.1**

一次性准备已完成（`pyproject.toml`、`LICENSE`、`.gitignore` 均已就位），
以下是你每次发新版本要执行的流程。

---

## 0. 首次发布前：申请 API token

1. 登录 <https://pypi.org/account/settings/> → **API tokens** → **Create token**
2. 勾选 `pypi-org` scope（组织名留空，适用于个人账号）
3. **立刻复制** token，只显示一次

配置凭据（二选一）：

**方式 A：命令行传入（不落盘）**

```bash
python -m twine upload dist/* -u __token__ -p <粘贴你的 token>
```

**方式 B：写入 `~/.pypirc`（推荐，token 不进 shell 历史）**

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-<粘贴你在 PyPI 生成的 token>
```

Windows 下 `~/.pypirc` 实际位于你的用户目录，例如 `C:\Users\<你的用户名>\.pypirc`。

> 可先用 TestPyPI 试跑：
> `python -m twine upload --repository testpypi dist/*`
> 测试安装：`pip install --index-url https://test.pypi.org/simple/ kk_codeimg`
> 注意 TestPyPI 与正式 PyPI 账号不通用，需单独注册。

---

## 1. 发新版本的完整流程

```bash
cd codepng

# 1) 递增版本号（自动读取当前版本，不用手改数字）
python -c "
import re, pathlib
TOML, INIT = 'pyproject.toml', 'kk_codeimg/__init__.py'
cur = re.search(r'(?m)^version = \"(.+)\"$', pathlib.Path(TOML).read_text(encoding='utf-8')).group(1)
a, b, c = (cur.split('.') + ['0'])[:3]
new = f'{a}.{b}.{int(c)+1}'
for p, pat, rep in [
    (TOML,  r'(?m)^(version = \")' + re.escape(cur) + r'(\")$', r'\g<1>' + new + r'\g<2>'),
    (INIT,  r'(__version__ = \")' + re.escape(cur) + r'(\")', r'\g<1>' + new + r'\g<2>'),
]:
    f = pathlib.Path(p); t = f.read_text(encoding='utf-8')
    assert re.search(pat, t), f'{p} 未匹配到版本号，请手工核对'
    f.write_text(re.sub(pat, rep, t), encoding='utf-8')
    print(f'{p}: {cur} -> {new}')
"

# 2) 跑测试（必须全绿）
python -m pytest scripts/test_codepng.py -q

# 2.5) 自检：确认两处版本号一致（不一致会导致 pip show 显示错版本）
python -c "
import re, pathlib, sys
v1 = re.search(r'(?m)^version = \"(.+)\"\$', pathlib.Path('pyproject.toml').read_text(encoding='utf-8')).group(1)
v2 = re.search(r'__version__ = \"(.+)\"', pathlib.Path('kk_codeimg/__init__.py').read_text(encoding='utf-8')).group(1)
print('pyproject:', v1, '| __init__:', v2)
sys.exit(0 if v1 == v2 else '版本号不一致，请修正！')
"

# 3) 清理并构建
rm -rf dist build *.egg-info
python -m build

# 4) 校验元数据（会检查 README 能否正常渲染）
python -m twine check dist/*

# 5) 上传
python -m twine upload dist/*
```

⚠️ **版本号一旦上传不可重用**，PyPI 不允许覆盖。改坏了只能递增版本重发。

---

## 2. 上传后验证

```bash
# 等 1~3 分钟让 PyPI 索引更新，然后：
pip install kk_codeimg
python -c "from kk_codeimg import code_generator; print('ok')"
```

或直接访问 <https://pypi.org/project/kk_codeimg/> 看页面是否正常。

---

## 3. 打包内容确认

`pyproject.toml` 里 `packages = ["kk_codeimg"]` 只包含库代码，
`out/`（样图）、`scripts/`（测试与样图生成）**不会**打进包里，这是有意为之。

若日后要发布源码包供人参考，`scripts/` 会被 sdist 自动包含（sdist 默认收录更多文件）。

---

## 4. 常见问题

| 现象 | 原因与处理 |
|---|---|
| `twine check` 报 `long_description` 渲染失败 | README 里有 PyPI 不支持的语法（相对路径图片、HTML 标签）。本项目已移除相对路径图片 |
| `409 Conflict` | 版本号已存在，必须递增 |
| `403 Forbidden` | token 无效或过期，检查 scope 是否含 `pypi-org` |
| `Invalid or non-existent file` | 确认 `dist/` 下同时有 `.whl` 和 `.tar.gz` |
| 装完 `import kk_codeimg` 报错 | 检查是否残留旧的 `codepng` 目录，`pip uninstall` 后重装 |
