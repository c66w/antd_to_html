# antd-to-html

一个将 Ant Design 表单 JSON 转换为可直接访问的 HTML 页面，并支持模板管理、实例配置与数据提交链路的 Python 服务。

## 快速上手

1. 创建虚拟环境并安装依赖（Python ≥ 3.11）：
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   pip install --upgrade pip
   pip install -e .
   ```

2. 复制环境变量样例并按需修改：
   ```bash
   cp env.example .env
   ```

3. 初始化数据库（PostgreSQL ≥ 13）：
   ```bash
   psql -h 192.168.110.23 -U postgres -d form -f schema.sql
   ```

4. 可选：验证数据库连通性。
   ```bash
   python scripts/test_db.py
   ```

5. 启动 FastAPI 服务：
   ```bash
   uvicorn antd_to_html.app:create_app --factory --host 0.0.0.0 --port 8400
   ```

## 典型流程

1. **创建模板** `POST /form-templates`
   ```json
   {
     "slug": "registration-form",
     "title": "注册账号",
     "description": "基础注册信息",
     "definition": {
       "title": "注册账号",
       "items": [
       { "type": "input", "name": "username", "label": "用户名", "required": true },
        { "type": "password", "name": "password", "label": "密码", "required": true }
      ]
    },
    "html_options": { "title": "账号注册" }
  }
   ```

   如需自定义模板 ID，可额外提供 `id` 字段（默认自动生成 9 位小写字母+数字）。
   未提供 `slug` 时会自动复用模板 `id`，可选地传入自定义 slug。

   可用 `DELETE /form-templates/{id_or_slug}` 删除模板。

   想快速预览模板外观，可访问 `GET /form-templates/{id_or_slug}/preview`，浏览器会返回只读页面，按钮全部禁用以避免误提交。

2. **创建实例** `POST /form-instances`
   ```json
   {
    "template_slug": "registration-form",
    "name": "instance-a",
    "runtime_config": {
      "submit": {
        "callback": {
          "url": "https://example.com/form/callback",
          "method": "POST",
          "params": {
            "task_id": "task_603a1e0ef40b40dd"
          }
        },
        "persistence": {
          "endpoint": "https://form.example.com/api/submissions",
          "headers": { "X-Trace": "demo" },
          "load_on_init": true,
          "update_text": "更新",
          "submission_id": "... 可选，指定已有提交记录 ..."
        }
      },
      "html": {
        "title": "业务方自定义标题"
      }
    }
  }
  ```

   同样可以通过可选字段 `id` 指定实例 ID（默认自动生成 9 位小写字母+数字）。

   > 说明：`submit.callback` 与 `submit.persistence` 是提交配置的唯一入口，参数均使用 snake_case（例如 `callback.url`、`callback.params`）。

   返回的 `id` 即实例 ID。

3. **访问时实时渲染** `GET /forms/{instance_id}/view`

   页面在浏览器打开后会：
   - 自动向 `GET /forms/{instance_id}/submissions` 拉取最近一次提交（可通过 `submission_id` 查询指定记录），并把 `payload.values` 回填到表单。
   - 默认显示“提交/重置”按钮；如果存在历史记录，提交按钮会切换为“更新”。

4. **确认提交/回调**
   - 点击“提交”后，脚本先 `POST /forms/{instance_id}/submissions` 写入或更新 `form_submissions`（字段包含 `payload`、`status`、`callback_status` 等）。
   - 若定义了 `submit.callback.url`，保存成功后再请求回调；回调成功会把记录更新成 `status=completed`、`callback_status=success`，失败则写入 `status=failed` 并保留错误信息。默认提示文案均为中文（“提交中…/提交成功/提交失败”）。
   - 也可以手动调用 `GET /forms/{instance_id}/submissions?submission_id=<submission_id>` 查询指定提交记录。

## 模块概览

- `src/antd_to_html/config.py`：环境变量 & 配置。
- `src/antd_to_html/db.py`：psycopg 连接池与查询工具。
- `src/antd_to_html/schema_validator.py`：AntD JSON 校验。
- `src/antd_to_html/render.py` / `submit_script.py`：HTML 渲染与提交脚本。
- `src/antd_to_html/models.py`：Pydantic 请求/响应模型。
- `src/antd_to_html/repositories.py`：模板/实例/提交的数据库读写。
- `src/antd_to_html/api/`：FastAPI 路由（模板、实例、运行时）。
- `src/antd_to_html/app.py`：应用工厂。

数据库结构详见 `schema.sql`，包含：
- `form_templates`
- `form_instances`
- `form_submissions`

## 直接生成 HTML

无需启动服务时，可以直接调用：
```python
from antd_to_html.render import convert_antd_form_to_html

html = convert_antd_form_to_html(definition, options={"html": {"title": "Demo"}})
```

## 测试

```bash
pytest
```

要快速验证服务端 CRUD 链路，可以先启动 API 服务，再执行：

```bash
python scripts/run_crud_tests.py
```

该脚本会自动创建/读取/更新/删除模板与实例数据，并在最后清理测试产生的记录。

## 环境变量样例

```
PG_HOST=192.168.110.23
PG_PORT=5433
PG_DATABASE=form
PG_USER=postgres
PG_PASSWORD=example
```
