#!/usr/bin/env python3
"""
[INPUT]: React 前端源码、Tauri 2 Rust 后端、macOS Objective-C 原生模块。
[OUTPUT]: 面向 Apple Silicon (aarch64-apple-darwin) 的 Claude-Local.app 与 .dmg 安装包。
[POS]: macOS 独立 Python 构建程序；无云端依赖、离线编译、全链路自动化。
"""
import hashlib
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("=" * 60)
    print("      Claude-Local macOS (Apple Silicon) Python 构建程序      ")
    print("=" * 60)

    # 1. 架构与平台检查
    sys_name = platform.system()
    machine = platform.machine()
    print(f">> 当前操作系统: {sys_name}")
    print(f">> 当前芯片架构: {machine}")
    print(f">> Python 解释器: {sys.executable} ({platform.python_version()})")

    if sys_name != "Darwin":
        print("错误: 本脚本仅限在 macOS 系统上运行！")
        sys.exit(1)

    if machine not in ("arm64", "aarch64"):
        print("提示: 当前非 Apple Silicon 芯片 (x86_64)，建议在 M系列芯片上构建原生应用。")

    # 2. 检查开发环境依赖
    print("\n>> 检查系统工具链...")
    missing_tools = []
    for tool in ["cargo", "rustc"]:
        if check_tool(tool):
            ver = subprocess.check_output([tool, "--version"], text=True).strip()
            print(f"  [✓] {tool}: {ver}")
        else:
            missing_tools.append(tool)
            print(f"  [✗] {tool}: 未安装")

    # 检查前端打包工具 (优先 bun，其次 npm)
    pkg_mgr = None
    if check_tool("bun"):
        pkg_mgr = "bun"
        ver = subprocess.check_output(["bun", "--version"], text=True).strip()
        print(f"  [✓] bun: {ver}")
    elif check_tool("npm"):
        pkg_mgr = "npm"
        ver = subprocess.check_output(["npm", "--version"], text=True).strip()
        print(f"  [✓] npm: {ver}")
    else:
        missing_tools.append("bun / npm")
        print("  [✗] bun / npm: 未找到前端包管理器")

    # 检查 clang (Xcode Command Line Tools)
    if check_tool("clang"):
        print("  [✓] clang: 已安装 (支持 Objective-C 原生编译)")
    else:
        missing_tools.append("clang (xcode-select)")
        print("  [✗] clang: 未找到 Xcode CLT")

    if missing_tools:
        print("\n" + "=" * 60)
        print("⚠️ 缺少以下构建工具，请按指引安装后重试：")
        for tool in missing_tools:
            print(f"  • {tool}")
        print("\n快速安装命令：")
        print("  1. Xcode CLT:  xcode-select --install")
        print("  2. Rust 语言:  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        print("  3. Bun 运行时: curl -fsSL https://bun.sh/install | bash")
        print("=" * 60)
        sys.exit(1)

    # 3. 准备伴生浏览器与资源
    print("\n>> 准备伴生浏览器环境...")
    pkg_browser_script = ROOT / "scripts/package_browser_macos.py"
    subprocess.run([sys.executable, str(pkg_browser_script)], check=True)

    # 4. 安装前端依赖与编译 UI
    print(">> 安装前端依赖与编译 Web UI...")
    os.chdir(ROOT)
    subprocess.run([pkg_mgr, "install"], check=True)
    subprocess.run([pkg_mgr, "run", "build"], check=True)

    # 5. 执行 Tauri 构建
    print("\n>> 编译 Tauri 2 macOS (Apple Silicon arm64) 应用...")
    conf_path = "src-tauri/tauri.macos.conf.json"
    if pkg_mgr == "bun":
        cmd = ["bun", "run", "tauri", "build", "--config", conf_path]
    else:
        cmd = ["npx", "tauri", "build", "--config", conf_path]
    subprocess.run(cmd, check=True)

    # 6. 验证产物
    print("\n" + "=" * 60)
    print("🎉 构建完成！正在扫描产物...")
    bundle_dir = ROOT / "src-tauri/target/release/bundle"
    macos_app = bundle_dir / "macos/Claude-Local.app"
    dmg_dir = bundle_dir / "dmg"

    if macos_app.is_dir():
        print(f"  [✓] App 应用程序: {macos_app}")
    else:
        print(f"  [!] 未找到 .app 包，请检查 target 目录")

    dmgs = list(dmg_dir.glob("*.dmg")) if dmg_dir.is_dir() else []
    for dmg in dmgs:
        digest = sha256_file(dmg)
        size_mb = dmg.stat().st_size / (1024 * 1024)
        print(f"  [✓] DMG 安装镜像: {dmg.name} ({size_mb:.1f} MB)")
        print(f"      SHA-256: {digest}")

    print("=" * 60)
    print("可以直接双击 DMG 进行安装，或者将 Claude-Local.app 拖入 /Applications 即可运行。")


if __name__ == "__main__":
    main()
