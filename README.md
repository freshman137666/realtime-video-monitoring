# 实时视频监控系统

这是一个基于Flask和Vue的前后端分离实时视频监控应用，使用YOLOv8进行对象检测和追踪，能够检测危险区域内的物体并发出警报。

## 项目结构

```
realtime-video-monitoring/
│
├── backend/             # Flask后端API
│   ├── app.py           # 主应用程序
│   └── ...
│
├── frontend/            # Vue前端应用
│   └── realtime-monitor-fronted/
│       ├── src/         # 源代码
│       ├── public/      # 静态资源
│       └── ...
│
├── uploads/             # 上传文件目录
├── danger_zone_config.json # 危险区域配置文件
├── start.bat            # 一键启动脚本
└── README.md            # 项目说明文档
```

## 功能特性

- 实时视频监控与对象检测
- 目标追踪与唯一ID分配
- 危险区域定义与可视化
- 危险区域入侵检测与告警
- 可自定义安全距离和停留时间阈值
- 支持上传视频或图片进行离线分析

## 技术栈

### 前端
- Vue 3
- Vue Router
- Vite

### 后端
- Flask
- Flask-CORS
- OpenCV
- YOLOv8

## 安装与使用

### 前提条件

- Python 3.8+
- Node.js 14+
- npm 6+

### 步骤

1. **安装后端依赖**

   ```bash
   cd backend
   pip install flask flask-cors opencv-python ultralytics
   ```

2. **安装前端依赖**

   ```bash
   cd frontend/realtime-monitor-fronted
   npm install
   ```

3. **启动应用**

   在Windows上，直接运行根目录下的`start.bat`脚本：
   
   ```bash
   start.bat
   ```

   或者手动启动：
   
   ```bash
   # 后端（在一个终端中）
   cd backend
   python app.py
   
   # 前端（在另一个终端中）
   cd frontend/realtime-monitor-fronted
   npm run dev
   ```

4. **访问应用**

   前端UI: http://localhost:5173
   后端API: http://localhost:5000/api/status

## 使用说明

1. 选择视频源（摄像头或上传文件）
2. 点击"编辑区域"按钮自定义危险区域
3. 调整安全距离和警报阈值
4. 查看底部告警信息区域获取实时告警

## 自定义危险区域

系统允许用户通过点击和拖动来自定义危险区域。进入编辑模式后：

- 点击并拖动区域点以调整位置
- 右键点击删除点
- 双击添加新点

## 告警机制

系统提供两种告警机制：

1. **停留告警**：当目标在危险区域内停留超过设定的阈值时间时触发
2. **接近告警**：当目标距离危险区域小于安全距离时触发

## 许可证

本项目采用MIT许可证
