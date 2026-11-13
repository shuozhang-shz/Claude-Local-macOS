#!/usr/bin/env python3
"""
[INPUT]: macOS Apple Silicon Chromium 引擎源码/已下载引擎、CCBrowser 启动器源码与配套图标。
[OUTPUT]: 编译 CCBrowser arm64 启动器、使用 plistlib 修补 Browser.app 元数据与图标、生成 Browser.zip 打包资源。
[POS]: macOS 构建前置准备纯 Python 实现；保证资源完整可用。
"""
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSER_RUNTIME = ROOT / "browser-runtime"
BROWSER_APP = BROWSER_RUNTIME / "Browser.app"
BROWSER_ZIP = BROWSER_RUNTIME / "Browser.zip"
LAUNCHER_SRC = BROWSER_RUNTIME / "launcher/CCBrowser.c"
ICONS_SRC = BROWSER_RUNTIME / "icons/app.icns"


def prepare_browser():
    print("=== [Python] 正在准备 macOS (Apple Silicon) 伴生浏览器 ===")

    # 1. 如果没有 Browser.app，尝试运行 fetch-browser.py 下载
    chromium_bin = BROWSER_APP / "Contents/MacOS/Chromium"
    if not BROWSER_APP.is_dir() or not chromium_bin.is_file():
        print(">> 未发现已准备的 Browser.app，尝试运行 fetch-browser.py 下载...")
        try:
            subprocess.run([sys.executable, str(ROOT / "scripts/fetch-browser.py")], check=True)
        except Exception as e:
            print(f"提示: 自动下载 Chromium 引擎跳过或失败 ({e})。")
            print("如需配套指纹伴生浏览器功能，请联网后运行: python3 scripts/fetch-browser.py")

    # 2. 如果已下载 Browser.app，注入 CCBrowser 启动器与元数据
    if BROWSER_APP.is_dir() and chromium_bin.is_file():
        print(">> 编译 arm64 版 CCBrowser 启动器...")
        ccbrowser_bin = BROWSER_APP / "Contents/MacOS/CCBrowser"
        clang_path = shutil.which("clang")
        if clang_path:
            cmd = [
                clang_path,
                "-arch", "arm64",
                "-O2",
                str(LAUNCHER_SRC),
                "-o", str(ccbrowser_bin),
                "-lproc"
            ]
            subprocess.run(cmd, check=True)
            ccbrowser_bin.chmod(0o755)
            print(">> CCBrowser 编译成功。")

            # 用 Python 自带的 plistlib 更新 Info.plist
            info_plist = BROWSER_APP / "Contents/Info.plist"
            if info_plist.is_file():
                try:
                    with open(info_plist, "rb") as f:
                        data = plistlib.load(f)
                    data["CFBundleExecutable"] = "CCBrowser"
                    data["CFBundleIdentifier"] = "ai.local.claude-local.browser"
                    data["CFBundleName"] = "Claude-Local Browser"
                    with open(info_plist, "wb") as f:
                        plistlib.dump(data, f)
                    print(">> Info.plist 元数据已更新。")
                except Exception as e:
                    print(f"警告: 更新 Info.plist 出错: {e}")

            # 复制专属图标
            if ICONS_SRC.is_file():
                res_dir = BROWSER_APP / "Contents/Resources"
                res_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ICONS_SRC, res_dir / "app.icns")
                print(">> 伴生浏览器图标注入完成。")

        # 3. 使用 macOS 原生 ditto 打包生成 Browser.zip
        print(">> 打包 Browser.zip...")
        if BROWSER_ZIP.exists():
            BROWSER_ZIP.unlink()
        subprocess.run(["ditto", "-c", "-k", "--keepParent", str(BROWSER_APP), str(BROWSER_ZIP)], check=True)
        size_mb = BROWSER_ZIP.stat().st_size / (1024 * 1024)
        print(f">> Browser.zip 打包完成 ({size_mb:.1f} MB)")
    else:
        # 兜底：创建占位 Browser.zip 确保 Tauri 构建不因缺少资源文件报错
        if not BROWSER_ZIP.exists():
            print(">> 创建基础 Browser.zip 占位包（运行时使用外部安装的 Chromium）...")
            stage = BROWSER_RUNTIME / ".placeholder"
            stage.mkdir(parents=True, exist_ok=True)
            (stage / "placeholder.txt").write_text("Claude-Local Browser Placeholder\n", encoding="utf-8")
            subprocess.run(["ditto", "-c", "-k", str(stage), str(BROWSER_ZIP)], check=True)
            shutil.rmtree(stage, ignore_errors=True)

    print("=== 浏览器资源准备完毕 ===\n")


if __name__ == "__main__":
    prepare_browser()
