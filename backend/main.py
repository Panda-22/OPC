from fastapi import FastAPI, UploadFile, File
import io
import os
import tempfile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, HTMLResponse
from starlette.requests import Request
import uuid
import json
from typing import Dict, Any
import json as jsonlib
try:
    import httpx
except Exception:
    httpx = None
import logging
logging.basicConfig(level=logging.INFO)

# 加载.env配置
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

app = FastAPI(title="Investment Report Agent API")
print(f"[Init] DeepSeek URL: {DEEPSEEK_API_URL[:30] if DEEPSEEK_API_URL else 'None'}")

def _convert_survey_to_analysis(survey_data: dict) -> dict:
    """将调查问卷JSON转换为分析格式"""
    sections = survey_data.get('sections', {})
    risk = survey_data.get('risk_assessment', {})
    bg = sections.get('background', {})
    fin = sections.get('financial', {})
    exp = sections.get('experience', {})
    inv = sections.get('investment', {})
    dims = risk.get('dimensions', {})
    
    radar_points = []
    # 处理dimensions可能是{"financial": 25} 或 {"financial": {"score": 25}}
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

def _try_parse_json_report(b: bytes, filename: str):
    """尝试解析JSON报告，兼容调查问卷格式"""
    try:
        s = b.decode('utf-8')
    except:
        try:
            s = b.decode('gbk', errors='ignore')
        except:
            return None
    try:
        data = jsonlib.loads(s)
    except:
        return None
    if not isinstance(data, dict):
        return None
    
    # 检测调查问卷格式
    if 'sections' in data and 'risk_assessment' in data:
        try:
            return _convert_survey_to_analysis(data)
        except Exception as e:
            logging.warning(f"[Survey] Convert failed: {e}")
    
    # 标准报告格式
    if any(k in data for k in ('core_conclusion', 'radar_points', 'dimension_scores', 'suggestions')):
        return {
            'core_conclusion': data.get('core_conclusion') or data.get('coreConclusion') or '',
            'radar_points': data.get('radar_points') or [],
            'dimension_scores': data.get('dimension_scores') or [],
            'suggestions': data.get('suggestions') or [],
            'title': data.get('title', '投资分析报告')
        }
return None

@app.post("/upload")
async def upload_only(file: UploadFile = File(...)):
    """处理问卷数据，返回分析报告"""
    try:
        content = await file.read()
        data = jsonlib.loads(content)
        
        if 'sections' in data and 'risk_assessment' in data:
            analysis = _convert_survey_to_analysis(data)
        elif any(k in data for k in ('core_conclusion', 'dimension_scores')):
            analysis = data
        else:
            return {"error": "未知格式"}
        
        import uuid
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = {'analysis': analysis, 'chat': []}
        
        return {"session_id": session_id, "analysis": analysis}
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat_with_deepseek")
async def chat_with_deepseek(request: Request):
    """Chat using DeepSeek API"""
    try:
        data = await request.json()
    except:
        return {"reply": "请求格式错误"}
    
    session_id = data.get('session_id', '')
    message = data.get('message', '')
    
    if not session_id or session_id not in SESSIONS:
        return {"reply": "无效的session"}
    
    analysis = SESSIONS[session_id].get('analysis', {})
    
    # 直接调用DeepSeek
    if DEEPSEEK_API_URL and DEEPSEEK_API_KEY:
        try:
            context = f"分析数据: {analysis.get('core_conclusion', '')} 维度: {analysis.get('dimension_scores', [])} 建议: {analysis.get('suggestions', [])}"
            prompt = f"你是一个投资分析助手。根据以下分析数据回答用户问题。\n数据：{context}\n问题：{message}\n回答："
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    DEEPSEEK_API_URL,
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500
                    },
                    headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get('choices'):
                        return {"reply": result['choices'][0]['message']['content']}
        except Exception as e:
            print(f"DeepSeek error: {e}")
    
    # 回退规则
    reply = ''
    if '核心' in message:
        reply = str(analysis.get('core_conclusion') or '暂无')
    elif '维度' in message:
        dims = analysis.get('dimension_scores', [])
        reply = '维度得分：' + ', '.join([f"{d.get('dimension')}:{d.get('score')}" for d in dims])
    else:
        reply = '\n'.join(analysis.get('suggestions', [])) or '暂无'
    
    return {"reply": reply}

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in SESSIONS:
        return JSONResponse(status_code=404, content={"error": "Session not found"})
    return {"session": SESSIONS[session_id]}


@app.get("/")
async def root():
    """默认显示survey问卷"""
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, '..', 'survey.html')
    path = os.path.normpath(path)
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Survey not found</h1>")

@app.get("/debug", tags=["debug"])
async def debug():
    return {
        "status": "ok", 
        "sessions": len(SESSIONS),
        "session_ids": list(SESSIONS.keys())[:3]
    }

# Static files under /frontend for assets
app.mount("/frontend", StaticFiles(directory="./frontend"), name="frontend")

@app.get("/report.html")
async def report_page():
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'report.html')
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Not found", status_code=404)

@app.get("/survey.html")
async def survey_page():
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, '..', 'survey.html')
    path = os.path.normpath(path)
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Not found", status_code=404)
