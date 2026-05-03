# 投资分析智能体 (投必盈)

餐饮投资智能分析系统 - 结合调查问卷与AI智能体

## 功能

1. **调查问卷** - 填写投资意向调查问卷
2. **自动分析** - 问卷数据自动转换为投资分析报告
3. **AI问答** - 基于DeepSeek API的智能问答

## 环境要求

- Python 3.8+
- DeepSeek API Key

## 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# DeepSeek API配置
export DEEPSEEK_API_URL="https://api.deepseek.com/v1/chat/completions"
export DEEPSEEK_API_KEY="your-api-key"
```

### 3. 启动服务

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问

- 调查问卷: http://localhost:8000/
- 投资分析主页: http://localhost:8000/index.html

## 项目结构

```
├── survey.html          # 调查问卷页面
├── index.html         # 投资分析主页
├── backend/
│   ├── main.py       # FastAPI服务器
│   └── requirements.txt
└── agents/
    └── investment_report_agent.py
```

## 使用流程

1. 打开 http://localhost:8000/ 填写调查问卷
2. 点击"提交问卷"
3. 系统自动：
   - 保存JSON到data文件夹
   - 生成分析报告
   - 开启智能问答
4. 在问答框提问（如"哪些城市适合开火锅店？"）

## 依赖

- fastapi
- uvicorn
- httpx
- python-multipart
- PyMuPDF (PDF解析，可选)
- pytesseract (OCR，可选)

## License

MIT
