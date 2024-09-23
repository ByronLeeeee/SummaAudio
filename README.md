# SummaAudio
 
## 概览
SummaAudio是一个基于Python的库，结合了[Modelscope](https://github.com/modelscope/modelscope)和LLM的能力，用于快速转录音频文件，并按需整理成文本。

常见应用场景：
- **语音转文本**：高效将音频文件转换为文本，适用于语音识别、语音转写等场景。
- **会议记录**：自动生成会议纪要。
- **对话录音整理**：轻松提取对话内容。

LLM模型支持：
- 各类**OpenAI**兼容的API
- 本地**OLLAMA**模型 

## 依赖
` Python 3.8+`

## 安装
```bash
git clone https://github.com/ByronLeeeee/SummaAudio.git
cd SummaAudio
```

推荐使用一键安装脚本安装
```bash
setup.ps1
```

安装脚本会自动创建虚拟环境`.venv`，请手动选择合适的`Pytorch`版本（CUDA/CPU），非NVDIA用户，请选择CPU。

## 运行
```bash
run.ps1
```

或手动激活虚拟环境后运行

```bash
cd \SummaAudio\.venv\Scripts\
Activate.ps1
cd ..\..\
streamlit run app.py
```

## 注意事项
1. 模型加载时间较长，请耐心等待。
2. 首次使用时，需要在Modelscope下载转录模型，耗时较长，请留意终端显示的下载进度，避免误关闭软件。
3. 转录模型默认只支持**wav**格式。如要支持其他音频格式，请手动下载安装[**FFmpeg**](https://www.ffmpeg.org/download.html)，并设置好环境变量。

## 贡献
欢迎随时提供反馈和建议。

## 开源协议
本项目采用 GNU Affero通用公共许可证 (AGPL-3.0)。