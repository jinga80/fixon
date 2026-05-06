#!/usr/bin/env python
"""FixOn — Django management entrypoint."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django import 실패. 가상환경 활성화 + `pip install -r requirements.txt` 후 다시 실행하세요."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
