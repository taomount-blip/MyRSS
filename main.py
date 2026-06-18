"""MyRssApp 启动入口 – 直接在 PyCharm 右键运行此文件"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from myrssapp.main import main

if __name__ == "__main__":
    main()
