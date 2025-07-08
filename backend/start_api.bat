@echo off
echo 正在启动实时视频监控后端API服务...
echo.

rem 激活Conda环境
call conda activate object_detection
if %errorlevel% neq 0 (
    echo 错误：无法激活Conda环境，请确保已安装Conda并创建了名为object_detection的环境。
    exit /b 1
)

echo Conda环境已激活: object_detection
echo.

rem 启动Flask应用
echo 启动Flask应用服务器...
python run.py

rem 如果Flask应用意外退出，保持窗口打开以查看错误信息
pause 