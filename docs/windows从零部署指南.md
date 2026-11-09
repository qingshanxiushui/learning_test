# Windows 从零部署指南

本文档说明在一台全新的 Windows 电脑上，从零搭建并运行本项目（儿童学习助手）的完整步骤。

## 1. 项目形态

- 后端：FastAPI + JSON 文件存储（无需数据库），运行在 `8000` 端口。
- 前端：React + Vite，构建产物已内置在 `backend/app/web`，由后端直接托管。
- 因此**只需启动后端，即可访问完整前端界面**（前后端一体化部署）。

## 2. 环境要求

| 软件    | 版本           | 用途     | 是否必需 |
| ------- | -------------- | -------- | -------- |
| Windows | 10 / 11（x64） | 操作系统 | 是       |
| Python  | 3.12           | 运行后端 | 是       |

> 本项目已包含构建好的前端静态文件（`backend/app/web`），因此**只需安装 Python 即可运行**，无需安装 Node.js。

## 3. 获取代码

本项目通过**直接拷贝目录**的方式分发，无需 git，且只需拷贝「运行」相关的目录与文件。

### 3.1 需要拷贝的内容

```text
child-learning/
└─ backend/
   ├─ app/                # 后端代码 + 前端构建产物（必须）
   │  ├─ api/             # 接口路由
   │  ├─ core/            # 配置与安全
   │  ├─ repositories/    # JSON 存储
   │  ├─ services/        # 业务逻辑
   │  ├─ web/             # 前端构建产物（必须，含 index.html 与 assets）
   │  ├─ main.py
   │  └─ models.py
   ├─ requirements.txt    # 后端依赖清单（必须）
   ├─ run_server.ps1      # 可选：启动脚本
   ├─ .env                # 可选：自定义账号等配置
   └─ data/               # 可选：已有数据（不拷贝则首次启动自动新建）
```

### 3.2 无需拷贝的内容

以下内容与运行无关，可省略：

- `frontend/` 前端源码及 `node_modules/`（仅修改前端时才会用到）
- `docs/` 文档（其中 `start_backend.bat` 为可选启动脚本，如需双击启动请一并拷贝）
- `backend/tests/` 后端测试
- `backend/run_tests.ps1` 测试脚本
- `backend/app/__pycache__/`、`.pytest_cache/`、`.ruff_cache/` 等缓存目录

以下命令均假设项目根目录为 `D:\child-learning`，请按实际路径替换。

## 4. 安装 Python 并准备后端

### 4.1 安装 Python 3.12

1. 打开 https://www.python.org/downloads/ ，下载 Windows 版 Python 3.12 安装包。
2. 运行安装包，**务必勾选 “Add python.exe to PATH”**，然后点击 “Install Now”。
3. 验证：

```powershell
python --version
# 应输出 Python 3.12.x
```

### 4.2 创建虚拟环境（推荐）

在项目根目录执行：

```powershell
cd D:\child-learning
python -m venv .venv
```

激活虚拟环境：

```powershell
.venv\Scripts\activate
```

> 若 PowerShell 提示“禁止运行脚本”，先执行 `Set-ExecutionPolicy -Scope Process RemoteSigned` 后再激活。

激活成功后，命令行提示符前会出现 `(.venv)`。

### 4.3 安装后端依赖

```powershell
cd D:\child-learning\backend
pip install -r requirements.txt
```

> 若下载慢，可使用国内镜像：
> `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### 4.4 配置环境变量（可选）

后端默认管理账号为 `admin`，密码 `dqshuchen`（见 `backend/app/core/config.py` 默认值），无需额外配置即可使用。

如需自定义，在 `backend` 目录新建 `.env` 文件：

```env
MANAGEMENT_ACCOUNT_NAME=admin
MANAGEMENT_PASSWORD=你的密码
MANAGEMENT_DISPLAY_NAME=Administrator
MANAGEMENT_USER_ID=parent_admin
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

## 5. 启动与访问

### 5.1 启动后端

**方式一：双击启动脚本（推荐）**

双击项目中的 `start_backend.bat`（位于 `docs/` 目录，部署时可把它拷贝到 `backend` 同级目录）即可启动后端。脚本开头可配置默认的绝对路径（`BACKEND_DIR` 与 `PYTHON`）；若默认路径不可用，会自动基于脚本位置回退查找，与当前所在目录无关。

**方式二：命令行启动**

在 `backend` 目录下执行（使用虚拟环境）：

```powershell
cd D:\child-learning\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- `--host 0.0.0.0`：允许本机与局域网内其它设备访问（家庭多设备场景推荐）。
- 只允许本机访问可改为 `--host 127.0.0.1`。

看到如下输出表示启动成功：

```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5.2 访问

- 本机访问：http://127.0.0.1:8000/ 或 http://localhost:8000/
- 局域网其它设备：http://<本机局域网IP>:8000/ （如 http://192.168.1.100:8000/）

> 首次启动时，后端会自动创建 `backend/data` 数据目录，并初始化默认家长账号 `admin`（密码 `dqshuchen`）。

## 6. 启动后验证

| 检查项   | 地址                         | 预期                 |
| -------- | ---------------------------- | -------------------- |
| 前端页面 | http://127.0.0.1:8000/       | 显示「拾光学堂」界面 |
| 健康检查 | http://127.0.0.1:8000/health | `{"status":"ok"}`    |
| API 文档 | http://127.0.0.1:8000/docs   | OpenAPI 调试页       |

## 7. 默认账号与数据

- 家长端登录账号：`admin`，密码：`dqshuchen`（可通过 `backend/.env` 覆盖）。
- 所有数据保存在 `backend/data` 下的 JSON 文件中：
  - `parent_users.json` 家长账号
  - `children.json` 孩子档案
  - `learning_rules.json` 学习规则
  - `math_settings.json` / `pinyin_settings.json` 算术/拼音设置
  - `contents/` 学习内容
  - `sessions/` 学习会话
- **备份即备份整个 `backend/data` 目录**；迁移到新机器时拷贝该目录即可保留数据。

## 8. 常用命令速查

```powershell
# 启动后端（在 backend 目录下执行）
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 运行后端测试
..\.venv\Scripts\python.exe -m pytest -q
```

## 9. 常见问题

### 9.1 仓库自带的 run_server.ps1 / run_tests.ps1 无法运行

这两个脚本里写死了开发机路径 `C:\Users\Administrator\me12\Scripts\python.exe`。新环境请改用虚拟环境命令（见第 5、8 章），或把脚本中的路径改为 `..\.venv\Scripts\python.exe`。

### 9.2 端口被占用

```powershell
netstat -ano | findstr :8000
```

找到占用进程 PID 后，用任务管理器结束该进程，或改用其它端口：

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 9.3 局域网设备无法访问

1. 确认后端以 `--host 0.0.0.0` 启动。
2. 在 Windows 防火墙中放行 `python.exe`（或 8000 端口）的入站连接。
3. 确认设备与本机处于同一局域网。

### 9.4 朗读语音环境设置

朗读依赖操作系统/浏览器安装的语音包：

- 浏览器需支持 Web Speech API（Edge / Chrome）。
- Windows 需在「设置 → 时间和语言 → 语言」中为英语勾选「语言包」和「文本到语音转换」。
- Chrome 的部分英语语音来自 Google 云，需联网。

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

## 10. 数据备份与恢复

- 备份：复制 `backend/data` 目录。
- 恢复：在新环境启动后端前，把备份的 `data` 目录放回 `backend/` 下（若目录不存在则首次启动会自动新建空数据）。

> 注意事项：本项目使用 JSON 文件存储，适合单实例、低并发场景；不建议多实例同时写入同一份 `data` 目录。
