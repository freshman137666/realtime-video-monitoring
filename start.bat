@echo off
echo 实时视频监控系统启动脚本
echo ====================================

:: 启动后端
echo 正在启动后端服务...
start "后端服务" cmd /k "cd backend && run_backend.bat"

:: 启动后端API服务
start "后端API服务" cmd /k "cd backend && python run.py --port 5000"


:: 启动前端
echo 正在启动前端服务...
cd frontend\realtime-monitor-fronted
start "前端服务" cmd /k "npm run dev"

echo ====================================
echo 服务已启动:
echo 前端: http://localhost:5173
echo 后端: http://localhost:5000/api/status
echo ====================================

:: 返回到根目录
cd ..\.. 