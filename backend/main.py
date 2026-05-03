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
from datetime import datetime

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
print(f"[Init] DeepSeek URL: {DEEPSEEK_API_URL[:30] if DEEPSEEK_API_URL else 'None'}")

def _generate_pdf_report(analysis: dict, session_id: str) -> str:
    
    pdf = FPDF()
    pdf.add_page()
    
    # 标题
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(44, 62, 78)
    pdf.cell(0, 15, analysis.get('title', '投资适配性分析报告'), ln=True, align='C')
    pdf.ln(5)
    
    # 分割线
    pdf.set_draw_color(189, 195, 199)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    # 核心结论
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(44, 62, 78)
    pdf.cell(0, 10, '核心结论', ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(52, 73, 94)
    core = analysis.get('core_conclusion', '暂无')
    pdf.multi_cell(0, 6, core)
    pdf.ln(5)
    
    # 维度得分
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(44, 62, 78)
    pdf.cell(0, 10, '维度得分对比', ln=True)
    
    dims = analysis.get('dimension_scores', [])
    if dims:
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(52, 73, 94)
        max_score = 25
        
        # 表头
        pdf.set_fill_color(236, 240, 241)
        pdf.cell(80, 8, '维度', 1, 0, 'C', True)
        pdf.cell(40, 8, '得分', 1, 0, 'C', True)
        pdf.cell(50, 8, '评估', 1, 1, 'C', True)
        
        # 数据行
        for dim in dims:
            name = dim.get('dimension', '?')
            score = dim.get('score', 0)
            
            # 评估等级
            if score >= 20:
                level = '优秀'
            elif score >= 15:
                level = '良好'
            elif score >= 10:
                level = '一般'
            else:
                level = '待提升'
            
            pdf.cell(80, 8, name, 1)
            pdf.cell(40, 8, f'{score}/{max_score}', 1, 0, 'C')
            pdf.cell(50, 8, level, 1, 1, 'C')
    
    pdf.ln(5)
    
    # 建议
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(44, 62, 78)
    pdf.cell(0, 10, '建议', ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(52, 73, 94)
    
    suggestions = analysis.get('suggestions', [])
    if suggestions:
        for i, s in enumerate(suggestions, 1):
            pdf.multi_cell(0, 6, f'{i}. {s}')
    else:
        pdf.cell(0, 6, '暂无建议', ln=True)
    
    pdf.ln(10)
    
    # 底部时间
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(149, 165, 166)
    pdf.cell(0, 6, f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Session: {session_id[:8]}', ln=True, align='R')
    
    # 保存PDF
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    pdf_path = os.path.join(data_dir, f'report_{ts}.pdf')
    pdf.output(pdf_path)
    
    return pdf_path
# 加载.env配置
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k] = v
                        
    # DeepSeek配置
    DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    print(f"[Init] DeepSeek URL: {DEEPSEEK_API_URL[:30] if DEEPSEEK_API_URL else 'None'}")

from agents.investment_report_agent import InvestmentReportAgent

app = FastAPI(title="Investment Report Agent API")

# Allow CORS for frontend
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory sessions cache
SESSIONS: Dict[str, Dict[str, Any]] = {}

agent = InvestmentReportAgent()


def _read_text_from_bytes(b: bytes, filename: str) -> str:
    # 优先尝试直接从 PDF 提取文本（如果上传的是 PDF），然后再退回文本解码
    fname = (filename or '').lower()
    # 直接对常见图片格式进行 OCR 提取（若上传的是图片）
    image_exts = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp')
    if fname.endswith(image_exts):
        try:
            ocr_text = _ocr_image_bytes(b, filename)
            if ocr_text:
                return ocr_text.strip()
        except Exception:
            pass
    if fname.endswith('.pdf'):
        # 1) 尝试直接文本提取
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=b, filetype="pdf")
            parts = []
            for page in doc:
                text = page.get_text("text")
                if text:
                    parts.append(text)
            pdf_text = "\n".join(parts).strip()
            doc.close()
            if pdf_text and len(pdf_text) > 100:
                return pdf_text
        except Exception:
            pdf_text = ''

        # 2) 直接 OCR 提取（对图片型 PDF/文本提取失败场景）
        try:
            ocr_text = _ocr_pdf_bytes(b, filename)
            if ocr_text:
                return ocr_text.strip()
        except Exception:
            pass
        # 3) 最后兜底：如果仍为空，继续回退到简单解码

    # 回退：尝试以 UTF-8 解码，失败时再用 GBK 忽略错误
    try:
        text = b.decode('utf-8')
        return text
    except Exception:
        try:
            return b.decode('gbk', errors='ignore')
        except Exception:
            return ''


def _ocr_pdf_bytes(b: bytes, filename: str) -> str:
    # 使用 PyMuPDF 渲染每页为图片后，使用 Tesseract OCR 识别
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except Exception:
        return ''
    text_parts = []
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        for page in doc:
            try:
                pix = page.get_pixmap(dpi=200)
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    pix.writePNG(tmp.name)
                    tmp.flush()
                    image = Image.open(tmp.name)
                    t = pytesseract.image_to_string(image, lang="chi_sim+eng")
                    if t:
                        text_parts.append(t)
                    image.close()
                    os.unlink(tmp.name)
            except Exception:
                continue
        doc.close()
    except Exception:
        return ''
    return '\n'.join(text_parts)

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

@app.post("/upload_report")
async def upload_report(file: UploadFile = File(...)):
    content = await file.read()
    
    # 解析JSON报告（支持调查问卷格式或标准格式）
    try:
        survey_json = jsonlib.loads(content)
        if 'sections' in survey_json and 'risk_assessment' in survey_json:
            analysis = _convert_survey_to_analysis(survey_json)
        elif any(k in survey_json for k in ('core_conclusion', 'radar_points', 'dimension_scores', 'suggestions')):
            analysis = survey_json
        else:
            raise ValueError("Unknown format")
    except:
        text = _read_text_from_bytes(content, file.filename)
        analysis = agent.analyze(text)
    
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        'analysis': analysis,
        'chat': []
    }
    
    # 返回完整信息供前端使用
    return {
        "session_id": session_id,
        "analysis": analysis,
        "title": analysis.get('title', '投资分析报告'),
        "core_conclusion": analysis.get('core_conclusion', ''),
        "radar_points": analysis.get('radar_points', []),
        "dimension_scores": analysis.get('dimension_scores', []),
        "suggestions": analysis.get('suggestions', [])
    }


@app.post("/chat")
async def chat(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid JSON: {e}"})
    
    session_id = data.get('session_id', '')
    message = data.get('message', '')
    
    logging.info(f"[Chat] Request - session: {session_id}, msg: {message[:30]}")
    logging.info(f"[Chat] Available sessions: {list(SESSIONS.keys())}")
    
    if session_id not in SESSIONS:
        return JSONResponse(status_code=400, content={
            "error": f"Session {session_id} not found", 
            "available": list(SESSIONS.keys())
        })
    
    analysis = SESSIONS[session_id].get('analysis', {})
    logging.info(f"[Chat] Analysis: {analysis}")
    
    # 简单的规则回复
    reply = ''
    if '核心' in message:
        reply = analysis.get('core_conclusion') or '无结论'
    elif '维度' in message or '雷达' in message:
        dims = analysis.get('dimension_scores', [])
        reply = '\n'.join([f"{d.get('dimension','?')}: {d.get('score','?')}" for d in dims]) or '无维度数据'
    elif '建议' in message:
        reply = '\n'.join(analysis.get('suggestions', [])) or '无建议'
    else:
        reply = '请提问关于核心结论、维度得分或建议'
    
def _try_parse_json_report(b: bytes, filename: str) -> dict:
    """兼容survey问卷和标准报告格式"""
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
    
    # Survey格式
    if 'sections' in data and 'risk_assessment' in data:
        return _convert_survey_to_analysis(data)
    
    # 标准格式
    if any(k in data for k in ('core_conclusion', 'radar_points', 'dimension_scores', 'suggestions')):
        return {
            'core_conclusion': data.get('core_conclusion', ''),
            'radar_points': data.get('radar_points', []),
            'dimension_scores': data.get('dimension_scores', []),
            'suggestions': data.get('suggestions', []),
            'title': data.get('title', '投资分析报告')
        }
    return None

@app.post("/upload")
async def upload_only(file: UploadFile = File(...)):
    """简化版上传"""
    try:
        content = await file.read()
        filename = file.filename or "unknown.json"
        
        # 解析JSON
        try:
            data = jsonlib.loads(content)
        except:
            return {"error": "不是有效的JSON"}
        
        # 保存到data文件夹
        import os
        from datetime import datetime
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        save_path = os.path.join(data_dir, f'survey_{ts}.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            jsonlib.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Saved] {save_path}")
        
        # 检测survey格式
        if 'sections' in data and 'risk_assessment' in data:
            analysis = _convert_survey_to_analysis(data)
        elif any(k in data for k in ('core_conclusion', 'dimension_scores')):
            analysis = data
        else:
            return {"error": "未知格式"}
        
        # 创建session
        import uuid
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = {'analysis': analysis, 'chat': []}
        
        # 生成PDF报告
        try:
            pdf_path = _generate_pdf_report(analysis, session_id)
            print(f"[PDF] {pdf_path}")
        except Exception as e:
            print(f"[PDF Error] {e}")
        
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
