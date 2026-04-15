# GitHub 上传指南

## 📤 方法一：通过 GitHub 网页手动上传 (推荐)

### 步骤 1: 创建新的 GitHub 仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" 图标 → "New repository"
3. 填写仓库信息:
   - **Repository name**: `ultimateDESIGN` (或其他你喜欢的名字)
   - **Description**: "长春伪满皇宫周边街区多模态微更新决策平台"
   - **Public/Private**: 根据需要选择
   - **不要勾选** "Initialize this repository with a README"
4. 点击 "Create repository"

### 步骤 2: 准备上传文件

1. **压缩项目文件夹**:
   - 右键点击 `ultimateDESIGN` 文件夹
   - 选择 "发送到" → "压缩 (zipped) 文件夹"
   - 生成 `ultimateDESIGN.zip`

### 步骤 3: 上传到 GitHub

**方式 A - 直接拖拽上传**:
1. 在刚创建的仓库页面，点击 "uploading an existing file"
2. 将 `ultimateDESIGN.zip` 拖拽到上传区域
3. 或者解压后，选择所有文件拖拽上传
4. 在 "Commit changes" 文本框中输入提交信息，如 "Initial commit"
5. 点击 "Commit changes"

**方式 B - 使用 Git 命令行**:
```bash
# 进入项目目录
cd c:\Users\23902\ultimateDESIGN

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 关联远程仓库 (替换为你的仓库地址)
git remote add origin https://github.com/YOUR_USERNAME/ultimateDESIGN.git

# 推送
git push -u origin main
```

## 📤 方法二：使用 Git 命令行 (适合有 Git 基础的用户)

### 前置要求

1. 安装 [Git](https://git-scm.com/download/win)
2. 安装 [GitHub Desktop](https://desktop.github.com/) (可选)

### 详细步骤

```bash
# 1. 进入项目目录
cd c:\Users\23902\ultimateDESIGN

# 2. 初始化 Git 仓库
git init

# 3. 添加所有文件到暂存区
git add .

# 4. 提交更改
git commit -m "Initial commit: 长春伪满皇宫微更新平台"

# 5. 在 GitHub 创建仓库后，关联远程仓库
git remote add origin https://github.com/YOUR_USERNAME/ultimateDESIGN.git

# 6. 推送到 GitHub
git branch -M main
git push -u origin main
```

## 📤 方法三：使用 GitHub Desktop (最简单)

### 步骤

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录 GitHub 账号
3. 点击 "File" → "Add local repository" → "Choose..."
4. 选择 `c:\Users\23902\ultimateDESIGN` 文件夹
5. 如果是第一次，点击 "Create a repository"
6. 填写信息后点击 "Publish repository"

## ⚠️ 重要提示

### 1. .gitignore 已配置

项目已包含 `.gitignore` 文件，会自动排除:
- `__pycache__/` - Python 缓存文件
- `venv/` - 虚拟环境
- `.vscode/` - IDE 配置
- `*.pyc` - 编译后的 Python 文件
- 其他临时文件

### 2. 大文件处理

如果项目包含大文件 (如街景图片),建议:
- 使用 [Git LFS](https://git-lfs.github.com/) 管理大文件
- 或者在 `.gitignore` 中排除大文件目录

### 3. 敏感信息

确保不要上传:
- API 密钥
- 数据库密码
- 个人敏感信息
- `.env` 文件

## 🎯 推荐做法

1. **首次上传**: 使用网页上传或 GitHub Desktop
2. **后续更新**: 使用 Git 命令行或 GitHub Desktop
3. **大文件**: 使用 Git LFS 或排除在版本控制外

## 📊 仓库大小优化

如果仓库过大，可以:

1. 在 `.gitignore` 中添加:
```
# 排除大文件
StreetViews/*.jpg
StreetViews/*.png
*.csv
*.xlsx
```

2. 使用 Git LFS 管理大文件:
```bash
git lfs install
git lfs track "*.jpg"
git lfs track "*.png"
git add .gitattributes
```

## ✅ 上传后检查

- [ ] 所有代码文件已上传
- [ ] README.md 显示正常
- [ ] requirements.txt 包含所有依赖
- [ ] 没有敏感信息泄露
- [ ] .gitignore 生效

## 🔗 相关资源

- [GitHub 文档](https://docs.github.com/)
- [Git 教程](https://git-scm.com/book/zh/v2)
- [GitHub Desktop](https://docs.github.com/desktop)
- [Git LFS](https://git-lfs.github.com/)
