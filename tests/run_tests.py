#!/usr/bin/env python3
"""
Finance Dashboard 測試命令選單
====================================
互動式 CLI 選單，整合 pytest 與 Allure 報告。

使用方法:
    python tests/run_tests.py
    python tests/run_tests.py --ci          # 非互動模式，執行全部測試
    python tests/run_tests.py --allure      # 執行全部並產生 Allure 報告
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ──────────────────────────────────────────────
# 路徑設定
# ──────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent     # finance_dashboard/
TESTS_DIR = ROOT_DIR / "tests"
ALLURE_RESULTS = TESTS_DIR / "allure-results"
ALLURE_REPORT = TESTS_DIR / "allure-report"

# ──────────────────────────────────────────────
# ANSI 顏色
# ──────────────────────────────────────────────
_NO_COLOR = not sys.stdout.isatty() or os.getenv("NO_COLOR")


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


BOLD   = lambda t: _c("1",     t)
RED    = lambda t: _c("31",    t)
GREEN  = lambda t: _c("32",    t)
YELLOW = lambda t: _c("33",    t)
CYAN   = lambda t: _c("36",    t)
DIM    = lambda t: _c("2",     t)


# ──────────────────────────────────────────────
# 工具函式
# ──────────────────────────────────────────────

def _run(cmd: list[str], *, capture: bool = False) -> int:
    """執行命令，回傳 exit code。"""
    print(DIM("$ " + " ".join(str(c) for c in cmd)))
    result = subprocess.run(cmd, capture_output=capture, cwd=ROOT_DIR)
    return result.returncode


def _pytest(*extra_args: str, allure: bool = False, verbose: bool = True) -> int:
    """組合 pytest 命令並執行。"""
    cmd: list[str] = [sys.executable, "-m", "pytest"]
    if verbose:
        cmd += ["-v", "--tb=short"]
    cmd += list(extra_args)
    if allure:
        cmd += [f"--alluredir={ALLURE_RESULTS}"]
    return _run(cmd)


def _ensure_allure() -> bool:
    """確認 allure CLI 是否可用。"""
    return shutil.which("allure") is not None


def _open_allure_report() -> None:
    """產生並開啟 Allure HTML 報告。"""
    if not _ensure_allure():
        print(
            YELLOW("\n⚠ 未偵測到 allure 命令。請先安裝：")
            + "\n  brew install allure\n  或 scoop install allure"
        )
        return

    if not ALLURE_RESULTS.exists():
        print(RED("\n✗ 找不到 allure-results/，請先執行含 --allure 的測試。"))
        return

    print(CYAN("\n產生 Allure HTML 報告…"))
    _run(["allure", "generate", str(ALLURE_RESULTS), "-o", str(ALLURE_REPORT), "--clean"])
    _run(["allure", "open", str(ALLURE_REPORT)])


def _clean() -> None:
    """清除 pytest cache 與 Allure 結果。"""
    targets = [
        ALLURE_RESULTS,
        ALLURE_REPORT,
        TESTS_DIR / ".pytest_cache",
        ROOT_DIR / ".pytest_cache",
    ]
    for t in targets:
        if t.exists():
            shutil.rmtree(t)
            print(GREEN(f"  已刪除 {t.relative_to(ROOT_DIR)}"))
    # 清除 __pycache__
    for p in ROOT_DIR.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    print(GREEN("  ✔ 清除完成"))


# ──────────────────────────────────────────────
# 選單動作
# ──────────────────────────────────────────────

MENU: list[tuple[str, str]] = [
    ("1", "執行 全部測試  (unit + e2e)"),
    ("2", "執行 Unit 測試"),
    ("3", "執行 E2E  測試"),
    ("4", "執行 指定模組  (輸入路徑)"),
    ("5", "執行 全部測試  + 產生 Allure 結果"),
    ("6", "執行 Unit 測試 + 產生 Allure 結果"),
    ("7", "執行 E2E  測試 + 產生 Allure 結果"),
    ("8", "開啟 Allure HTML 報告"),
    ("9", "清除 測試快取 & Allure 結果"),
    ("0", "離開"),
]


def _print_menu() -> None:
    width = 54
    border = "─" * width
    print(f"\n╔{border}╗")
    print(f"║{'Finance Dashboard — 測試選單':^{width}}║")
    print(f"╠{border}╣")
    for key, label in MENU:
        print(f"║  {CYAN(key)}  {label:<48}║")
    print(f"╚{border}╝")


def _handle_choice(choice: str) -> bool:
    """處理選擇，回傳 False 表示應結束。"""
    choice = choice.strip()

    if choice == "0":
        print(GREEN("\n掰掰！"))
        return False

    elif choice == "1":
        code = _pytest("tests/")
        _summarize(code)

    elif choice == "2":
        code = _pytest("tests/unit/", "-m", "unit")
        _summarize(code)

    elif choice == "3":
        code = _pytest("tests/e2e/", "-m", "e2e")
        _summarize(code)

    elif choice == "4":
        path = input(CYAN("  輸入測試路徑（相對於專案根目錄）: ")).strip()
        if not path:
            print(YELLOW("  未輸入路徑，取消。"))
        else:
            code = _pytest(path)
            _summarize(code)

    elif choice == "5":
        code = _pytest("tests/", allure=True)
        _summarize(code)

    elif choice == "6":
        code = _pytest("tests/unit/", "-m", "unit", allure=True)
        _summarize(code)

    elif choice == "7":
        code = _pytest("tests/e2e/", "-m", "e2e", allure=True)
        _summarize(code)

    elif choice == "8":
        _open_allure_report()

    elif choice == "9":
        _clean()

    else:
        print(RED("  無效選項，請重新輸入。"))

    return True  # 繼續


def _summarize(code: int) -> None:
    if code == 0:
        print(GREEN("\n✔ 所有測試通過！"))
    else:
        print(RED(f"\n✗ 測試失敗 (exit code {code})"))


# ──────────────────────────────────────────────
# 進入點
# ──────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finance Dashboard 測試選單")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI 模式：非互動，執行全部測試後退出",
    )
    parser.add_argument(
        "--allure",
        action="store_true",
        help="執行全部測試並產生 Allure 結果",
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="僅執行 unit 測試",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="僅執行 e2e 測試",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # ── 非互動模式 ──
    if args.ci:
        code = _pytest("tests/", allure=args.allure)
        sys.exit(code)

    if args.allure:
        code = _pytest("tests/", allure=True)
        _summarize(code)
        sys.exit(code)

    if args.unit:
        code = _pytest("tests/unit/", "-m", "unit")
        _summarize(code)
        sys.exit(code)

    if args.e2e:
        code = _pytest("tests/e2e/", "-m", "e2e")
        _summarize(code)
        sys.exit(code)

    # ── 互動選單 ──
    print(BOLD(CYAN("\n  Finance Dashboard 測試工具\n")))
    while True:
        _print_menu()
        try:
            choice = input(CYAN("\n  請選擇 [0-9]: "))
        except (KeyboardInterrupt, EOFError):
            print(GREEN("\n\n已中斷，掰掰！"))
            break
        if not _handle_choice(choice):
            break


if __name__ == "__main__":
    main()
