# 后端 API 响应格式规范

## 核心规则

### 分页列表

```python
class ListResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
```

响应示例：

```json
{ "items": [...], "total": 100, "page": 1, "page_size": 20 }
```

### 单个资源

直接返回资源 schema，无包装：

```python
return OrderResponse.model_validate(get_order(db, order_no))
```

### 操作结果

状态变更等操作返回操作结果 schema：

```python
class OrderStatusUpdateResponse(BaseModel):
    order_no: str
    previous_status: str
    new_status: str
    updated_at: datetime
```

---

## 禁止事项

- ❌ 在路由文件中内联定义响应 schema（必须放 `domain/<域>/schemas.py`）
- ❌ 使用自定义的 `{"code": ..., "data": ...}` 包装
- ❌ 在路由函数里做分页参数校验（用 `Query(ge=1, le=100)`）
