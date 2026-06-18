# MyRssApp

Windows 桌面 RSS 阅读器，基于 PySide6 + Python 3.13。

## 快速启动（PyCharm）

1. 用 PyCharm 打开 `D:\projects\MyRssApp`
2. 设置解释器：`File → Settings → Project → Python Interpreter` → 选择 `venv\Scripts\python.exe`
3. 右键 `main.py` → Run 'main'

或命令行：

```bash
cd D:\projects\MyRssApp
venv\Scripts\python.exe main.py
```

## 功能

- RSS 订阅管理（增删改查、OPML 导入导出）
- 文章阅读（QWebEngineView 渲染、已读/未读、收藏）
- 全文搜索（SQLite FTS5）
- AI 中英双向翻译（默认腾讯混元 API）
- 深色/浅色主题切换
- 字体与同步频率设置

## 项目结构

```
myrssapp/
├── models/        # 数据模型 (dataclass, 无 Qt 依赖)
├── database/      # SQLite 连接/建表/Repository
├── services/      # 业务逻辑 (抓取/翻译/搜索/设置)
├── viewmodels/    # MVVM ViewModel 层
├── views/         # MVVM View 层
└── utils/         # 工具 (资源路径/主题/字体/配置)
resources/         # 图标和 QSS 样式
```

## 依赖

- Python >= 3.11
- PySide6 >= 6.8.0
- feedparser, requests, lxml, openai, beautifulsoup4

## 打包

```bash
pip install pyinstaller
pyinstaller myrssapp.spec
```
