# 投资分析智能体 (OPC)

餐饮投资智能分析系统 - 结合调查问卷与AI智能体

## 环境要求

- Python 3.8+
- DeepSeek API Key

## 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置文件 (重要!)

在项目根目录 `OPC/` 下创建 `.env` 文件:

```bash
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=你的API密钥
```

### 3. 启动服务

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问

- 调查问卷: http://localhost:8000/

## 输出文件

每次提交问卷后会自动生成：
- `data/survey_YYYY-MM-DD.json` - 原始问卷数据
- `data/report_YYYY-MM-DD.pdf` - 分析报告PDF

## 项目结构

```
├── .env                    # API配置（需要手动创建）
├── survey.html            # 调查问卷页面
├── README.md
├── backend/
│   ├── main.py            # FastAPI服务器
│   └── requirements.txt
├── agents/
│   └── investment_report_agent.py
└── data/                  # 生成的文件目录
```

## 依赖

- fastapi
- uvicorn
- httpx
- python-multipart
- fpdf