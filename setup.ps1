# 设置脚本编码为UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

# 询问用户选择设备类型
Write-Host "开始安装SummaAudio"
Write-Host "开始安装步骤，安装库耗时较长，请耐心等待。"
Write-Host "请选择设备类型："
Write-Host "1. CUDA - 11.8"
Write-Host "2. CUDA - 12.1"
Write-Host "3. CUDA - 12.4"
Write-Host "4. CPU"
$choice = Read-Host "请填写相应序号"

# 创建Python虚拟环境
Write-Host "正在创建Python虚拟环境..."
python -m venv .venv
Write-Host "创建Python虚拟环境完成！"

# 激活虚拟环境
Write-Host "正在激活Python虚拟环境..."
.\.venv\Scripts\Activate.ps1

# 更改pip镜像源为阿里云
Write-Host "正在更改pip镜像源为阿里云..."
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装requirements.txt中的依赖
Write-Host "正在更新pip"
pip install -U pip --upgrade
Write-Host "正在安装依赖..."
pip install -r requirements.txt
Write-Host "依赖安装完成！"

# 根据用户选择安装对应版本的PyTorch和torchaudio
if ($choice -eq "1") {
    Write-Host "正在安装CUDA118版本的PyTorch/torchaudio/torchvision..."
    pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu118 --force-reinstall
}
elseif ($choice -eq "2") {
    Write-Host "正在安装CUDA121版本的PyTorch/torchaudio/torchvision..."
    pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
}
elseif ($choice -eq "3") {
    Write-Host "正在安装CUDA124版本的PyTorch/torchaudio/torchvision..."
    pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu124 --force-reinstall
}
elseif ($choice -eq "4") {
    Write-Host "正在安装CPU版本的PyTorch/torchaudio/torchvision..."
    pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cpu --force-reinstall
}
else {
    Write-Host "无效的选择，脚本将退出。" 
    exit 
}

Write-Host "安装完成!"