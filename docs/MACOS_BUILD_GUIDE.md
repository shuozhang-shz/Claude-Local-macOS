# Claude-Local macOS (Apple Silicon M系列芯片) 适配与构建指南

本项目已完成从 Windows 平台向 **macOS (Apple Silicon arm64)** 的完整适配改造。以下是详细的环境准备、构建步骤及架构说明。

---

## 🛠️ 一、构建环境前置要求

在苹果芯片 (M1/M2/M3/M4) 的 Mac 上编译和运行本项目，需要安装以下基础工具：

### 1. Xcode Command Line Tools
编译 macOS Objective-C 原生底层库（AppKit、Security、CoreLocation 等）必需：
```bash
xcode-select --install
```

### 2. Rust 工具链 (Apple Silicon 原生 aarch64)
后端基于 Rust 语言开发：
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustc --version  # 确认输出包含 aarch64-apple-darwin
```

### 3. Bun 运行时（推荐）或 Node.js
用于前端构建与依赖管理：
```bash
# 推荐使用 Bun（速度最快）
curl -fsSL https://bun.sh/install | bash
source "$HOME/.bashrc" # 或 ~/.zshrc

# 或者使用 Homebrew 安装 Node.js
brew install node
```

### 4. Python 3.10+
用量分析与额度审计引擎需要系统 Python：
```bash
python3 --version
```

---

## 🚀 二、一键构建命令

你可以直接使用 macOS 已经自带的 Python 运行全链路构建脚本：

### 快速一键打包（生成 .app 与 .dmg）
```bash
# 方式一：直接运行 Python 自动化脚本（推荐，自带依赖扫描与哈希校验）
python3 scripts/build_macos.py

# 方式二：使用 npm/bun 脚本
bun run build:macos
# 或
npm run build:macos

# 方式三：直接执行 Bash 脚本
bash scripts/build-macos.sh
```

### 开发模式实时调试
```bash
bun install
bun run tauri dev
```

### 构建产物路径
构建完成后，安装包将输出在：
- **可执行应用包**：`src-tauri/target/release/bundle/macos/Claude-Local.app`
- **磁盘镜像安装包**：`src-tauri/target/release/bundle/dmg/Claude-Local_0.3.1_aarch64.dmg`

---

## 🧩 三、macOS 适配关键改造清单

| 模块 | Windows 原版实现 | macOS (Apple Silicon) 适配改造 |
| :--- | :--- | :--- |
| **应用容器配置** | `tauri.windows.conf.json` (NSIS exe) | 新增/完善 `tauri.macos.conf.json`，目标设为 `dmg` 和 `app`，支持 Apple 签名与 entitlements |
| **应用图标** | `icon.ico` (Win32 多分辨率) | 引入 `icon.icns`，同时保留统一的星环视觉设计 |
| **原生系统桥接** | Win32 API (`windows-sys`, 注册表, 句柄) | Objective-C 模块 (`src-tauri/native/*.m`)，通过 `cc` 编译链接 `AppKit`、`Security`、`LocalAuthentication`、`CoreLocation`、`SystemConfiguration` |
| **凭据安全** | Windows 凭据管理器 | Apple 钥匙串服务 (`SecKeychainUnlock` / `Keychain.m`)，支持原生授权与零凭据暴露 |
| **伴生指纹浏览器** | `chrome.exe` + Win32 快捷方式注册 | `Browser.app` (内置 `Contents/MacOS/Chromium`) + arm64 原生 `CCBrowser` 调度器 (`CCBrowser.c`) + LaunchServices 注册 |
| **浏览器资源打包** | PowerShell 脚本打包 zip | 新建 `scripts/package-browser-macos.sh`，支持自动校验 arm64 架构与 ditto 打包 |
| **CLI 安装与更新** | PowerShell 脚本 (`claude-cli.ps1`) | 原生 Zsh 脚本 (`claude-cli.sh`)，全面兼容 Homebrew Cask、npm 全局、官方独立二进制 |
| **前端安装提示** | 硬编码 `irm ... \| iex` (PowerShell) | 动态探测平台：macOS 自动呈现 `curl -fsSL https://claude.ai/install.sh \| bash` 及 Terminal 终端指引 |
| **多实例唤醒** | Win32 消息循环 `--browser` 路由 | Tauri 单实例插件新增 macOS 分支，支持 `--browser` 伴生浏览器静默唤醒 |
| **窗口拖拽与控件** | Windows 原生顶栏 | 采用 macOS 规范的 `Overlay` 标题栏，原生红黄绿三色红绿灯交通灯按钮完美融入 |

---

## 🔒 四、权限与系统设置说明

1. **钥匙串权限**：当需要切换账号或进行深度数据清理时，macOS 会通过系统标准弹窗请求钥匙串解锁权限，所有凭据仅在本地内存中流转，绝不上传云端。
2. **位置与时区**：由于 macOS 采用系统级权限沙箱，修改时区需通过管理员授权（osascript 认证），关闭定位服务会直接引导至 macOS 系统设置（隐私与安全性 -> 定位服务）。
