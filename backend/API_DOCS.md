# 实时视频监控系统 - 后端API文档

## 1. 概述

本文档详细介绍了实时视频监控系统的后端API接口。前端开发人员可以参考本文档与后端进行集成。

### 基本信息

- **基础URL**: `http://服务器IP:5000/api`
- **Swagger UI**: `http://服务器IP:5000/api/`（可在线查看和测试所有API）

## 2. API接口详情

### 2.1 视频流相关API

#### 2.1.1 获取实时视频流

- **URL**: `/video/feed/{stream_id}`
- **方法**: `GET`
- **参数**: 
  - `stream_id`: 视频流ID，可以是任意字符串，用于标识不同的摄像头
- **返回**: MJPEG视频流
- **示例**:
  ```html
  <!-- 在前端HTML中使用 -->
  <img src="http://服务器IP:5000/api/video/feed/cam1" alt="视频流">
  ```

#### 2.1.2 获取危险区域配置

- **URL**: `/video/config`
- **方法**: `GET`
- **返回**: JSON对象，包含危险区域坐标、安全距离和停留时间阈值
- **示例响应**:
  ```json
  {
    "danger_zone": [[100, 700], [600, 700], [600, 800], [100, 800]],
    "safety_distance": 100,
    "loitering_threshold": 2.0
  }
  ```

#### 2.1.3 更新危险区域配置

- **URL**: `/video/config`
- **方法**: `PUT`
- **请求体**: JSON对象，包含新的危险区域坐标、安全距离和停留时间阈值
- **示例请求**:
  ```json
  {
    "danger_zone": [[150, 700], [650, 700], [650, 800], [150, 800]],
    "safety_distance": 120,
    "loitering_threshold": 1.5
  }
  ```
- **返回**: 更新后的配置

### 2.2 报警相关API

#### 2.2.1 获取所有报警

- **URL**: `/alerts`
- **方法**: `GET`
- **返回**: 报警列表
- **示例响应**:
  ```json
  [
    {
      "id": 1,
      "alert_type": "入侵危险区域",
      "description": "人员进入危险区域并停留2.5秒",
      "image_path": "alert_20250708123456.jpg",
      "created_at": "2025-07-08T12:34:56",
      "is_handled": false
    },
    {
      "id": 2,
      "alert_type": "靠近危险区域",
      "description": "人员距离危险区域边缘不足安全距离",
      "image_path": "alert_20250708123556.jpg",
      "created_at": "2025-07-08T12:35:56",
      "is_handled": true
    }
  ]
  ```

#### 2.2.2 创建新报警

- **URL**: `/alerts`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "alert_type": "入侵危险区域",
    "description": "人员进入危险区域",
    "image_path": "某图片路径.jpg"
  }
  ```
- **返回**: 新创建的报警记录

#### 2.2.3 标记报警为已处理

- **URL**: `/alerts/handle/{id}`
- **方法**: `PUT`
- **参数**:
  - `id`: 报警ID
- **返回**: 更新后的报警记录

### 2.3 人脸识别API

#### 2.3.1 注册人脸

- **URL**: `/face/register`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "student_id": "学生ID",
    "image": "图片的Base64编码"
  }
  ```
- **返回**:
  ```json
  {
    "message": "人脸注册成功"
  }
  ```

#### 2.3.2 识别人脸

- **URL**: `/face/recognize`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "image": "图片的Base64编码"
  }
  ```
- **返回**:
  ```json
  {
    "recognized": true,
    "student_id": "学生ID",
    "confidence": 0.85
  }
  ```

## 3. 与前端集成指南

### 3.1 视频流集成

前端可以通过简单地将`<img>`标签的`src`属性设置为视频流URL来显示实时视频：

```html
<img src="http://服务器IP:5000/api/video/feed/cam1" alt="视频流">
```

如果需要处理视频流加载错误，可以添加错误处理：

```javascript
const videoImg = document.getElementById('videoStream');
videoImg.onerror = function() {
  console.error('视频流加载失败');
  // 显示错误信息或尝试重新连接
};
```

### 3.2 人脸识别集成

下面是一个使用前端摄像头捕获图像并发送到人脸识别API的示例：

```javascript
async function captureFace() {
  const video = document.getElementById('webcam');
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  
  // 获取图像的Base64编码
  const imageBase64 = canvas.toDataURL('image/jpeg').split(',')[1];
  
  try {
    const response = await fetch('http://服务器IP:5000/api/face/recognize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ image: imageBase64 })
    });
    
    const result = await response.json();
    
    if (result.recognized) {
      console.log(`识别成功！学生ID: ${result.student_id}`);
    } else {
      console.log('未识别到已知人脸');
    }
  } catch (error) {
    console.error('人脸识别失败:', error);
  }
}
```

### 3.3 报警处理集成

下面是一个获取并显示报警信息的示例：

```javascript
async function fetchAlerts() {
  try {
    const response = await fetch('http://服务器IP:5000/api/alerts');
    const alerts = await response.json();
    
    // 显示报警信息
    const alertsList = document.getElementById('alerts-list');
    alertsList.innerHTML = '';
    
    alerts.forEach(alert => {
      const alertItem = document.createElement('div');
      alertItem.className = 'alert-item';
      alertItem.innerHTML = `
        <h3>${alert.alert_type}</h3>
        <p>${alert.description}</p>
        <img src="http://服务器IP:5000/uploads/${alert.image_path}" alt="报警截图">
        <p>时间: ${new Date(alert.created_at).toLocaleString()}</p>
        <button onclick="handleAlert(${alert.id})" ${alert.is_handled ? 'disabled' : ''}>
          ${alert.is_handled ? '已处理' : '标记为已处理'}
        </button>
      `;
      alertsList.appendChild(alertItem);
    });
  } catch (error) {
    console.error('获取报警信息失败:', error);
  }
}

async function handleAlert(alertId) {
  try {
    await fetch(`http://服务器IP:5000/api/alerts/handle/${alertId}`, {
      method: 'PUT'
    });
    // 刷新报警列表
    fetchAlerts();
  } catch (error) {
    console.error('处理报警失败:', error);
  }
}
```

## 4. 注意事项

1. **跨域资源共享(CORS)**：后端已配置CORS，允许前端从任何源访问API。
2. **图片路径**：报警图片存储在后端服务器的`uploads`目录中，需要通过适当的URL访问。
3. **视频流性能**：视频流使用MJPEG格式，对网络带宽要求较高，前端可以考虑降低刷新频率或分辨率以提高性能。
4. **错误处理**：前端应该妥善处理API请求可能出现的错误，提供友好的用户体验。

## 5. API在线文档

完整的API文档可以通过访问Swagger UI获取：`http://服务器IP:5000/api/`

在这个页面上，你可以：
- 浏览所有可用的API端点
- 查看详细的请求和响应模式
- 直接在浏览器中测试API调用
- 下载OpenAPI规范文件，用于其他工具集成 