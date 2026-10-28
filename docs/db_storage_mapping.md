# 儿童学习助手 JSON 存储映射文档

## 1. 文档说明

- 文档名称：JSON 存储映射文档
- 版本：V1.0
- 日期：2026-08-20
- 目的：补充数据库设计文档，说明逻辑表如何映射到当前 MVP 的 JSON 文件存储结构

## 2. 设计背景

当前技术架构明确规定底层不使用数据库服务，而采用 JSON 文件作为持久化介质。因此，数据库设计需要区分两层：

- 逻辑层：按实体关系设计表、字段、索引和约束
- 物理层：将这些逻辑实体映射到 JSON 文件和目录结构

本文件只描述 JSON 物理存储层约定。

## 3. 目录结构约定

```text
data/
  parent_users.json
  children.json
  learning_rules.json
  math_settings.json
  pinyin_settings.json
  contents/
    character.json
    classic.json
    poem.json
    idiom.json
    english_word.json
  sessions/
    learning_sessions.json
    session_questions.json
    answer_records.json
```

## 4. 文件映射关系

| 逻辑实体                | JSON 文件                              | 说明                           |
| ----------------------- | -------------------------------------- | ------------------------------ |
| parent_user             | `data/parent_users.json`               | 家长账户集合                   |
| child_profile           | `data/children.json`                   | 孩子档案集合                   |
| learning_rule           | `data/learning_rules.json`             | 学习规则集合                   |
| math_settings           | `data/math_settings.json`              | 算术设置集合（每孩子一条）     |
| pinyin_settings         | `data/pinyin_settings.json`            | 拼音设置集合（每孩子一条）     |
| learning_content        | `data/contents/*.json`                 | 按内容类型拆分主数据           |
| learning_content_detail | `data/contents/*.json`                 | 与主数据合并存储在同一条记录中 |
| learning_session        | `data/sessions/learning_sessions.json` | 学习会话摘要                   |
| session_question        | `data/sessions/session_questions.json` | 会话题目快照                   |
| answer_record           | `data/sessions/answer_records.json`    | 作答明细                       |

## 5. JSON 记录结构建议

### 5.1 parent_users.json

```json
[
  {
    "id": "uuid",
    "account_name": "parent_demo",
    "display_name": "家长",
    "status": "active",
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.2 children.json

```json
[
  {
    "id": "uuid",
    "parent_user_id": "uuid",
    "name": "小明",
    "nickname": "明明",
    "age": 5,
    "grade_level": "幼儿园大班",
    "avatar_url": null,
    "status": "active",
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.3 learning_rules.json

```json
[
  {
    "id": "uuid",
    "child_id": "uuid",
    "question_count": 5,
    "default_content_types": ["character", "poem"],
    "allow_child_select_types": 1,
    "status": 1,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.4 contents/\*.json

说明：

- 每个内容类型单独一个文件。
- 主表字段和扩展字段建议合并存储为单条 JSON 记录，避免 JSON 场景下额外维护 detail 文件的一致性成本。

```json
[
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
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.5 learning_sessions.json

```json
[
  {
    "id": "uuid",
    "child_id": "uuid",
    "selected_content_types": ["poem", "character"],
    "total_questions": 5,
    "completed_questions": 5,
    "answered_questions": 5,
    "correct_questions": 4,
    "accuracy_rate": 80.0,
    "session_status": "completed",
    "started_at": "2026-08-20T10:00:00Z",
    "finished_at": "2026-08-20T10:05:00Z",
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:05:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.6 session_questions.json

```json
[
  {
    "id": "uuid",
    "session_id": "uuid",
    "content_id": "uuid",
    "content_type": "poem",
    "question_type": "next_line_choice",
    "question_stem": "“床前明月光”下一句是什么？",
    "question_options": ["疑是地上霜", "举头望明月", "低头思故乡"],
    "correct_answer": "疑是地上霜",
    "answer_explanation": "出自《静夜思》第二句",
    "question_order": 1,
    "content_snapshot": {
      "title": "静夜思",
      "author": "李白",
      "poem_lines": ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
    },
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.7 answer_records.json

汉字卡片也存储在 `session_questions.json`，其 `question_type` 为 `character_card`、`question_stem` 为单个汉字、`question_options` 为空。查看后在题目记录写入 `viewed_at` 和 `view_duration_ms`，不会生成 `answer_records.json` 记录。

`learning_sessions.json` 中的 `completed_questions` 表示已作答选择题与已查看卡片的合计；`answered_questions` 仅表示真实作答数。

```json
[
  {
    "id": "uuid",
    "session_question_id": "uuid",
    "session_id": "uuid",
    "child_id": "uuid",
    "user_answer": "疑是地上霜",
    "correct_answer": "疑是地上霜",
    "is_correct": 1,
    "answer_duration_ms": 4200,
    "answered_at": "2026-08-20T10:01:00Z",
    "created_at": "2026-08-20T10:01:00Z",
    "updated_at": "2026-08-20T10:01:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

### 5.8 math_settings.json

```json
[
  {
    "id": "uuid",
    "child_id": "uuid",
    "min_value": 1,
    "max_value": 20,
    "operators": ["add", "subtract", "multiply", "divide"],
    "status": 1,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-20T10:00:00Z",
    "deleted_at": null,
    "is_deleted": 0
  }
]
```

说明：

- 每个孩子仅保留一条有效设置（`is_deleted = 0`），采用 upsert 语义。
- `min_value ≥ 0`、`max_value > min_value`、`operators` 为非空子集 `{add, subtract, multiply, divide}`。
- 算术无内容条目，不写入 `contents/`，题目由设置在会话开始时即时生成。

### 5.9 算术题目快照（session_questions.json）

算术题 `content_id` 为 `null`、`content_type` 为 `math`、`question_type` 为 `math_arithmetic`，`question_options` 为空，`correct_answer` 为整数结果的字符串形式，`content_snapshot` 保存出题参数（`min_value`、`max_value`、`operator`、`operand_a`、`operand_b`、`title`）以便历史追溯。

## 6. 读写约定

### 6.1 读取约定

- 所有查询默认过滤 `is_deleted = 0`
- 仅返回业务有效状态的数据
- 高频读取文件可做进程内缓存

### 6.2 写入约定

- 所有写入必须使用临时文件 + 原子替换
- 同一文件只允许串行写入
- 写入前后都要做 schema 校验
- 每次更新都要刷新 `updated_at`

### 6.3 删除约定

- 默认软删除
- 删除时仅更新 `is_deleted` 和 `deleted_at`
- 历史学习会话、题目快照、作答记录不做级联物理删除

## 7. 与逻辑数据库设计的差异说明

- 在逻辑设计中，`learning_content` 与 `learning_content_detail` 是两个实体，用于明确业务结构。
- 在 JSON 物理存储中，建议将两者合并到同一条记录中，减少文件关联复杂度。
- 在逻辑设计中可表达索引与唯一约束；在 JSON 存储中，这些约束需要由应用层和仓储层主动保证。

## 8. 结论

该映射方案保证了：

- 逻辑模型足够规范，便于后续数据库迁移
- 当前 JSON 存储实现足够简单，便于 MVP 快速落地
- 会话、题目、作答链路完整可追溯
- 软删除、快照保存、结构校验等关键要求都能落到物理层实现
