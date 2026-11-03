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
- 汉字/国学/古诗/成语出题逐字标注拼音（带声调）
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

## 朗读语音环境设置

学习端（孩子端）的「朗读」按钮基于浏览器 Web Speech API 实现，实际发声依赖操作系统或浏览器安装的语音包。若点击「朗读」没有声音（常见于英语卡片），通常是系统缺少对应语言的语音包，请按下面步骤配置。

### 1. Windows 语音包设置（以 Edge 为例）

1. 打开「设置 → 时间和语言 → 语言」（部分版本为「语言和区域」）。
2. 若列表中没有英语，点击「添加语言」，选择 "English (United States)" 并添加。
3. 点击英语语言右侧的「…」→「语言选项」。
4. 在「可选语言功能」中，勾选并安装：
   - **语言包**（基础依赖）
   - **文本到语音转换**（关键，朗读发声依赖此项）
5. 其余「基本语音识别」「增强的语音识别」「手写」与朗读无关，无需勾选；其中「增强的语音识别」约 102 MB，不建议安装。
6. 等待下载安装完成。

中文朗读同理：若中文卡片朗读无声，请确认「中文（简体，中国）」下的「文本到语音转换」已安装。

### 2. 浏览器说明

- 推荐使用 Microsoft Edge 或 Google Chrome 等支持 Web Speech API 的浏览器。
- Edge / Safari / Firefox 使用操作系统安装的语音包；Chrome 桌面版的部分语音来自 Google 云服务，需要联网。
- 安装完语音包后，请**刷新学习页面或重启浏览器**，让浏览器重新加载语音列表后再点击「朗读」。

### 3. 注意事项

- 朗读必须在用户点击后触发，浏览器自动播放策略下不允许自动发声（本功能由点击「朗读」按钮触发，符合要求）。
- 发音质量取决于系统/浏览器安装的语音包；未安装对应语言语音时，点击会给出「朗读失败」提示。
- 英语卡片使用 `en-US` 语音，汉字/国学/古诗/成语卡片使用 `zh-CN` 语音。
- 朗读语速已在代码中固定为慢速（便于孩子跟读）；多音字发音以语音包默认读音为准，可能与拼音标注不一致，属已知限制。

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
