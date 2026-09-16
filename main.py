"""
main.py — корневая точка входа.
Делегирует запуск в app.main.
"""

import sys

from app.main import main

if __name__ == "__main__":
    sys.exit(main())
