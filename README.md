# OPC 餐饮投资报告应用

基于问卷数据生成三份餐饮创业分析报告：

- 综合适配度报告
- 选址分析报告
- 加盟品牌双向适配报告

所有报告均标注：仅基于公开数据分析，不构成最终投资建议。

## 启动

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

访问：

```text
http://127.0.0.1:8000/
```

## 接口

### 提交问卷

```text
POST /upload
Content-Type: multipart/form-data
field: file
```

上传内容为问卷 JSON。接口返回本次会话的三份报告链接：

```json
{
  "session_id": "uuid",
  "reports": {
    "compatibility": "/reports/{session_id}/compatibility",
    "location": "/reports/{session_id}/location",
    "brand": "/reports/{session_id}/brand"
  }
}
```

### 查看报告

```text
GET /reports/{session_id}/compatibility
GET /reports/{session_id}/location
GET /reports/{session_id}/brand
```

## 项目结构

```text
survey.html
backend/
  main.py
  requirements.txt
```
