@echo off
echo 启动后端服务...
echo ====================================

:: 启动后端
start cmd /k "cd backend && run_backend.bat"

:: 启动后端API服务
start cmd /k "cd backend && python run.py --port 5000"

echo ====================================
echo 后端服务已启动: http://localhost:5000/api/status@echo off
echo 启动后端服务...
cd backend
start "后端服务" cmd /k "run_backend.bat"
start "后端API服务" cmd /k "python run.py --port 5000"
echo 后端服务已启动: http://localhost:5000/api/status