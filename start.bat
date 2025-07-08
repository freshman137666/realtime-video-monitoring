@echo off
echo 启动实时视频监控系统...
echo ====================================

:: 切换到当前目录
cd /d "%~dp0"

:: 启动后端API服务
start cmd /k "cd backend && python run.py --port 5000"

:: 等待后端API启动
echo 等待后端API启动...
timeout /t 5

:: 启动前端服务
start cmd /k "cd frontend/realtime-monitor-fronted && npm run dev"

echo ====================================
echo 系统已启动:
echo - 后端API: http://localhost:5000/api/status
echo - 前端UI: http://localhost:5173
echo ====================================
echo 按任意键打开前端界面...
pause
start http://localhost:5173 