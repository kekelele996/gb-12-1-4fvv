# 留学申请管理系统

一个面向留学中介机构和自助留学学生的全流程申请管理平台，帮助用户管理目标院校、准备申请材料、跟踪申请进度。

## 快速启动（Docker Compose）

### 一键部署

```bash
# 1. 复制环境变量配置文件
cp .env.example .env

# 2. 启动所有服务（可能需要等待1-2分钟）
docker compose up -d

# 3. 查看服务状态
docker compose ps

# 4. 查看日志（可选）
docker compose logs -f
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:8012 | 留学申请管理系统前端界面 |
| 后端API | http://localhost:3012 | Django REST API 服务 |
| API文档 | http://localhost:3012/api/docs/ | Swagger 接口文档 |
| MinIO控制台 | http://localhost:9010 | 对象存储管理控制台 |

## 主要功能

### 1. 院校数据库
- 维护全球主要院校信息（校名、国家、城市、排名、优势专业、申请截止日期、学费范围）
- 支持按国家、排名区间、专业方向筛选院校
- 院校详情页展示申请要求（GPA、语言成绩、标化考试要求）

### 2. 申请项目管理
- 学生创建申请项目（目标院校 + 申请专业 + 申请轮次）
- 自动关联院校申请要求和截止日期
- 申请状态流转：规划中 → 准备材料 → 已提交 → 等待结果 → 已录取/已拒/候补

### 3. 文书管理
- 为每个申请项目管理文书材料（PS、RL、CV、Essay）
- 支持在线编辑和版本管理（记录每次修改的版本历史）
- 使用 diff-match-patch 实现版本对比
- 留学顾问可在线批注和反馈修改意见

### 4. 材料清单与进度跟踪
- 每个申请项目生成标准化材料清单
- 学生逐项上传材料并标记已完成
- 自动计算材料准备进度百分比

### 5. 时间线管理
- 为每个申请项目生成关键时间节点时间线
- 支持语言考试日期、文书截止、网申截止、面试日期、预计出结果日期
- 临近截止日期自动发送提醒通知

### 6. 顾问协作
- 留学顾问与学生绑定后可查看学生所有申请项目
- 顾问可在文书上添加批注
- 顾问可为学生推荐选校方案（含推荐理由）
- 站内消息沟通系统

### 7. 申请数据看板
- 学生个人申请总览：已申请院校数量、各状态分布、录取率统计
- 机构管理后台：所有学生的申请汇总数据
- 使用 ECharts 实现数据可视化

## 本地开发

### 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- MinIO（可选，本地开发可用默认文件存储）

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（复制 .env.example 的相关配置）
# 确保数据库配置正确

# 5. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser

# 7. 启动开发服务器
python manage.py runserver 0.0.0.0:3012
```

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 或构建生产版本
npm run build
```

## 技术栈

| 分类 | 技术 | 版本 |
|------|------|------|
| **前端框架** | React | 18.x |
| **前端语言** | TypeScript | 5.x |
| **UI组件库** | Ant Design | 5.x |
| **构建工具** | Vite | 5.x |
| **路由** | React Router | 6.x |
| **状态管理** | Zustand | 4.x |
| **HTTP客户端** | Axios | 1.x |
| **图表** | ECharts | 5.x |
| **版本对比** | diff-match-patch | 1.x |
| **后端框架** | Django | 4.x |
| **API框架** | Django REST Framework | 3.x |
| **数据库** | PostgreSQL | 14+ |
| **对象存储** | MinIO | 最新版 |
| **认证** | JWT (djangorestframework-simplejwt) | - |
| **容器化** | Docker | - |
| **编排工具** | Docker Compose | - |

## 项目目录结构

```
留学申请管理系统/
├── backend/                          # Django 后端项目
│   ├── analytics/                    # 数据分析模块（数据看板API）
│   ├── applications/                 # 申请项目管理模块
│   ├── config/                       # Django 项目配置
│   │   ├── settings.py               # 项目设置
│   │   ├── urls.py                   # 主路由配置
│   │   └── wsgi.py                   # WSGI 入口
│   ├── documents/                    # 文书管理模块（版本控制、批注）
│   ├── materials/                    # 材料清单模块
│   ├── messages/                     # 站内消息模块
│   ├── timelines/                    # 时间线模块（通知）
│   ├── universities/                 # 院校数据库模块
│   ├── users/                        # 用户模块（认证、角色）
│   ├── Dockerfile                    # 后端 Dockerfile
│   ├── manage.py                     # Django 管理脚本
│   └── requirements.txt              # Python 依赖
├── frontend/                         # React 前端项目
│   ├── src/
│   │   ├── api/                      # API 请求封装
│   │   ├── components/               # 公共组件
│   │   ├── pages/                    # 页面组件
│   │   │   ├── Login.tsx             # 登录/注册页面
│   │   │   ├── Dashboard.tsx         # 数据看板
│   │   │   ├── Universities.tsx      # 院校列表
│   │   │   ├── Applications.tsx      # 申请项目
│   │   │   ├── Documents.tsx         # 文书管理
│   │   │   ├── Timeline.tsx          # 时间线
│   │   │   ├── Messages.tsx          # 消息中心
│   │   │   └── Profile.tsx           # 个人中心
│   │   ├── store/                    # 状态管理
│   │   ├── styles/                   # 样式文件
│   │   ├── types/                    # TypeScript 类型定义
│   │   ├── App.tsx                   # 应用入口
│   │   └── main.tsx                  # 渲染入口
│   ├── Dockerfile                    # 前端 Dockerfile
│   ├── nginx.conf                    # Nginx 配置
│   ├── package.json                  # 前端依赖
│   ├── tsconfig.json                 # TypeScript 配置
│   └── vite.config.ts                # Vite 配置
├── .env.example                      # 环境变量示例
├── docker-compose.yml                # Docker Compose 编排
└── README.md                         # 项目文档
```

## 环境变量说明

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

### 数据库配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `POSTGRES_DB` | 数据库名 | study_abroad |
| `POSTGRES_USER` | 数据库用户名 | postgres |
| `POSTGRES_PASSWORD` | 数据库密码 | postgres123 |
| `POSTGRES_HOST` | 数据库主机 | db |
| `POSTGRES_PORT` | 数据库端口 | 5432 |

### Django 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DJANGO_SECRET_KEY` | Django 密钥 | 随机生成字符串 |
| `DJANGO_DEBUG` | 调试模式 | False |
| `DJANGO_ALLOWED_HOSTS` | 允许的主机 | * |

### MinIO 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MINIO_ENDPOINT` | MinIO 地址 | minio:9000 |
| `MINIO_ACCESS_KEY` | 访问密钥 | minioadmin |
| `MINIO_SECRET_KEY` | 秘密密钥 | minioadmin |
| `MINIO_BUCKET_NAME` | 存储桶名 | study-abroad |

### JWT 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `JWT_ACCESS_TOKEN_LIFETIME` | Access Token 有效期 | 60（分钟） |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh Token 有效期 | 1440（分钟） |

### 邮件配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `EMAIL_HOST` | SMTP 服务器 | smtp.example.com |
| `EMAIL_PORT` | SMTP 端口 | 587 |
| `EMAIL_HOST_USER` | 邮箱用户名 | your-email@example.com |
| `EMAIL_HOST_PASSWORD` | 邮箱密码 | your-password |
| `EMAIL_USE_TLS` | 使用 TLS | True |

## Docker 部署说明

### 服务说明

`docker-compose.yml` 配置了以下服务：

| 服务名 | 容器名 | 端口映射 | 说明 |
|--------|--------|----------|------|
| `db` | `study-abroad-db` | `5505:5432` | PostgreSQL 数据库 |
| `minio` | `study-abroad-minio` | `9009:9000`, `9010:9001` | MinIO 对象存储 |
| `backend` | `study-abroad-backend` | `3012:8000` | Django 后端 |
| `frontend` | `study-abroad-frontend` | `8012:80` | Nginx 托管的前端 |

### 数据卷

| 卷名 | 用途 |
|------|------|
| `study_abroad_postgres_data` | 持久化 PostgreSQL 数据 |
| `study_abroad_minio_data` | 持久化 MinIO 存储 |

### 常用 Docker 命令

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f [服务名]

# 进入后端容器
docker exec -it study-abroad-backend bash

# 执行数据库迁移（容器内）
python manage.py migrate

# 创建超级用户（容器内）
python manage.py createsuperuser

# 清理所有资源（含数据卷）
docker compose down -v
```

### 常见问题

**Q: 后端启动失败，显示数据库连接错误？**
A: 确保数据库容器已完全启动（需要 30-60 秒），检查 `.env` 中的数据库配置是否正确。

**Q: 前端无法连接后端 API？**
A: 检查前端 `nginx.conf` 中的 API 代理配置，默认代理到 `http://backend:8000`。

**Q: 文件上传失败？**
A: 检查 MinIO 服务是否正常运行，访问 http://localhost:9010 查看 MinIO 控制台（默认账号: minioadmin / minioadmin）。

**Q: 容器网络无法互通？**
A: 所有服务使用名为 `study-abroad-network` 的自定义网络，通过容器名进行内部通信。

## License

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
