@echo off
echo 实时视频监控系统启动脚本
echo ====================================

:: 启动后端
echo 正在启动后端服务...
start cmd /k "cd backend && run_backend.bat"

:: 等待后端启动
echo 等待后端启动 (5秒)...
timeout /t 5 /nobreak > nul

:: 启动前端
echo 正在启动前端服务...
cd frontend\realtime-monitor-fronted
start cmd /k "npm run dev"

echo ====================================
echo 服务已启动:
echo 前端: http://localhost:5173
echo 后端: http://localhost:5000/api/status
echo ====================================

:: 返回到根目录
cd ..\.. 