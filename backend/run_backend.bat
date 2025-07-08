@echo off
echo 启动视频监控后端API服务...
echo ====================================

:: 切换到当前目录
cd /d "%~dp0"

:: 激活conda环境
call conda activate object_detection

:: 启动后端API服务
python app.py

pause 