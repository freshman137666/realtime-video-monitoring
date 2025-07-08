@echo off
echo 启动视频监控后端API服务...
echo ====================================

:: 切换到当前目录
cd /d "%~dp0"

:: 解决 "OMP: Error #15" 警告
echo 设置环境变量以允许多个OpenMP运行时...
set KMP_DUPLICATE_LIB_OK=TRUE

:: 激活conda环境
echo 激活conda环境: video_monitor...
call conda activate video_monitor

:: 检查conda环境是否激活成功
if %errorlevel% neq 0 (
    echo 错误: 激活conda环境 'video_monitor' 失败。
    echo 请确保已正确安装conda并且环境存在。
    pause
    exit /b
)

:: 启动后端API服务
echo 启动Flask后端服务...
python app.py

pause 