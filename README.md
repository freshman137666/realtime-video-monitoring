# 实时视频监控系统

本系统是一个基于YOLOv8和Flask、Vue的全栈实时视频监控应用，旨在提供一个灵活、可扩展的框架，用于集成各种计算机视觉任务，如危险区域入侵检测、人脸识别、异常行为分析等。

## 环境配置指南

为了确保项目顺利运行，请遵循以下步骤配置您的开发环境。推荐使用 [Anaconda](https://www.anaconda.com/products/distribution) 来管理Python环境。

### 1. 克隆项目

```bash
git clone [你的项目Git仓库地址]
cd realtime-video-monitoring
```

### 2. 配置后端环境 (Python)

项目后端依赖于特定的Python包，尤其是`dlib`在Windows上直接使用`pip`安装可能会失败。我们强烈建议使用`conda`来创建和管理环境。

**第一步：创建并激活Conda环境**

打开Anaconda Prompt或您的终端，使用以下命令创建一个名为 `video_monitor` 的Python 3.9环境（如果已有该环境，请直接激活）。

```bash
conda create -n video_monitor python=3.9 -y
conda activate video_monitor
```

**第二步：安装 `dlib` (关键步骤)**

`dlib` 是 `face-recognition` 库的核心依赖，且编译过程复杂。请务必使用`conda`从`conda-forge`渠道安装预编译好的版本，以避免错误。

```bash
conda install -c conda-forge dlib -y
```

**第三步：安装其余Python依赖**

当`dlib`安装成功后，再使用`pip`安装`requirements.txt`中剩余的依赖包。

```bash
pip install -r requirements.txt
```

### 3. 配置前端环境 (Node.js)

项目前端是基于Vue.js和Vite构建的。请确保您已安装 [Node.js](https://nodejs.org/) (推荐LTS版本)。

进入前端项目目录，安装npm依赖。

```bash
cd frontend/realtime-monitor-fronted
npm install
```

### 4. 运行项目

你需要打开两个终端：

*   **终端1 (启动后端)**:
    ```bash
    conda activate video_monitor
    cd backend
    python run.py
    ```

*   **终端2 (启动前端)**:
    ```bash
    cd frontend/realtime-monitor-fronted
    npm run dev
    ```

服务启动后，在浏览器中打开前端地址 (通常是 `http://localhost:5173`) 即可访问系统。

---

## 项目概述

这是一个基于Flask和Vue的前后端分离实时视频监控应用，使用YOLOv8进行对象检测和追踪，能够检测危险区域内的物体并发出警报。

## 项目结构

```
realtime-video-monitoring/
│
├── backend/                       # Flask后端API
│   ├── app/                       # 应用模块
│   │   ├── routes/                # API路由
│   │   │   ├── api.py             # 基础API端点
│   │   │   ├── config.py          # 配置相关API
│   │   │   └── video.py           # 视频处理API
│   │   ├── services/              # 业务逻辑
│   │   │   ├── alerts.py          # 警报管理
│   │   │   ├── danger_zone.py     # 危险区域配置
│   │   │   ├── detection.py       # 对象检测
│   │   │   └── video.py           # 视频流处理
│   │   └── utils/                 # 工具函数
│   │       └── geometry.py        # 几何计算
│   ├── uploads/                   # 上传文件目录
│   ├── run.py                     # 应用入口
│   └── run_backend.bat            # 后端启动脚本
│
├── frontend/                      # Vue前端应用
│   └── realtime-monitor-fronted/
│       ├── src/                   # 源代码
│       │   ├── assets/            # 静态资源
│       │   ├── components/        # 组件
│       │   ├── router/            # 路由配置
│       │   ├── stores/            # 状态管理
│       │   ├── views/             # 页面视图
│       │   ├── App.vue            # 根组件
│       │   └── main.js            # 入口文件
│       ├── public/                # 公共资源
│       └── index.html             # HTML模板
│
├── danger_zone_config.json        # 危险区域配置文件
├── start.bat                      # 一键启动脚本
├── requirements.txt               # Python依赖列表
└── README.md                      # 项目说明文档
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
- Pinia (状态管理)
- Vite

### 后端
- Flask
- Flask-CORS
- OpenCV
- YOLOv8 (Ultralytics)
- NumPy

## 安装与使用

### 前提条件

- Python 3.8+
- Node.js 14+
- npm 6+

### 环境配置

1. **创建并激活Conda环境**

   ```bash
   conda create -n video_monitor python=3.8
   conda activate video_monitor
   ```

2. **安装后端依赖**

   ```bash
   pip install -r requirements.txt
   ```

   或手动安装核心依赖：

   ```bash
   pip install flask flask-cors opencv-python ultralytics numpy
   ```

3. **安装前端依赖**

   ```bash
   cd frontend/realtime-monitor-fronted
   npm install
   ```

### 启动应用

#### 方法一：一键启动（推荐）

在Windows上，直接运行根目录下的`start.bat`脚本：

```bash
start.bat
```

这将同时启动前端和后端服务。

#### 方法二：分别启动

1. **启动后端**

   ```bash
   # 方式1：使用启动脚本
   cd backend
   run_backend.bat
   
   # 方式2：直接使用Python
   cd backend
   python run.py
   
   # 方式3：使用Flask命令（开发模式）
   cd backend
   set FLASK_APP=app
   set FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000
   ```

2. **启动前端**

   ```bash
   cd frontend/realtime-monitor-fronted
   npm run dev
   ```

### 访问应用

- 前端UI: http://localhost:5173
- 后端API状态: http://localhost:5000/api/status
- 视频流地址: http://localhost:5000/api/video_feed

## 使用说明

1. **视频源选择**
   - 点击"摄像头"按钮使用实时摄像头
   - 点击"上传视频"按钮上传本地视频或图片文件

2. **危险区域设置**
   - 点击"编辑区域"按钮进入编辑模式
   - 点击并拖动区域点以调整位置
   - 右键点击删除点
   - 双击添加新点
   - 点击"保存区域"保存设置

3. **参数调整**
   - 使用滑块调整"安全距离"（像素）
   - 使用滑块调整"警报阈值"（秒）
   - 点击"应用设置"保存参数

4. **告警信息**
   - 查看底部告警信息区域获取实时告警

## 告警机制

系统提供两种告警机制：

1. **停留告警**：当目标在危险区域内停留超过设定的阈值时间时触发
2. **接近告警**：当目标距离危险区域小于安全距离时触发

## 常见问题排查

1. **摄像头无法打开**
   - 检查摄像头设备是否正常连接
   - 确认没有其他应用程序占用摄像头

2. **模型加载失败**
   - 确认`yolov8n.pt`文件存在于项目根目录和backend目录下

3. **前端无法连接后端**
   - 确认后端服务正常运行（http://localhost:5000/api/status）
   - 检查浏览器控制台是否有CORS错误

4. **视频处理性能问题**
   - 考虑使用更小的YOLOv8模型（如yolov8n.pt）
   - 降低视频分辨率或帧率

## 许可证

本项目采用MIT许可证
