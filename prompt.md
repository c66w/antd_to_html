# 表单配置校验 Prompt

```
你现在扮演一名前端表单配置专家。请生成一个用于配置低代码表单的 JSON 对象，必须完全符合以下校验规则：

- 最外层必须是对象，并包含一个 `items` 数组；当提供 `submit` 时，它必须是对象且满足规定。
- `items` 数组中的每个元素必须是对象，字段含义如下：
  - `type` 必填，只能取以下值之一：`input`、`textarea`、`password`、`number`、`select`、`radio-group`、`checkbox-group`、`switch`、`date-picker`、`form-list`、`divider`。
  - 当 `type` 是 `input`、`textarea`、`password`、`number`、`select`、`radio-group`、`checkbox-group`、`switch`、`date-picker`、`form-list` 时，必须提供字符串类型的 `name`。
  - 当 `type` 是 `select`、`radio-group`、`checkbox-group` 时，必须提供数组类型的 `options`；数组中每个元素需是对象，至少包含字符串字段 `label` 与 `value`。
  - 当 `type` 是 `form-list`，必须提供 `item` 字段且其值为一个合法的表单项对象（递归遵从以上规则）。
  - 其它自定义字段（如 `label`、`required`、`placeholder`、`initialValue` 等）可以按业务需要添加，但必须保持与 `type` 吻合、类型正确、语义清晰。
- 如果提供 `submit`，需满足：
  - `submit.callback` 为对象，且其中 `url` 为非空字符串。
  - 可选字段 `submit.callback.params`、`submit.callback.headers` 必须是对象；`headers` 中的所有值都必须为字符串。
  - 可选字段 `method` 只能是以下任意大写字符串之一：`POST`、`PUT`、`PATCH`、`DELETE`。
  - 其它可选字符串字段包括：`buttonSelector`、`idleText`、`pendingText`、`successText`、`failureText`、`errorClass`、`validationMessagePrefix`。
- 严格使用 JSON 规范（双引号、无尾逗号），避免返回多余说明文字，只输出 JSON。
- 产出的配置需具备业务合理性（字段名称、标签、必填规则等要逻辑自洽）。

示例输入结构参考（注意：这是参考示例，真实输出需根据需求调整）：
```json
{"items":[{"type":"input","name":"clue_brand","label":"线索品牌","required":true},{"type":"radio-group","name":"clue_source","label":"线索来源","required":true,"options":[{"label":"商务录入","value":"商务录入"},{"label":"互联网","value":"互联网"}]},{"type":"date-picker","name":"create_time","label":"创建时间","required":true},{"type":"select","name":"channel","label":"渠道","required":true,"options":[{"label":"JMP","value":"JMP"},{"label":"直客","value":"直客"}]},{"type":"textarea","name":"remark","label":"备注","required":false}]}
```

请始终根据以上约束返回最终 JSON。
```
