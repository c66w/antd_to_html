# API 测试数据文档

本文档列出了所有测试用例使用的测试数据。

## 测试标识符

- **slug**: `test-all-apis-{timestamp}` (例如: `test-all-apis-1762507312`)
- **template_id**: 与 slug 相同（因为 slug 是主键）
- **instance_id**: 自动生成的短ID（例如: `bk38wqpxc`）
- **submission_id**: 自动生成的短ID（例如: `tcg1kuxzh1ou`）

---

## 测试 1: POST /form-templates - 创建模板

### 请求数据
```json
{
  "slug": "test-all-apis-{timestamp}",
  "title": "完整测试模板",
  "description": "用于测试所有接口的模板",
  "theme": "default",
  "definition": {
    "title": "完整测试表单",
    "subtitle": "这是一个测试表单",
    "items": [
      {
        "type": "input",
        "name": "username",
        "label": "用户名",
        "required": true
      },
      {
        "type": "password",
        "name": "password",
        "label": "密码",
        "required": true
      },
      {
        "type": "select",
        "name": "country",
        "label": "国家",
        "options": [
          {"label": "中国", "value": "cn"},
          {"label": "美国", "value": "us"}
        ]
      },
      {
        "type": "radio-group",
        "name": "plan",
        "label": "计划",
        "options": [
          {"label": "免费", "value": "free"},
          {"label": "专业", "value": "pro"}
        ],
        "defaultValue": "free"
      }
    ],
    "submit": {
      "callback": {
        "url": "https://example.com/callback",
        "method": "POST",
        "headers": {"X-Test": "true"}
      }
    }
  },
  "html_options": {
    "title": "测试表单",
    "contextBanner": {
      "label": "测试",
      "value": "true"
    }
  },
  "version": 1
}
```

### 预期响应
- 状态码: `200`
- 包含字段: `id`, `slug`, `title`, `description`, `theme`, `definition`, `html_options`, `version`, `created_at`, `updated_at`

---

## 测试 2: GET /form-templates/{slug} - 通过 slug 读取模板

### 请求参数
- **路径参数**: `slug` = `test-all-apis-{timestamp}`

### 预期响应
- 状态码: `200`
- `slug` 字段应与请求参数匹配

---

## 测试 3: GET /form-templates/{id} - 通过 id 读取模板

### 请求参数
- **路径参数**: `id` = `test-all-apis-{timestamp}` (与 slug 相同)

### 预期响应
- 状态码: `200`
- `id` 字段应与请求参数匹配

---

## 测试 4: GET /form-templates/{id}/preview - 预览模板

### 请求参数
- **路径参数**: `id` = `test-all-apis-{timestamp}`

### 预期响应
- 状态码: `200`
- Content-Type: `text/html; charset=utf-8`
- 响应体包含: `<!DOCTYPE html>`, `预览模式`

---

## 测试 5: POST /form-instances - 创建实例

### 请求数据
```json
{
  "template_slug": "test-all-apis-{timestamp}",
  "name": "测试实例",
  "runtime_config": {
    "submit": {
      "callback": {
        "url": "https://example.com/runtime-callback",
        "method": "POST",
        "params": {"test": "true"},
        "headers": {"X-Runtime": "test"}
      },
      "persistence": {
        "endpoint": "https://example.com/persistence",
        "headers": {"X-Persistence": "test"},
        "load_on_init": true,
        "update_text": "更新"
      }
    },
    "html": {
      "title": "运行时标题"
    }
  }
}
```

### 预期响应
- 状态码: `200`
- 包含字段: `id`, `template_id`, `name`, `runtime_config`, `created_at`, `updated_at`
- `template_id` 应与请求中的 `template_slug` 匹配

---

## 测试 6: GET /form-instances/{instance_id} - 读取实例

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）

### 预期响应
- 状态码: `200`
- 响应结构:
  ```json
  {
    "instance": {
      "id": "...",
      "template_id": "...",
      "name": "...",
      "runtime_config": {...},
      "created_at": "...",
      "updated_at": "..."
    },
    "template": {
      "id": "...",
      "slug": "...",
      "title": "...",
      ...
    }
  }
  ```

---

## 测试 7: GET /forms/{instance_id}/view - 渲染表单

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）

### 预期响应
- 状态码: `200`
- Content-Type: `text/html; charset=utf-8`
- 响应体包含: `<!DOCTYPE html>`, `form` 元素

---

## 测试 8: POST /forms/{instance_id}/submissions - 创建提交

### 请求数据
```json
{
  "payload": {
    "values": {
      "username": "testuser",
      "password": "testpass",
      "country": "cn",
      "plan": "pro"
    }
  },
  "status": "submitted",
  "callback_status": "pending",
  "callback_info": {
    "message": "测试提交"
  }
}
```

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）

### 预期响应
- 状态码: `200`
- 包含字段: `id`, `instance_id`, `payload`, `status`, `callback_status`, `callback_info`, `submitted_at`, `updated_at`
- `status` = `"submitted"`
- `instance_id` 应与请求参数匹配

---

## 测试 9: POST /forms/{instance_id}/submissions - 更新提交

### 请求数据
```json
{
  "submission_id": "tcg1kuxzh1ou",
  "payload": {
    "values": {
      "username": "updated_user",
      "password": "updated_pass",
      "country": "us",
      "plan": "free"
    }
  },
  "status": "completed",
  "callback_status": "success",
  "callback_info": {
    "message": "更新成功"
  }
}
```

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）
- **请求体中的 submission_id**: 测试8返回的提交ID

### 预期响应
- 状态码: `200`
- `id` 应与请求中的 `submission_id` 匹配
- `status` = `"completed"`
- `payload.values.username` = `"updated_user"`

---

## 测试 10: GET /forms/{instance_id}/submissions?submission_id=xxx - 获取指定提交

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）
- **查询参数**: `submission_id` = 测试8返回的提交ID（例如: `tcg1kuxzh1ou`）

### 预期响应
- 状态码: `200`
- `id` 应与查询参数中的 `submission_id` 匹配
- `payload.values.username` = `"updated_user"` (更新后的值)

---

## 测试 11: GET /forms/{instance_id}/submissions - 获取最新提交

### 请求参数
- **路径参数**: `instance_id` = 自动生成的ID（例如: `bk38wqpxc`）

### 预期响应
- 状态码: `200`
- 包含字段: `id`, `instance_id`, `payload`, `status`, ...
- `instance_id` 应与请求参数匹配
- 应返回该实例的最新提交记录

---

## 测试 12: DELETE /form-templates/{id} - 删除模板

### 请求参数
- **路径参数**: `id` = `test-all-apis-{timestamp}`

### 预期响应
- 状态码: `204 No Content`
- 响应体为空

---

## 测试 13: GET /form-templates/{id} (404) - 验证删除

### 请求参数
- **路径参数**: `id` = `test-all-apis-{timestamp}` (已删除的模板ID)

### 预期响应
- 状态码: `404 Not Found`
- 错误信息: `"Template not found."`

---

## 数据清理

在测试12之前，会执行以下SQL清理操作：

```sql
DELETE FROM form_submissions WHERE instance_id = '{instance_id}';
DELETE FROM form_instances WHERE slug = '{instance_id}';
```

---

## 测试数据流程

1. **创建模板** → 获得 `template_id` (等于 `slug`)
2. **读取模板** (通过 slug 和 id)
3. **预览模板**
4. **创建实例** → 获得 `instance_id`
5. **读取实例**
6. **渲染表单**
7. **创建提交** → 获得 `submission_id`
8. **更新提交** (使用 `submission_id`)
9. **获取指定提交** (使用 `submission_id`)
10. **获取最新提交**
11. **清理数据** (删除提交和实例)
12. **删除模板**
13. **验证删除** (确认返回404)

