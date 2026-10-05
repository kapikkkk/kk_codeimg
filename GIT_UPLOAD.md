# 上传到 GitHub

仓库地址：https://github.com/kapikkkk/kk_codeimg

本地已完成的准备工作：

- `git init` + 首次提交（23 个文件，3279 行，commit `dff9fea`）
- 敏感信息审计通过（无 token、无本机绝对路径、无个人用户名）
- `dist/` `out/` 已由 `.gitignore` 排除
- `docs/` 下 7 张示例图、`.github/` issue 模板均已纳入版本管理

## 第 1 步：建空仓库（浏览器操作，1 分钟）

打开 <https://github.com/new>，填写：

| 字段 | 填什么 |
|---|---|
| Owner | `kapikkkk` |
| Repository name | `kk_codeimg` |
| Description | 把代码渲染成精美的代码图片：12 套主题、16 种预设风格，纯 Pillow + Pygments 离线渲染 |
| Visibility | **Public** |
| Initialize this repository | **全部不勾**（不要加 README/.gitignore/LICENSE） |

> ⚠️ 一定要**空仓库**，否则远程已有 commit 会导致 push 被拒。

## 第 2 步：登录（在你自己的终端执行）

```bash
gh auth login
```

按提示选：`GitHub.com` → `HTTPS` → `Y`（用浏览器认证）。

> 若 `gh` 报网络错误，改用 Personal Access Token：
> <https://github.com/settings/tokens> → Generate new token (classic)
> 勾选 `repo` 和 `read:org` → 复制 token → 执行
> `gh auth login --with-token`，把 token 粘进去回车。

## 第 3 步：推送

```bash
cd /path/to/kk_codeimg
git remote add origin https://github.com/kapikkkk/kk_codeimg.git
git push -u origin main
```

## 备选：不用 gh，用 GitHub 网页

如果第 2 步的网络有问题，直接在 <https://github.com/kapikkkk/kk_codeimg> 页面
（建好空仓库后）上传。注意先在本地删除 `out/`、`dist/` 再打包，
因为网页上传不支持 `.gitignore`：

```bash
# 临时准备一个纯净副本
cd /path/to/           # 即 kk_codeimg 的父目录
python -c "
import shutil, pathlib
src = pathlib.Path('codepng'); dst = pathlib.Path('kk_codeimg_upload')
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns('out','dist','.git','__pycache__','.pytest_cache','*.egg-info'))
print('已生成', dst.resolve())
"
```

然后把 `kk_codeimg_upload/` 里的 23 个文件拖到 GitHub 网页上。

## 推完后建议做的事

1. 在仓库 About 里填 Website：`https://pypi.org/project/kk_codeimg/`
2. README 顶部三个徽章会自动显示（指向 PyPI）
3. 发一版到 PyPI：见 `PUBLISH.md`
4. 把 `pyproject.toml` 里注释掉的链接补上：

```toml
[project.urls]
Homepage = "https://github.com/kapikkkk/kk_codeimg"
Repository = "https://github.com/kapikkkk/kk_codeimg"
Issues = "https://github.com/kapikkkk/kk_codeimg/issues"
```
