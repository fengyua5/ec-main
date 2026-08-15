# 后端 Pydantic schema 规范

## 位置

- 请求/响应 schema 统一放 `domain/<域>/schemas.py`,禁止在路由文件内联定义。

```python
class OrderResponse(BaseModel):
    order_no: str
    buyer_id: int
    amount: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

  参考:`backend/app/domain/orders/schemas.py`

## 禁止

- ❌ 在 `app/api/...` 路由文件里写 `class XxxIn(BaseModel)`(反例:历史 `backend/app/api/web/ai.py`)。
