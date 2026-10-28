# 儿童学习助手项目说明

## 项目简介

本项目是一个面向家庭学习场景的双端系统，核心目标是帮助家长管理学习内容，帮助孩子按内容进行学习训练。

当前仓库包含：

- 家长端前端 Web 应用（React + TypeScript + Vite + Ant Design + Tailwind CSS）
- 后端 API 服务（FastAPI + Pydantic + SQLModel，JSON 文件存储）
- 文档体系（PRD、技术架构、数据库设计、接口规范）

## 主要能力

- 家长登录与鉴权
- 孩子档案管理（增删改查）
- 学习内容管理（增删改查、启用停用、按学习类型过滤、分页浏览）
- 汉字正文批量解析（忽略符号、按单字去重并独立存储）
- 英语正文批量导入（按换行/标点分割、空格不分割、词组去重并独立存储）
- 拼音练习（家长设置声母/单韵母/韵母/整体认读音节与是否带声调，系统按内置拼音表出卡片题）
- 汉字单字卡片学习
- 学习规则管理（题量、默认类型、孩子是否可自主选择）
- 算术练习（家长设置最小值/最大值/运算符，孩子随机出题并输入答案判分）
- 学习统计概览（总学习次数、正确率等）

## 技术栈

### 前端

- React
- TypeScript
- Vite
- Ant Design
- Tailwind CSS
- Vitest + Testing Library

### 后端

- Python 3.12
- FastAPI
- Pydantic
- SQLModel
- JSON 文件持久化
- Pytest

## 仓库结构

```text
.
├─ backend/
│  ├─ app/
│  ├─ tests/
│  ├─ requirements.txt
│  └─ run_tests.ps1
├─ frontend/
│  ├─ src/
│  ├─ package.json
│  └─ vite.config.ts
├─ docs/
│  ├─ PRD-儿童学习产品.md
│  ├─ 技术架构设计文档.md
│  ├─ db_design.md
│  ├─ db_storage_mapping.md
│  └─ api_spec.md
└─ README.md
```

## 环境要求

- Node.js >= 20（已在当前环境验证 Node 22）
- npm >= 10
- Python 3.12

## 快速启动

### 1. 启动后端

进入后端目录并安装依赖：

```powershell
cd backend
C:/Users/Administrator/me12/Scripts/python.exe -m pip install -r requirements.txt
```

启动 FastAPI 服务：

```powershell
C:/Users/Administrator/me12/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端会从 `backend/.env` 读取配置（若未配置则使用默认值）。可新建 `backend/.env`：

```env
MANAGEMENT_ACCOUNT_NAME=admin
MANAGEMENT_PASSWORD=dqshuchen
MANAGEMENT_DISPLAY_NAME=Administrator
MANAGEMENT_USER_ID=parent_admin
```

启动后访问：

- 健康检查: http://127.0.0.1:8000/health
- OpenAPI 文档: http://127.0.0.1:8000/docs

### 2. 启动前端

新开终端进入前端目录并安装依赖：

```powershell
cd frontend
npm install
```

启动开发服务器：

```powershell
npm run dev
```

默认访问地址：

- http://127.0.0.1:5173

## 本地联调流程

1. 启动后端服务（8000 端口）。
2. 在后端创建家长账号（可通过 API 或 `/docs` 调试页面）。
3. 在前端登录页输入账号密码登录。
4. 进入家长端工作台后，可进行孩子、内容、规则的 CRUD 操作。

新增汉字内容时，可在正文中输入多行文本，例如：

```text
- 根、茂、但、闻、响
- 苔、初、本、习
```

系统会忽略项目符号、标点和空白，按首次出现顺序去重，并将每个汉字保存为独立内容。再次导入已有汉字时会更新原记录。孩子选择汉字学习后，每次只展示一个汉字，点击“下一个”记录学习进度。

新增英语内容时，同样可在正文中输入多行文本，例如：

```text
apple, banana
good morning
well-known, don't
```

系统按换行与标点分割，空格不分割（`good morning` 作为整体保留），并保留连字符/撇号（`well-known`、`don't`），按首次出现顺序去重后，为每个词组保存为独立内容。再次导入已存在的词组时会更新原记录。

默认管理端账号（可被 `backend/.env` 覆盖）：

- 账号：admin
- 密码：dqshuchen

说明：

- 前端默认后端地址为 `http://127.0.0.1:8000/api/v1`。
- 如需修改地址，可在前端环境变量中配置 `VITE_API_BASE`。

## 测试

### 后端测试

```powershell
cd backend
C:/Users/Administrator/me12/Scripts/python.exe -m pytest -q
```

### 前端测试

```powershell
cd frontend
npm run test
```

### 前端构建验证

```powershell
cd frontend
npm run build
```

## 关键文档

- 产品需求文档: docs/PRD-儿童学习产品.md
- 技术架构文档: docs/技术架构设计文档.md
- 数据库设计文档: docs/db_design.md
- 接口规范文档: docs/api_spec.md

## 注意事项

- 当前阶段使用 JSON 文件存储，适合 MVP 和低并发场景。
- 不建议多实例同时写入同一份 JSON 数据目录。
- 若后续并发和数据规模增长，建议优先迁移到真实数据库。
