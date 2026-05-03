from fastapi import FastAPI, UploadFile, File
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.requests import Request
import uuid
import json
import logging

logging.basicConfig(level=logging.INFO)

# Load .env config
def _load_env():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k] = v

_load_env()

DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
print(f"[Init] DeepSeek URL: {DEEPSEEK_API_URL[:30] if DEEPSEEK_API_URL else 'None'}")

app = FastAPI(title="Investment Report Agent API")

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sessions
SESSIONS = {}

# Survey to analysis converter
def _convert_survey_to_analysis(survey_data: dict) -> dict:
    sections = survey_data.get('sections', {})
    risk = survey_data.get('risk_assessment', {})
    bg = sections.get('background', {})
    fin = sections.get('financial', {})
    exp = sections.get('experience', {})
    inv = sections.get('investment', {})
    dims = risk.get('dimensions', {})
    
    radar_points = []
    f = dims.get('financial')
    if f:
        val = f.get('score', f) if isinstance(f, dict) else f
        radar_points.append({'label': '资金匹配度', 'value': float(val)})
    e = dims.get('experience')
    if e:
        val = e.get('score', e) if isinstance(e, dict) else e
        radar_points.append({'label': '经验匹配度', 'value': float(val)})
    t = dims.get('timeMindset')
    if t:
        val = t.get('score', t) if isinstance(t, dict) else t
        radar_points.append({'label': '时间/心态匹配度', 'value': float(val)})
    r = dims.get('region')
    if r:
        val = r.get('score', r) if isinstance(r, dict) else r
        radar_points.append({'label': '区域匹配度', 'value': float(val)})
    
    dimension_scores = []
    for pt in radar_points:
        dimension_scores.append({'dimension': pt['label'], 'score': int(pt['value'])})
    
    score = risk.get('score', 0)
    level = risk.get('level', '未知')
    core_conclusion = f"风险评估得分{score}分，适配等级{level}。"
    if fin.get('total_budget'):
        core_conclusion += f"初始预算{int(fin.get('total_budget'))}万元。 "
    if inv.get('track_intent'):
        core_conclusion += f"意向品类：{inv.get('track_intent')}。"
    
    suggestions = risk.get('recommendations', []) or []
    if not suggestions:
        suggestions = ["建议持续关注市场动态，合理配置资源。"]
    
    return {
        'title': f"投资适配性分析报告 - {survey_data.get('submitted_at', 'N/A')[:10]}",
        'core_conclusion': core_conclusion,
        'radar_points': radar_points,
        'dimension_scores': dimension_scores,
        'suggestions': suggestions
    }

# Upload endpoint
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        data = json.loads(content)
    except:
        return {"error": "Invalid JSON"}
    
    if 'sections' in data and 'risk_assessment' in data:
        analysis = _convert_survey_to_analysis(data)
    elif any(k in data for k in ('core_conclusion', 'dimension_scores')):
        analysis = data
    else:
        return {"error": "Unknown format"}
    
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {'analysis': analysis, 'chat': []}
    return {"session_id": session_id, "analysis": analysis}

# Chat endpoint
@app.post("/chat_with_deepseek")
async def chat(request: Request):
    try:
        data = await request.json()
    except:
        return {"reply": "请求格式错误"}
    
    session_id = data.get('session_id', '')
    message = data.get('message', '')
    
    if not session_id or session_id not in SESSIONS:
        return {"reply": "无效的session"}
    
    analysis = SESSIONS[session_id].get('analysis', {})
    
    # Try DeepSeek
    if DEEPSEEK_API_URL and DEEPSEEK_API_KEY:
        try:
            import httpx
            context = f"分析数据: {analysis.get('core_conclusion', '')} 维度: {analysis.get('dimension_scores', [])} 建议: {analysis.get('suggestions', [])}"
            prompt = f"你是一个投资分析助手。根据以下分析数据回答用户问题。\n数据：{context}\n问题：{message}\n回答："
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    DEEPSEEK_API_URL,
                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                    headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('choices'):
                        return {"reply": result['choices'][0]['message']['content']}
        except Exception as e:
            print(f"DeepSeek error: {e}")
    
    # Fallback to rules
    reply = ''
    if '核心' in message:
        reply = str(analysis.get('core_conclusion') or '暂无')
    elif '维度' in message:
        dims = analysis.get('dimension_scores', [])
        reply = '维度得分：' + ', '.join([f"{d.get('dimension')}:{d.get('score')}" for d in dims])
    else:
        reply = '\n'.join(analysis.get('suggestions', [])) or '暂无'
    
    return {"reply": reply}

# Root - serve survey.html
@app.get("/")
async def root():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'survey.html')
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Survey not found")

# Serve static files
app.mount("/frontend", StaticFiles(directory="./frontend"), name="frontend")

@app.get("/report.html")
async def report_page():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'report.html')
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Report page not found")
