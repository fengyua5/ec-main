# 后端分层规范

## 铁律

- 路由函数体只做:参数解析 + 调 domain 函数 + `model_validate` 包装返回。
- 业务规则(状态机、权限、校验)必须写在 `domain/<域>/`。

```python
@router.get("/{order_no}", response_model=OrderResponse)
def order_detail(order_no: str, db: Session = Depends(get_db)):
    return OrderResponse.model_validate(get_order(db, order_no))
```

  参考:`backend/app/api/admin/orders.py`(薄路由)、`backend/app/domain/orders/__init__.py`(状态机)

## 禁止

- ❌ 在路由文件里写业务逻辑(状态流转、权限判断、校验)。
- ❌ 在路由里直接读写 DB(应走 domain 或 repo)。
