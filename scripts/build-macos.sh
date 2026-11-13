#!/usr/bin/env bash
# [INPUT]: React 前端源码、Tauri 2 Rust 后端、macOS Objective-C 原生模块。
# [OUTPUT]: 面向 Apple Silicon (aarch64-apple-darwin) 的 Claude-Local.app 与 .dmg 安装包。
# [POS]: macOS 独立构建脚本；无云端依赖、离线编译。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "=================================================="
echo "    Claude-Local macOS (Apple Silicon) 构建程序   "
echo "=================================================="

# 1. 检查必要工具
check_tool() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "错误: 未找到 $1，请先安装。"
        return 1
    fi
}

echo ">> 检查开发环境..."
MISSING=0
check_tool "cargo" || MISSING=1
check_tool "rustc" || MISSING=1

PKG_MGR="bun"
if ! command -v bun >/dev/null 2>&1; then
    if command -v npm >/dev/null 2>&1; then
        PKG_MGR="npm"
        echo "提示: 未检测到 bun，使用 npm 代替。"
    else
        echo "错误: 未找到 bun 或 npm，请先安装其中之一。"
        MISSING=1
    fi
fi

if [[ $MISSING -eq 1 ]]; then
    echo ""
    echo "=================================================="
    echo "请先在您的 Mac 上安装以下前置依赖："
    echo "1. Xcode Command Line Tools: xcode-select --install"
    echo "2. Rust 编程环境: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "3. Bun 运行时: curl -fsSL https://bun.sh/install | bash"
    echo "=================================================="
    exit 1
fi

echo ">> Rust 版本: $(rustc --version)"
echo ">> 包管理器: $PKG_MGR ($($PKG_MGR --version))"
echo ">> 系统架构: $(uname -m)"

# 2. 准备伴生浏览器
echo ">> 准备伴生浏览器资源..."
"$SCRIPT_DIR/package-browser-macos.sh"

# 3. 构建前端资源
echo ">> 安装前端依赖与构建 UI..."
$PKG_MGR install
$PKG_MGR run build

# 4. 执行 Tauri 构建
echo ">> 构建 Tauri macOS 客户端 (Apple Silicon)..."
if [[ "$PKG_MGR" == "bun" ]]; then
    bun run tauri build --config src-tauri/tauri.macos.conf.json
else
    npx tauri build --config src-tauri/tauri.macos.conf.json
fi

echo ""
echo "=================================================="
echo "✨ 构建成功！"
echo "应用程序位置："
echo "  .app 包: src-tauri/target/release/bundle/macos/Claude-Local.app"
echo "  .dmg 包: src-tauri/target/release/bundle/dmg/"
echo "=================================================="
