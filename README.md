# SummaAudio 🎙️✨ - 一键音频转录与智能整理

SummaAudio 是一款强大的 Python 应用，它巧妙融合了 [ModelScope](https://github.com/modelscope/modelscope) 的语音识别技术和大型语言模型（LLM）的智能处理能力。无论是会议录音、语音笔记还是播客内容，SummaAudio 都能帮你快速将其转换为文字，并根据你的需求进行智能校对、总结或格式化整理。

![SummaAudio 一键转录](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/OneClick.jpg)
*SummaAudio 一键转录界面*

## 核心特性

*   🚀 **高效转录**：基于 ModelScope 先进的语音识别模型，快速准确地将音频文件转换为文本。
*   🧠 **智能处理**：集成 LLM（OpenAI API 兼容模型 / 本地 Ollama 模型），实现：
    *   文本自动校对与修正
    *   内容摘要与归纳
    *   自定义会议纪要生成
*   🗣️ **说话人分离**：支持识别并区分不同说话人（需模型支持）。
*   🛠️ **灵活配置**：提供详细的设置选项，轻松切换和管理 LLM及转录模型。
*   📝 **提示词管理**：内置提示词（Prompt）管理功能，方便用户自定义和优化处理效果。

![SummaAudio 文本归纳](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/summary.jpg)
*文本归纳与摘要功能*

![SummaAudio 设置界面](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/setting.jpg)
*灵活的LLM和服务配置*

## 典型应用场景

*   **会议记录**：一键生成结构清晰的会议纪要。
*   **采访整理**：快速提取访谈对话的关键内容。
*   **语音笔记转文字**：将零散的语音备忘录整理成可编辑文本。
*   **播客/视频字幕初稿**：为音视频内容生成文字稿。

## 环境要求

*   **Python**: 3.10+ (推荐 3.10 或 3.11 以获得最佳兼容性)
*   **Git**
*   详细依赖请参见 `requirements.txt`

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ByronLeeeee/SummaAudio.git
cd SummaAudio
```

### 2. 安装依赖

我们强烈推荐使用项目提供的 **一键安装脚本** (PowerShell)，它将为您自动创建虚拟环境并引导您完成 PyTorch 的安装。

```bash
# Windows PowerShell
.\setup.ps1
```
👉 **如果系统提示无法运行脚本**：请以管理员身份打开 PowerShell，执行 `Set-ExecutionPolicy RemoteSigned`，在提示中选择 `Y` (是)，然后再运行 `setup.ps1`。

![安装脚本指引](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/setup.jpg)
*一键安装脚本将引导您选择合适的 PyTorch 版本*

---

**或者，选择手动安装：**

**(a) 创建并激活虚拟环境 (推荐)**
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
```

**(b) 安装基础依赖**
```bash
pip install -r requirements.txt
```

**(c) 安装 PyTorch**
根据您的硬件情况（CPU 或 NVIDIA GPU CUDA 版本）选择合适的 PyTorch 安装命令。**请务必准确选择，否则可能导致运行错误！** 如果不确定，请选择 CPU 版本。

*   **CPU 版本:**
    ```bash
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    ```

*   **NVIDIA GPU (CUDA) 版本 (选择一个):**
    ```bash
    # 适用于 CUDA 11.8
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

    # 适用于 CUDA 12.1
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

    # 更多版本请参考 PyTorch 官网: https://pytorch.org/get-started/locally/
    ```
    *注意：`--force-reinstall` 通常在需要覆盖现有不兼容版本时使用，首次安装一般不需要。*

### 3. 运行应用

使用项目提供的 **一键运行脚本**：

```bash
# Windows PowerShell
.\run.ps1
```

---

**或者，手动运行：**
```bash
# 1. 确保虚拟环境已激活 (如果之前未激活)
#    Windows: .\.venv\Scripts\Activate.ps1
#    macOS/Linux: source .venv/bin/activate

# 2. 运行 Streamlit 应用
streamlit run app.py
```

## 使用指南

1.  **首次启动配置** ❗
    *   应用启动后，请务必先进入 **“设置”** 页面。
    *   根据您的需求配置 **LLM 模式**（Ollama 或 OpenAI）、ModelScope 缓存路径、Ollama 地址、OpenAI API 密钥等。
    ![首次使用提示](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/tips.jpg)
    *详细指引请参考应用首页*

2.  **提示词（Prompt）自定义**
    *   通过 **“提示词管理”** 页面，您可以查看、编辑或添加用于文本修正和归纳的提示词模板，打造个性化的智能助手。
    ![提示词管理](https://github.com/ByronLeeeee/SummaAudio/blob/main/screenshot/PromptManagerment.jpg)
    *打造您的专属AI助手*

3.  **开始转录与处理**
    *   **一键转录**：上传音频，选择处理流程，应用将自动完成转录、修正和归纳。
    *   **分步处理**：可分别使用“音频转录”、“修正文本”、“文本归纳”功能，进行更细致的操作。

## ⚠️ 重要注意事项

*   ⏳ **模型加载**：首次运行或切换模型时，ModelScope 和 LLM 模型的下载与加载可能需要较长时间，请耐心等待，并留意终端输出的进度信息，避免中途关闭。
*   💾 **内存需求**：同时运行转录模型和本地 LLM 模型（如 Ollama）对内存有较高要求。建议在拥有 **16GB 或以上物理内存** 的设备上运行，以获得流畅体验。
*   ⚙️ **PyTorch 版本**：请务必根据您的硬件（CPU/GPU 及 CUDA 版本）选择并安装正确的 PyTorch 版本，这是应用正常运行的关键。
*   🎵 **音频格式**：ModelScope 的转录模型默认主要支持 `.wav` 格式。若需处理其他格式（如 `.mp3`, `.m4a` 等），请确保已正确安装 [**FFmpeg**](https://www.ffmpeg.org/download.html) 并将其添加到系统环境变量 `PATH` 中。
*   🌐 **网络连接**：首次使用 ModelScope 模型或 OpenAI API 时，需要稳定的网络连接以下载模型或访问服务。

## 贡献

我们非常欢迎任何形式的贡献，包括但不限于：

*   Bug 反馈和功能建议
*   代码优化和新功能实现
*   文档改进

请通过 [GitHub Issues](https://github.com/ByronLeeeee/SummaAudio/issues) 或 Pull Requests 参与贡献。

## 开源许可

本项目基于 [GPL-3.0](https://github.com/ByronLeeeee/SummaAudio/blob/main/LICENSE) 开源许可证。