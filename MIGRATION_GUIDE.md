# 迁移指南：从单体Flask应用到前后端分离架构

本指南提供了从原始单体Flask应用迁移到新的前后端分离架构的步骤和说明。

## 迁移概述

原始项目是一个基于Flask的单体应用，通过Jinja2模板渲染前端页面。新架构将项目分为：
1. Flask后端API（`backend/app.py`）
2. Vue前端应用（`frontend/realtime-monitor-fronted`）

## 文件映射关系

以下表格展示了原始项目文件与新项目结构的映射关系：

| 原始文件/目录               | 新项目对应                                      | 说明                                       |
|--------------------------|---------------------------------------------|------------------------------------------|
| `webapp.py`              | `backend/app.py`                            | 后端API，移除了模板渲染，改为返回JSON数据      |
| `templates/index.html`   | `frontend/realtime-monitor-fronted/src/views/MonitorView.vue` | 监控页面的Vue组件版本 |
| `templates/base.html`    | `frontend/realtime-monitor-fronted/src/App.vue` | Vue应用的主布局 |
| `static/assets/`         | `frontend/realtime-monitor-fronted/src/assets/` | 静态资源 |
| `danger_zone_config.json`| 保持不变，由后端管理                               | 危险区域配置 |
| `uploads/`               | 保持不变，由后端管理                               | 上传文件存储目录 |

## 功能对应关系

| 原始功能                   | 新项目对应                                      | 变化                                       |
|--------------------------|---------------------------------------------|------------------------------------------|
| 视频上传和处理              | 通过API接口 `/api/upload`                     | 前端上传文件，后端处理并返回结果URL            |
| 实时视频流                  | 通过API接口 `/api/video_feed`                 | 保持相同功能，但通过API提供                    |
| 危险区域编辑                | 前端组件 + API接口                              | 用户体验改进，更直观的交互                    |
| 参数设置                   | 前端UI组件 + API接口                            | 更现代的滑块UI，实时设置                      |
| 告警显示                   | 前端组件 + API轮询                              | 动态更新，无需刷新页面                        |

## 如何恢复到原始版本

如果您需要恢复到原始的单体应用版本，只需：

1. 停止前后端服务
2. 确保您有原始的`webapp.py`和`templates/`目录的备份
3. 将这些备份文件恢复到项目根目录

## 迁移步骤详解

如果您想手动执行迁移，可以按照以下步骤操作：

### 1. 准备工作

```bash
# 创建备份
cp webapp.py webapp.py.bak
cp -r templates templates.bak

# 创建新的目录结构
mkdir -p backend frontend
```

### 2. 后端迁移

```bash
# 创建后端应用
cp webapp.py backend/app.py

# 安装所需依赖
pip install flask-cors
```

然后修改`backend/app.py`，将所有模板渲染改为返回JSON数据。

### 3. 前端创建

```bash
# 创建Vue项目
cd frontend
npm init vue@latest
# 按照提示操作...

# 安装依赖
cd realtime-monitor-fronted
npm install
```

### 4. 启动新系统

```bash
# 在一个终端启动后端
cd backend
python app.py

# 在另一个终端启动前端
cd frontend/realtime-monitor-fronted
npm run dev
```

## 故障排除

如果您在迁移过程中遇到问题：

1. **跨域问题**：确保后端正确配置了CORS
2. **API连接失败**：检查API端点URL是否正确
3. **视频流无法显示**：确保前端正确引用了视频流URL

## 性能比较

新架构相比原始单体应用有以下优势：

1. **更好的用户体验**：前端使用Vue的响应式特性，页面交互更流畅
2. **更高的开发效率**：前后端可以独立开发和部署
3. **更好的可扩展性**：可以轻松添加新功能和扩展现有功能

## 联系与支持

如有任何问题或需要帮助，请创建GitHub Issue或联系项目维护者。 