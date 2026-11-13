#!/usr/bin/env bash
# [INPUT]: macOS Apple Silicon Chromium 引擎源码/已下载引擎、CCBrowser 启动器源码与配套图标。
# [OUTPUT]: 编译 CCBrowser arm64 启动器、修补 Browser.app 元数据与图标、生成 Browser.zip 打包资源。
# [POS]: macOS 构建前置准备；准备隔离的 Fingerprint Chromium 引擎与启动入口。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

BROWSER_APP="$ROOT_DIR/browser-runtime/Browser.app"
BROWSER_ZIP="$ROOT_DIR/browser-runtime/Browser.zip"
LAUNCHER_SRC="$ROOT_DIR/browser-runtime/launcher/CCBrowser.c"
ICONS_SRC="$ROOT_DIR/browser-runtime/icons/app.icns"

echo "=== 正在准备 macOS (Apple Silicon) 伴生浏览器 ==="

# 1. 如果没有 Browser.app，尝试运行 fetch-browser.py 下载
if [[ ! -d "$BROWSER_APP" || ! -f "$BROWSER_APP/Contents/MacOS/Chromium" ]]; then
    echo ">> 未发现已准备的 Browser.app，尝试通过 fetch-browser.py 下载..."
    if command -v python3 >/dev/null 2>&1; then
        python3 "$ROOT_DIR/scripts/fetch-browser.py" || {
            echo "警告: 自动下载 Chromium 引擎失败（可能无网络或被拦截）。"
            echo "如需伴生浏览器功能，请手动运行: python3 scripts/fetch-browser.py"
        }
    fi
fi

# 2. 如果 Browser.app 存在，编译 CCBrowser 并注入
if [[ -d "$BROWSER_APP" && -f "$BROWSER_APP/Contents/MacOS/Chromium" ]]; then
    echo ">> 编译 arm64 版 CCBrowser 启动器..."
    if command -v clang >/dev/null 2>&1; then
        clang -arch arm64 -O2 "$LAUNCHER_SRC" -o "$BROWSER_APP/Contents/MacOS/CCBrowser" -lproc
        chmod +x "$BROWSER_APP/Contents/MacOS/CCBrowser"
        
        # 配置 Info.plist 的执行文件名与 bundle identifier
        INFO_PLIST="$BROWSER_APP/Contents/Info.plist"
        if command -v plutil >/dev/null 2>&1; then
            plutil -replace CFBundleExecutable -string "CCBrowser" "$INFO_PLIST" 2>/dev/null || true
            plutil -replace CFBundleIdentifier -string "ai.local.claude-local.browser" "$INFO_PLIST" 2>/dev/null || true
            plutil -replace CFBundleName -string "Claude-Local Browser" "$INFO_PLIST" 2>/dev/null || true
        fi
        
        # 复制专属图标
        if [[ -f "$ICONS_SRC" ]]; then
            mkdir -p "$BROWSER_APP/Contents/Resources"
            cp "$ICONS_SRC" "$BROWSER_APP/Contents/Resources/app.icns"
        fi
        echo ">> CCBrowser 启动器配置完成。"
    else
        echo "警告: 未找到 clang，跳过编译 CCBrowser。"
    fi

    # 3. 生成 Browser.zip 供 Tauri 打包资源引用
    echo ">> 打包 Browser.zip..."
    rm -f "$BROWSER_ZIP"
    ditto -c -k --keepParent "$BROWSER_APP" "$BROWSER_ZIP"
    echo ">> Browser.zip 准备完成 ($(du -h "$BROWSER_ZIP" | cut -f1))"
else
    # 创建一个占位的 Browser.zip，防止 Tauri bundler 缺失资源报错
    if [[ ! -f "$BROWSER_ZIP" ]]; then
        echo ">> 创建基础 Browser.zip 占位包（运行时可使用外部安装的 Chromium）..."
        mkdir -p "$ROOT_DIR/browser-runtime/.placeholder"
        echo "placeholder" > "$ROOT_DIR/browser-runtime/.placeholder/placeholder.txt"
        ditto -c -k "$ROOT_DIR/browser-runtime/.placeholder" "$BROWSER_ZIP"
        rm -rf "$ROOT_DIR/browser-runtime/.placeholder"
    fi
fi

echo "=== 浏览器资源准备完毕 ==="
