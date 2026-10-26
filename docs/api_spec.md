# 儿童学习助手接口文档规范

## 1. 文档说明

- 文档名称：接口文档规范
- 文档版本：V1.0
- 文档日期：2026-08-20
- 适用范围：儿童学习助手 MVP
- 设计依据：产品需求文档、技术架构设计文档、数据库设计文档

## 2. 设计目标

本接口规范用于统一前后端协作方式，覆盖首版 MVP 所有核心业务接口，包括：

- 登录与鉴权
- 家长账户信息
- 孩子档案管理
- 学习内容管理
- 学习规则管理
- 学习会话管理
- 学习统计与结果查询

接口设计原则：

- 使用 RESTful 风格
- 使用 JSON 作为请求和响应格式
- 所有接口统一返回结构
- 明确区分需要鉴权和无需鉴权的接口
- 明确错误码、状态码和业务错误含义

## 3. 基础规范

### 3.1 Base URL

```text
/api/v1
```

### 3.2 请求头规范

所有 JSON 接口默认请求头：

```http
Content-Type: application/json
Accept: application/json
```

需要鉴权的接口必须携带：

```http
Authorization: Bearer <token>
```

### 3.3 鉴权规则

- 登录接口：无需 Token
- 其余家长端和孩子端业务接口：默认都需要 Token 鉴权
- Token 建议采用 JWT Bearer Token
- Token 中至少包含：`user_id`、`account_name`、`exp`

### 3.4 时间格式

- 所有时间字段统一使用 ISO 8601 UTC 格式
- 示例：`2026-08-20T10:00:00Z`

### 3.5 分页规范

列表接口统一支持以下分页参数：

- `page`：页码，从 1 开始
- `page_size`：每页条数，默认 10，最大 100

### 3.6 统一返回格式

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "req_123456"
}
```

失败响应：

```json
{
  "code": 40001,
  "message": "invalid request params",
  "data": null,
  "request_id": "req_123456"
}
```

字段说明：

- `code`：业务状态码，`0` 表示成功
- `message`：结果说明
- `data`：返回数据体，失败时可为 `null`
- `request_id`：请求追踪 ID，便于日志排查

## 4. HTTP 状态码规范

| HTTP 状态码 | 含义           | 使用场景               |
| ----------- | -------------- | ---------------------- |
| 200         | 成功           | 查询、更新、删除成功   |
| 201         | 已创建         | 创建资源成功           |
| 400         | 请求错误       | 参数错误、格式错误     |
| 401         | 未认证         | Token 缺失、无效、过期 |
| 403         | 无权限         | 无权访问该资源         |
| 404         | 资源不存在     | 查询目标不存在         |
| 409         | 冲突           | 唯一约束冲突、状态冲突 |
| 422         | 业务校验失败   | 字段规则不满足         |
| 500         | 服务器内部错误 | 未预期异常             |

## 5. 业务错误码定义

| 错误码 | 含义                       |
| ------ | -------------------------- |
| 0      | 成功                       |
| 40001  | 请求参数错误               |
| 40002  | JSON 格式错误              |
| 40003  | 分页参数非法               |
| 40101  | 未登录或 Token 缺失        |
| 40102  | Token 无效                 |
| 40103  | Token 已过期               |
| 40301  | 无权访问该资源             |
| 40401  | 家长账户不存在             |
| 40402  | 孩子档案不存在             |
| 40403  | 学习内容不存在             |
| 40404  | 学习规则不存在             |
| 40405  | 学习会话不存在             |
| 40406  | 会话题目不存在             |
| 40901  | 账号已存在                 |
| 40902  | 孩子默认规则已存在         |
| 40903  | 学习会话状态冲突           |
| 42201  | 字段校验失败               |
| 42202  | 内容类型非法               |
| 42203  | 学习题量超出允许范围       |
| 42204  | 当前内容不足以生成学习会话 |
| 42205  | 答题参数不合法             |
| 50001  | 服务器内部错误             |
| 50002  | 数据读写失败               |
| 50003  | JSON 存储损坏或校验失败    |

## 6. 鉴权接口

## 6.1 家长登录

- 接口：`POST /api/v1/auth/login`
- 鉴权：否
- 说明：家长使用账号登录，获取访问 Token

请求体：

```json
{
  "account_name": "parent_demo",
  "password": "123456"
}
```

请求参数说明：

| 字段         | 类型   | 必填 | 说明     |
| ------------ | ------ | ---- | -------- |
| account_name | string | 是   | 家长账号 |
| password     | string | 是   | 登录密码 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt_token",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": "uuid",
      "account_name": "parent_demo",
      "display_name": "家长"
    }
  },
  "request_id": "req_001"
}
```

错误码：

- `40001` 请求参数错误
- `40101` 账号或密码为空
- `40102` 账号或密码错误
- `50001` 服务器异常

## 6.2 获取当前登录用户信息

- 接口：`GET /api/v1/auth/me`
- 鉴权：是
- 说明：返回当前 Token 对应家长用户信息

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "account_name": "parent_demo",
    "display_name": "家长",
    "status": "active"
  },
  "request_id": "req_002"
}
```

错误码：

- `40101` 未携带 Token
- `40102` Token 无效
- `40103` Token 过期
- `40401` 用户不存在

## 7. 家长账户接口

## 7.1 创建家长账户

- 接口：`POST /api/v1/parents`
- 鉴权：否
- 说明：注册家长账户。若 MVP 暂不开放注册，可保留为后台初始化接口。

请求体：

```json
{
  "account_name": "parent_demo",
  "display_name": "家长",
  "password": "123456"
}
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "account_name": "parent_demo",
    "display_name": "家长",
    "status": "active",
    "created_at": "2026-08-20T10:00:00Z"
  },
  "request_id": "req_003"
}
```

错误码：

- `40001` 参数错误
- `40901` 账号已存在
- `42201` 字段校验失败

## 8. 孩子档案接口

## 8.1 获取孩子档案列表

- 接口：`GET /api/v1/children`
- 鉴权：是
- 说明：查询当前家长下的孩子列表

查询参数：

| 参数      | 类型   | 必填 | 说明                       |
| --------- | ------ | ---- | -------------------------- |
| page      | int    | 否   | 页码，默认 1               |
| page_size | int    | 否   | 每页条数，默认 10          |
| status    | string | 否   | 状态筛选：active、disabled |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "uuid",
        "name": "小明",
        "nickname": "明明",
        "age": 5,
        "grade_level": "幼儿园大班",
        "avatar_url": null,
        "status": "active",
        "created_at": "2026-08-20T10:00:00Z",
        "updated_at": "2026-08-20T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 1
    }
  },
  "request_id": "req_004"
}
```

错误码：

- `40101` 未登录
- `40003` 分页参数非法

## 8.2 创建孩子档案

- 接口：`POST /api/v1/children`
- 鉴权：是

请求体：

```json
{
  "name": "小明",
  "nickname": "明明",
  "age": 5,
  "grade_level": "幼儿园大班",
  "avatar_url": null
}
```

请求字段说明：

| 字段        | 类型   | 必填 | 说明       |
| ----------- | ------ | ---- | ---------- |
| name        | string | 是   | 姓名       |
| nickname    | string | 否   | 昵称       |
| age         | int    | 是   | 年龄       |
| grade_level | string | 否   | 年级或学段 |
| avatar_url  | string | 否   | 头像地址   |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "小明",
    "nickname": "明明",
    "age": 5,
    "grade_level": "幼儿园大班",
    "avatar_url": null,
    "status": "active",
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z"
  },
  "request_id": "req_005"
}
```

错误码：

- `40001` 参数错误
- `42201` 字段校验失败

## 8.3 获取孩子档案详情

- 接口：`GET /api/v1/children/{child_id}`
- 鉴权：是

路径参数：

| 参数     | 类型   | 必填 | 说明    |
| -------- | ------ | ---- | ------- |
| child_id | string | 是   | 孩子 ID |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "小明",
    "nickname": "明明",
    "age": 5,
    "grade_level": "幼儿园大班",
    "avatar_url": null,
    "status": "active",
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z"
  },
  "request_id": "req_006"
}
```

错误码：

- `40402` 孩子档案不存在
- `40301` 无权访问

## 8.4 更新孩子档案

- 接口：`PUT /api/v1/children/{child_id}`
- 鉴权：是

请求体：

```json
{
  "name": "小明",
  "nickname": "小明同学",
  "age": 6,
  "grade_level": "一年级",
  "avatar_url": null,
  "status": "active"
}
```

错误码：

- `40402` 孩子档案不存在
- `42201` 字段校验失败

## 8.5 删除孩子档案

- 接口：`DELETE /api/v1/children/{child_id}`
- 鉴权：是
- 说明：软删除孩子档案

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "deleted": true
  },
  "request_id": "req_007"
}
```

## 9. 学习内容接口

## 9.1 获取学习内容列表

- 接口：`GET /api/v1/children/{child_id}/contents`
- 鉴权：是

查询参数：

| 参数         | 类型   | 必填 | 说明                                               |
| ------------ | ------ | ---- | -------------------------------------------------- |
| page         | int    | 否   | 页码                                               |
| page_size    | int    | 否   | 每页条数                                           |
| content_type | string | 否   | 类型：character、classic、poem、idiom、englishWord |
| status       | string | 否   | 状态：enabled、disabled                            |
| keyword      | string | 否   | 标题或内容关键字                                   |

成功响应 `data.list` 单项示例：

```json
{
  "id": "uuid",
  "child_id": "uuid",
  "content_type": "poem",
  "title": "静夜思",
  "content_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
  "pronunciation": null,
  "meaning": "表达思乡之情",
  "example": null,
  "difficulty": 1,
  "status": "enabled",
  "sort_order": 0,
  "detail": {
    "poem_title": "静夜思",
    "author": "李白",
    "dynasty": "唐",
    "poem_lines": ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"],
    "poem_meaning": "表达诗人的思乡情感"
  },
  "created_at": "2026-08-20T10:00:00Z",
  "updated_at": "2026-08-20T10:00:00Z"
}
```

错误码：

- `40402` 孩子档案不存在
- `42202` 内容类型非法

## 9.2 创建学习内容

- 接口：`POST /api/v1/children/{child_id}/contents`
- 鉴权：是

请求体示例：

```json
{
  "content_type": "poem",
  "title": "静夜思",
  "content_text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
  "pronunciation": null,
  "meaning": "表达思乡之情",
  "example": null,
  "difficulty": 1,
  "status": "enabled",
  "sort_order": 0,
  "detail": {
    "poem_title": "静夜思",
    "author": "李白",
    "dynasty": "唐",
    "poem_lines": ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"],
    "poem_meaning": "表达诗人的思乡情感"
  }
}
```

请求字段说明：

- 通用字段：`content_type`、`title`、`content_text`、`pronunciation`、`meaning`、`example`、`difficulty`、`status`、`sort_order`
- 扩展字段：`detail`，根据不同 `content_type` 动态校验

成功响应返回完整内容对象。

错误码：

- `40402` 孩子不存在
- `42201` 字段校验失败
- `42202` 内容类型非法

## 9.2.1 批量导入汉字

- 接口：`POST /api/v1/children/{child_id}/contents/characters/batch`
- 鉴权：是
- 说明：从多行正文提取 CJK 汉字，忽略符号与空白，按首次出现顺序去重，并为每个字创建独立内容记录。

请求体不包含 `content_type` 和 `title`，其余字段作为共同属性复制到每个汉字。每条记录的 `title`、`content_text` 均为该字。若孩子已有同标题的活动汉字记录，则保留 ID 并覆盖共同属性。

```json
{
  "content_text": "- 根、茂、但、闻、响\n- 苔、初、本、习",
  "pronunciation": null,
  "meaning": null,
  "example": null,
  "difficulty": 1,
  "status": "enabled",
  "sort_order": 0,
  "detail": {}
}
```

成功响应的 `data` 包含 `list`、`created_count`、`updated_count` 和 `total_count`。正文未包含汉字时返回 `42206`。

## 9.2.2 批量导入英语单词

- 接口：`POST /api/v1/children/{child_id}/contents/english/batch`
- 鉴权：是
- 说明：从多行正文切分英语内容：以换行与标点为分隔，**空格不分割**（空格分隔的词组作为整体保留，如 `good morning`）；同时保留单词内部的连字符/撇号（如 `well-known`、`don't`）；忽略纯数字片段，按首次出现顺序去重（不区分大小写），并为每个词组创建独立内容记录。

请求体不包含 `content_type` 和 `title`，其余字段作为共同属性复制到每个单词。每条记录的 `title`、`content_text` 均为该单词。若孩子已有同标题（忽略大小写）的活动单词记录，则保留 ID 并覆盖共同属性。

```json
{
  "content_text": "apple, banana\norange pear apple",
  "pronunciation": null,
  "meaning": null,
  "example": null,
  "difficulty": 1,
  "status": "enabled",
  "sort_order": 0,
  "detail": {}
}
```

成功响应的 `data` 包含 `list`、`created_count`、`updated_count` 和 `total_count`。正文未包含英语单词时返回 `42206`。

## 9.3 获取学习内容详情

- 接口：`GET /api/v1/children/{child_id}/contents/{content_id}`
- 鉴权：是

错误码：

- `40402` 孩子不存在
- `40403` 学习内容不存在

## 9.4 更新学习内容

- 接口：`PUT /api/v1/children/{child_id}/contents/{content_id}`
- 鉴权：是

请求体：与创建接口一致，支持全量更新。

错误码：

- `40403` 学习内容不存在
- `42201` 字段校验失败

## 9.5 软删除学习内容

- 接口：`DELETE /api/v1/children/{child_id}/contents/{content_id}`
- 鉴权：是

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "deleted": true
  },
  "request_id": "req_008"
}
```

## 9.6 更新学习内容状态

- 接口：`PATCH /api/v1/children/{child_id}/contents/{content_id}/status`
- 鉴权：是

请求体：

```json
{
  "status": "disabled"
}
```

错误码：

- `40403` 学习内容不存在
- `42201` 状态字段非法

## 10. 学习规则接口

## 10.1 获取学习规则

- 接口：`GET /api/v1/children/{child_id}/rules`
- 鉴权：是

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "child_id": "uuid",
    "question_count": 5,
    "default_content_types": ["character", "poem"],
    "allow_child_select_types": true,
    "status": 1,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z"
  },
  "request_id": "req_009"
}
```

错误码：

- `40404` 学习规则不存在

## 10.2 创建学习规则

- 接口：`POST /api/v1/children/{child_id}/rules`
- 鉴权：是
- 说明：若系统约定创建孩子时自动生成规则，则该接口可仅用于初始化或后台工具。

请求体：

```json
{
  "question_count": 5,
  "default_content_types": ["character", "poem"],
  "allow_child_select_types": true,
  "status": 1
}
```

错误码：

- `40902` 孩子默认规则已存在
- `42203` 学习题量超出允许范围

## 10.3 更新学习规则

- 接口：`PUT /api/v1/children/{child_id}/rules`
- 鉴权：是

请求体：

```json
{
  "question_count": 10,
  "default_content_types": ["character", "classic", "poem"],
  "allow_child_select_types": true,
  "status": 1
}
```

错误码：

- `40404` 学习规则不存在
- `42203` 学习题量超出允许范围
- `42202` 内容类型非法

## 10.4 算术设置

## 10.4.1 获取算术设置

- 接口：`GET /api/v1/children/{child_id}/math-settings`
- 鉴权：是
- 说明：返回该孩子的算术设置；未设置时 `data` 返回 `null`。

成功响应（未设置）：

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

成功响应（已设置）：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "child_id": "uuid",
    "min_value": 1,
    "max_value": 20,
    "operators": ["add", "subtract", "multiply", "divide"],
    "status": 1
  }
}
```

## 10.4.2 保存算术设置

- 接口：`PUT /api/v1/children/{child_id}/math-settings`
- 鉴权：是
- 说明：upsert（存在则更新，不存在则创建）。

请求体：

```json
{
  "min_value": 1,
  "max_value": 20,
  "operators": ["add", "subtract", "multiply", "divide"],
  "status": 1
}
```

错误码：

- `42207` 算术设置不合法（min ≥ max、运算符为空/非法）

## 11. 学习会话接口

## 11.1 开始学习会话

- 接口：`POST /api/v1/children/{child_id}/sessions`
- 鉴权：是
- 说明：根据孩子选择类型和当前规则，生成本轮学习会话与题目快照

请求体：

```json
{
  "selected_content_types": ["poem", "character"]
}
```

请求字段说明：

| 字段                   | 类型     | 必填 | 说明                                                 |
| ---------------------- | -------- | ---- | ---------------------------------------------------- |
| selected_content_types | string[] | 否   | 孩子主动选择的学习类型，不传或空数组表示使用默认规则 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": "uuid",
      "child_id": "uuid",
      "selected_content_types": ["poem", "character"],
      "total_questions": 5,
      "completed_questions": 0,
      "answered_questions": 0,
      "correct_questions": 0,
      "accuracy_rate": 0,
      "session_status": "in_progress",
      "started_at": "2026-08-20T10:00:00Z"
    },
    "questions": [
      {
        "id": "uuid",
        "question_order": 1,
        "content_type": "poem",
        "question_type": "next_line_choice",
        "question_stem": "“床前明月光”下一句是什么？",
        "question_options": ["疑是地上霜", "举头望明月", "低头思故乡"]
      }
    ]
  },
  "request_id": "req_010"
}
```

汉字内容生成 `character_card`，`question_stem` 为单个汉字且 `question_options` 为空。卡片通过查看接口推进，不调用答题接口。

算术内容生成 `math_arithmetic`，`question_stem` 为形如 `3 + 5 = ?` 的算式，`question_options` 为空，孩子通过输入整数作答（见 11.3）。

错误码：

- `40402` 孩子不存在
- `40404` 学习规则不存在
- `40407` 算术设置不存在
- `42202` 内容类型非法
- `42204` 当前内容不足以生成学习会话

## 11.2 获取学习会话详情

- 接口：`GET /api/v1/children/{child_id}/sessions/{session_id}`
- 鉴权：是

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": "uuid",
      "child_id": "uuid",
      "selected_content_types": ["poem", "character"],
      "total_questions": 5,
      "answered_questions": 1,
      "correct_questions": 1,
      "accuracy_rate": 100,
      "session_status": "in_progress",
      "started_at": "2026-08-20T10:00:00Z",
      "finished_at": null
    },
    "questions": [
      {
        "id": "uuid",
        "question_order": 1,
        "content_type": "poem",
        "question_type": "next_line_choice",
        "question_stem": "“床前明月光”下一句是什么？",
        "question_options": ["疑是地上霜", "举头望明月", "低头思故乡"],
        "correct_answer": "疑是地上霜",
        "answer_explanation": "出自《静夜思》第二句"
      }
    ]
  },
  "request_id": "req_011"
}
```

错误码：

- `40405` 学习会话不存在

## 11.3 提交单题答案

- 接口：`POST /api/v1/children/{child_id}/sessions/{session_id}/answers`
- 鉴权：是
- 说明：提交某一道题的答案，返回判题结果和当前进度

请求体：

```json
{
  "session_question_id": "uuid",
  "user_answer": "疑是地上霜",
  "answer_duration_ms": 4200
}
```

请求字段说明：

| 字段                | 类型   | 必填 | 说明        |
| ------------------- | ------ | ---- | ----------- |
| session_question_id | string | 是   | 会话题目 ID |
| user_answer         | string | 是   | 孩子作答    |
| answer_duration_ms  | int    | 否   | 答题耗时    |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_question_id": "uuid",
    "is_correct": true,
    "correct_answer": "疑是地上霜",
    "answer_explanation": "出自《静夜思》第二句",
    "progress": {
      "answered_questions": 1,
      "total_questions": 5,
      "correct_questions": 1,
      "accuracy_rate": 100
    }
  },
  "request_id": "req_012"
}
```

错误码：

- `40405` 学习会话不存在
- `40406` 会话题目不存在
- `40903` 会话状态冲突
- `42205` 答题参数不合法

## 11.3.1 记录汉字卡片已查看

- 接口：`POST /api/v1/children/{child_id}/sessions/{session_id}/questions/{question_id}/viewed`
- 鉴权：是
- 说明：仅用于 `character_card`。首次调用记录 `viewed_at` 和查看耗时，重复调用保持幂等。

```json
{
  "view_duration_ms": 1800
}
```

响应进度包含 `completed_questions` 和 `total_questions`。非卡片题目返回 `42206`。

## 11.4 完成学习会话

- 接口：`POST /api/v1/children/{child_id}/sessions/{session_id}/complete`
- 鉴权：是
- 说明：所有选择题已作答、所有汉字卡片已查看后结束本轮学习并返回结果汇总

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": "uuid",
      "session_status": "completed",
      "total_questions": 5,
      "completed_questions": 5,
      "answered_questions": 5,
      "correct_questions": 4,
      "accuracy_rate": 80,
      "started_at": "2026-08-20T10:00:00Z",
      "finished_at": "2026-08-20T10:05:00Z"
    },
    "summary": {
      "need_review_contents": [
        {
          "content_id": "uuid",
          "title": "静夜思",
          "content_type": "poem"
        }
      ]
    }
  },
  "request_id": "req_013"
}
```

错误码：

- `40405` 学习会话不存在
- `40903` 会话状态冲突
- `40904` 尚有题目或卡片未完成

## 11.5 获取学习会话列表

- 接口：`GET /api/v1/children/{child_id}/sessions`
- 鉴权：是

查询参数：

| 参数           | 类型   | 必填 | 说明                              |
| -------------- | ------ | ---- | --------------------------------- |
| page           | int    | 否   | 页码                              |
| page_size      | int    | 否   | 每页条数                          |
| session_status | string | 否   | in_progress、completed、abandoned |
| start_date     | string | 否   | 开始日期，ISO 8601                |
| end_date       | string | 否   | 结束日期，ISO 8601                |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": "uuid",
        "child_id": "uuid",
        "selected_content_types": ["poem", "character"],
        "total_questions": 5,
        "answered_questions": 5,
        "correct_questions": 4,
        "accuracy_rate": 80,
        "session_status": "completed",
        "started_at": "2026-08-20T10:00:00Z",
        "finished_at": "2026-08-20T10:05:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total": 20
    }
  },
  "request_id": "req_014"
}
```

## 11.6 获取学习会话结果详情

- 接口：`GET /api/v1/children/{child_id}/sessions/{session_id}/result`
- 鉴权：是
- 说明：面向家长端查看本次学习结果详情

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session": {
      "id": "uuid",
      "total_questions": 5,
      "answered_questions": 5,
      "correct_questions": 4,
      "accuracy_rate": 80,
      "session_status": "completed",
      "started_at": "2026-08-20T10:00:00Z",
      "finished_at": "2026-08-20T10:05:00Z"
    },
    "answers": [
      {
        "session_question_id": "uuid",
        "question_order": 1,
        "question_stem": "“床前明月光”下一句是什么？",
        "user_answer": "疑是地上霜",
        "correct_answer": "疑是地上霜",
        "is_correct": true,
        "answer_explanation": "出自《静夜思》第二句"
      }
    ]
  },
  "request_id": "req_015"
}
```

## 12. 统计接口

## 12.1 获取孩子学习统计概览

- 接口：`GET /api/v1/children/{child_id}/stats/overview`
- 鉴权：是
- 说明：返回家长端首页所需统计信息

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_sessions": 20,
    "sessions_last_7_days": 5,
    "average_accuracy_rate": 82.5,
    "content_count": 60,
    "recent_session": {
      "id": "uuid",
      "finished_at": "2026-08-20T10:05:00Z",
      "accuracy_rate": 80
    }
  },
  "request_id": "req_016"
}
```

## 12.2 获取孩子按类型学习统计

- 接口：`GET /api/v1/children/{child_id}/stats/by-content-type`
- 鉴权：是

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "content_type": "poem",
      "total_answers": 20,
      "correct_answers": 16,
      "accuracy_rate": 80
    },
    {
      "content_type": "character",
      "total_answers": 10,
      "correct_answers": 9,
      "accuracy_rate": 90
    }
  ],
  "request_id": "req_017"
}
```

## 12.3 获取孩子薄弱内容列表

- 接口：`GET /api/v1/children/{child_id}/stats/weak-contents`
- 鉴权：是

查询参数：

| 参数         | 类型   | 必填 | 说明                       |
| ------------ | ------ | ---- | -------------------------- |
| limit        | int    | 否   | 返回条数，默认 10，最大 50 |
| content_type | string | 否   | 类型筛选                   |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "content_id": "uuid",
      "title": "静夜思",
      "content_type": "poem",
      "wrong_count": 3,
      "last_wrong_at": "2026-08-20T10:02:00Z"
    }
  ],
  "request_id": "req_018"
}
```

## 13. 数据字典约定

### 13.1 content_type 枚举

| 值          | 含义 |
| ----------- | ---- |
| character   | 汉字 |
| classic     | 国学 |
| poem        | 古诗 |
| idiom       | 成语 |
| englishWord | 英语 |

### 13.2 session_status 枚举

| 值          | 含义   |
| ----------- | ------ |
| in_progress | 进行中 |
| completed   | 已完成 |
| abandoned   | 已放弃 |

### 13.3 content_status 枚举

| 值       | 含义 |
| -------- | ---- |
| enabled  | 启用 |
| disabled | 停用 |

### 13.4 parent_user_status / child_status 枚举

| 值       | 含义 |
| -------- | ---- |
| active   | 正常 |
| disabled | 停用 |

## 14. 鉴权接口汇总

无需 Token：

- `POST /api/v1/auth/login`
- `POST /api/v1/parents`

需要 Token：

- `GET /api/v1/auth/me`
- `GET /api/v1/children`
- `POST /api/v1/children`
- `GET /api/v1/children/{child_id}`
- `PUT /api/v1/children/{child_id}`
- `DELETE /api/v1/children/{child_id}`
- `GET /api/v1/children/{child_id}/contents`
- `POST /api/v1/children/{child_id}/contents`
- `GET /api/v1/children/{child_id}/contents/{content_id}`
- `PUT /api/v1/children/{child_id}/contents/{content_id}`
- `DELETE /api/v1/children/{child_id}/contents/{content_id}`
- `PATCH /api/v1/children/{child_id}/contents/{content_id}/status`
- `GET /api/v1/children/{child_id}/rules`
- `POST /api/v1/children/{child_id}/rules`
- `PUT /api/v1/children/{child_id}/rules`
- `POST /api/v1/children/{child_id}/sessions`
- `GET /api/v1/children/{child_id}/sessions`
- `GET /api/v1/children/{child_id}/sessions/{session_id}`
- `POST /api/v1/children/{child_id}/sessions/{session_id}/answers`
- `POST /api/v1/children/{child_id}/sessions/{session_id}/complete`
- `GET /api/v1/children/{child_id}/sessions/{session_id}/result`
- `GET /api/v1/children/{child_id}/stats/overview`
- `GET /api/v1/children/{child_id}/stats/by-content-type`
- `GET /api/v1/children/{child_id}/stats/weak-contents`

## 15. 结论

本接口规范已经覆盖当前 MVP 的全部核心业务边界，满足以下要求：

- 所有业务接口完整
- 每个接口明确请求参数、响应体、错误码
- 清晰区分登录接口与 Token 鉴权接口
- 全部接口遵循 RESTful 风格
- 统一使用标准 JSON 返回格式

后续若继续推进，建议下一步基于本文档输出 OpenAPI 结构定义或后端 Pydantic Schema 设计文档。
