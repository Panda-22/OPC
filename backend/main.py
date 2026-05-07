from fastapi import FastAPI, UploadFile, File
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uuid
import json
import logging
from html import escape

logging.basicConfig(level=logging.INFO)

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

DISCLAIMER = "仅基于公开数据分析，不构成最终投资建议。"

CITY_PUBLIC_DATA = {
    "南京": {
        "population": "957.70 万",
        "urbanization": "87.3%",
        "retail_sales": "8552.75 亿",
        "income": "75180 元",
        "sources": [
            {
                "label": "南京市统计局 2024 统计公报",
                "url": "https://tjj.nanjing.gov.cn/njstjj/202504/t20250401_5108470.html",
            },
            {
                "label": "南京市政府主要经济指标",
                "url": "https://www.nanjing.gov.cn/sjfb/sjfb/202502/t20250207_5069723.html",
            },
        ],
    }
}

BRAND_PUBLIC_DATA = {
    "茶百道": {
        "category": "现制茶饮",
        "headquarter": "四川成都",
        "positioning": "新一线主流茶饮品牌",
        "store_count": "8395 家",
        "revenue": "2024 年营收约 49.2 亿元",
        "members": "注册会员约 1.39 亿",
        "supply_chain": "92% 门店下单补货次日达，水果统配率约 71.7%",
        "new_products": "2024 年国内推出 60 款新品，完成 42 款经典产品升级",
        "investment_min": 25,
        "investment_max": 30,
        "franchise_fee": 0,
        "deposit": 1.0,
        "decoration_fee": 8.0,
        "equipment_fee": 13.0,
        "design_fee": 1.5,
        "rent_estimate": 6.0,
        "first_material_fee": 4.0,
        "reserve_fund": 16.5,
        "gross_margin": 0.65,
        "avg_ticket": 15,
        "monthly_fixed_cost": 4.35,
        "fit_store_type": "标准店/社区店/写字楼边缘店",
        "support": ["培训体系", "供应链配送", "新品研发", "数字化督导", "营销活动"],
        "risk_notes": ["南京区域加盟名额需确认", "合同区域保护需核验", "真实门店流水需访谈加盟商"],
        "ratings": {
            "brand_power": 0.86,
            "support": 0.78,
            "product": 0.80,
            "risk_control": 0.73,
            "concept": 0.82,
        },
        "source_label": "茶百道官网与 2024 年业绩公开报道",
        "source_url": "https://www.chabaidao.com/home/index/",
        "updated_at": "2026-05-07",
    },
    "古茗": {
        "category": "现制茶饮",
        "headquarter": "浙江台州",
        "positioning": "下沉与区域高密度茶饮品牌",
        "store_count": "公开资料显示门店规模处于头部梯队，具体城市名额需核验",
        "revenue": "需以最新招股书/公告核验",
        "members": "需公开资料补充",
        "supply_chain": "区域密集开店和供应链能力是主要优势",
        "new_products": "需公开资料补充",
        "investment_min": 30,
        "investment_max": 38,
        "franchise_fee": 3.0,
        "deposit": 1.0,
        "decoration_fee": 10.0,
        "equipment_fee": 12.0,
        "design_fee": 1.5,
        "rent_estimate": 6.0,
        "first_material_fee": 4.5,
        "reserve_fund": 16.0,
        "gross_margin": 0.62,
        "avg_ticket": 14,
        "monthly_fixed_cost": 4.1,
        "fit_store_type": "社区店/街边店",
        "support": ["供应链配送", "培训体系", "运营督导"],
        "risk_notes": ["南京区域政策需确认", "投资额可能高于 30 万预算"],
        "ratings": {
            "brand_power": 0.78,
            "support": 0.70,
            "product": 0.74,
            "risk_control": 0.67,
            "concept": 0.70,
        },
        "source_label": "品牌官网/公告/招商资料，需接入后核验",
        "source_url": "#",
        "updated_at": "2026-05-07",
    },
    "蜜雪冰城": {
        "category": "现制饮品",
        "headquarter": "河南郑州",
        "positioning": "高性价比大众饮品品牌",
        "store_count": "公开资料显示门店规模极高，具体城市密度需地图核验",
        "revenue": "需以最新公告核验",
        "members": "需公开资料补充",
        "supply_chain": "强供应链和高标准化是主要优势",
        "new_products": "以高频基础款为主",
        "investment_min": 20,
        "investment_max": 28,
        "franchise_fee": 1.1,
        "deposit": 2.0,
        "decoration_fee": 6.0,
        "equipment_fee": 7.0,
        "design_fee": 1.0,
        "rent_estimate": 6.0,
        "first_material_fee": 5.0,
        "reserve_fund": 14.5,
        "gross_margin": 0.58,
        "avg_ticket": 8,
        "monthly_fixed_cost": 3.8,
        "fit_store_type": "社区店/学校周边/街边店",
        "support": ["培训体系", "标准化产品", "供应链配送"],
        "risk_notes": ["低客单需要高杯量支撑", "同品牌密度和驻店要求需核验"],
        "ratings": {
            "brand_power": 0.90,
            "support": 0.80,
            "product": 0.70,
            "risk_control": 0.76,
            "concept": 0.62,
        },
        "source_label": "蜜雪冰城官方加盟页",
        "source_url": "https://www.mxbc.com/franchised.html",
        "updated_at": "2026-05-07",
    },
    "沪上阿姨": {
        "category": "现制茶饮",
        "headquarter": "上海",
        "positioning": "中端现制茶饮品牌",
        "store_count": "需以最新官网/公告核验",
        "revenue": "需以最新公告核验",
        "members": "需公开资料补充",
        "supply_chain": "具备连锁茶饮供应链基础",
        "new_products": "需公开资料补充",
        "investment_min": 28,
        "investment_max": 36,
        "franchise_fee": 3.0,
        "deposit": 1.0,
        "decoration_fee": 9.0,
        "equipment_fee": 11.0,
        "design_fee": 1.5,
        "rent_estimate": 6.0,
        "first_material_fee": 4.0,
        "reserve_fund": 15.0,
        "gross_margin": 0.62,
        "avg_ticket": 13,
        "monthly_fixed_cost": 4.2,
        "fit_store_type": "社区店/写字楼边缘店",
        "support": ["培训体系", "运营督导", "营销支持"],
        "risk_notes": ["区域竞争和开店政策需核验"],
        "ratings": {
            "brand_power": 0.72,
            "support": 0.68,
            "product": 0.70,
            "risk_control": 0.65,
            "concept": 0.68,
        },
        "source_label": "品牌官网/招商资料，需接入后核验",
        "source_url": "#",
        "updated_at": "2026-05-07",
    },
}


def _html(text) -> str:
    return escape(str(text or ""), quote=True)


def _score_from_dims(dims: dict, key: str) -> int:
    value = dims.get(key, 0)
    if isinstance(value, dict):
        value = value.get("score", 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _survey_context(survey_data: dict) -> dict:
    sections = survey_data.get("sections", {})
    bg = sections.get("background", {})
    fin = sections.get("financial", {})
    exp = sections.get("experience", {})
    inv = sections.get("investment", {})
    loc = inv.get("target_location", {}) or {}
    risk = survey_data.get("risk_assessment", {})
    dims = risk.get("dimensions", {})
    brand = inv.get("brand_intent") or inv.get("brand") or inv.get("target_brand") or ""
    city = loc.get("city") or "南京"
    city_short = city.replace("市", "")
    city_data = CITY_PUBLIC_DATA.get(city_short, CITY_PUBLIC_DATA["南京"])
    return {
        "sections": sections,
        "background": bg,
        "financial": fin,
        "experience": exp,
        "investment": inv,
        "location": loc,
        "brand": brand or "待填写品牌",
        "city": city or "南京",
        "city_short": city_short,
        "city_data": city_data,
        "track": inv.get("track_intent") or "现制饮品（奶茶/咖啡）",
        "budget": fin.get("total_budget") or 0,
        "score": int(risk.get("score") or dims.get("total") or 0),
        "level": risk.get("level") or "待评估",
        "dim_financial": _score_from_dims(dims, "financial"),
        "dim_experience": _score_from_dims(dims, "experience"),
        "dim_time": _score_from_dims(dims, "timeMindset"),
        "dim_region": _score_from_dims(dims, "region"),
        "reasons": risk.get("reasons", []),
        "recommendations": risk.get("recommendations", []),
    }


def _report_nav(session_id: str | None, report_type: str | None) -> str:
    if not session_id or not report_type:
        return ""
    report_order = [
        ("compatibility", "综合适配度报告"),
        ("location", "选址分析报告"),
        ("brand", "品牌双向适配报告"),
    ]
    index_by_type = {item[0]: idx for idx, item in enumerate(report_order)}
    if report_type not in index_by_type:
        return ""
    idx = index_by_type[report_type]
    prev_type, prev_label = report_order[(idx - 1) % len(report_order)]
    next_type, next_label = report_order[(idx + 1) % len(report_order)]
    return f"""
    <nav class="report-nav" aria-label="报告切换">
      <a class="report-nav-link" href="/reports/{_html(session_id)}/{_html(prev_type)}">← {_html(prev_label)}</a>
      <a class="report-nav-link" href="/reports/{_html(session_id)}/{_html(next_type)}">{_html(next_label)} →</a>
    </nav>
    """


def _report_shell(title: str, subtitle: str, body: str, session_id: str | None = None, report_type: str | None = None) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_html(title)}</title>
  <style>
    :root {{ --bg:#fff7ed; --card:#fff; --ink:#2f1d14; --muted:#80685c; --line:#f0dfd1; --orange:#ff7a3d; --amber:#f6a800; --green:#2fad5b; --red:#e85f3a; --soft:#fff2df; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif; line-height:1.55; }}
    a {{ color:inherit; }}
    .page {{ max-width:1160px; margin:0 auto; padding:28px 24px 56px; }}
    .nav {{ display:flex; justify-content:space-between; color:var(--muted); font-size:14px; margin-bottom:18px; }}
    .hero {{ border-radius:22px; color:#fff; background:linear-gradient(120deg,#ff733f,#f6b73c); padding:30px; margin-bottom:28px; box-shadow:0 12px 26px rgba(91,55,27,.08); }}
    .kicker {{ font-size:15px; font-weight:800; opacity:.92; }}
    h1 {{ margin:8px 0; font-size:40px; line-height:1.12; letter-spacing:0; }}
    h2 {{ margin:0 0 20px; font-size:24px; }}
    h3 {{ margin:0 0 8px; font-size:18px; }}
    p {{ margin:0; }}
    .hero p {{ max-width:880px; color:rgba(255,255,255,.9); }}
    .meta {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:22px; }}
    .meta-item {{ background:rgba(255,255,255,.24); border:1px solid rgba(255,255,255,.38); border-radius:16px; padding:14px 16px; }}
    .meta-label {{ color:rgba(255,255,255,.78); font-size:13px; }}
    .meta-value {{ margin-top:4px; color:#fff; font-size:18px; font-weight:850; }}
    .grid {{ display:grid; gap:26px; }}
    .two {{ grid-template-columns:1fr 1fr; }}
    .three {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .four {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .card {{ background:var(--card); border:1px solid var(--line); border-radius:22px; box-shadow:0 12px 26px rgba(91,55,27,.08); padding:30px; margin-top:28px; }}
    .result {{ display:grid; grid-template-columns:300px 1fr; gap:28px; align-items:center; }}
    .ring {{ width:190px; aspect-ratio:1; margin:0 auto; display:grid; place-items:center; border-radius:50%; background:conic-gradient(var(--amber) 0 var(--deg),#f2e6d7 var(--deg) 360deg); position:relative; }}
    .ring::after {{ content:""; position:absolute; inset:22px; border-radius:50%; background:#fff; }}
    .score {{ position:relative; z-index:1; color:var(--amber); text-align:center; font-size:54px; font-weight:850; line-height:1; }}
    .score span {{ display:block; margin-top:8px; color:var(--muted); font-size:14px; font-weight:700; }}
    .badge {{ display:inline-flex; margin-top:20px; padding:6px 16px; border-radius:999px; background:#fff8eb; border:1px solid #ffc46f; color:#e85f22; font-weight:850; }}
    .summary {{ color:var(--muted); font-size:17px; }}
    .pill-row {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin-top:22px; }}
    .pill {{ background:var(--soft); border-radius:18px; padding:16px; text-align:center; }}
    .pill-label {{ color:var(--muted); font-weight:700; font-size:14px; }}
    .pill-score {{ margin-top:4px; color:var(--orange); font-size:28px; font-weight:850; }}
    .pill-score small {{ color:var(--ink); font-size:16px; }}
    .metric {{ background:#fffaf5; border:1px solid var(--line); border-radius:16px; padding:18px; min-height:116px; }}
    .metric-label {{ color:var(--muted); font-size:14px; font-weight:700; }}
    .metric-value {{ margin-top:4px; color:var(--orange); font-size:25px; font-weight:850; }}
    .metric-note {{ margin-top:6px; color:var(--muted); font-size:13px; }}
    .table {{ width:100%; border-collapse:collapse; }}
    .table th,.table td {{ padding:13px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    .table th {{ color:var(--muted); font-size:14px; font-weight:800; }}
    .tag {{ display:inline-flex; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:850; }}
    .tag.good {{ background:#eaf8ef; color:var(--green); }}
    .tag.mid {{ background:#fff4d8; color:#d98600; }}
    .tag.bad {{ background:#fff0ea; color:var(--red); }}
    .block {{ border:1px solid var(--line); border-radius:18px; padding:20px; background:#fffaf5; }}
    .block ul {{ margin:8px 0 0; color:var(--muted); }}
    .report-nav {{ display:flex; justify-content:space-between; gap:16px; margin-top:32px; }}
    .report-nav-link {{ display:flex; align-items:center; justify-content:center; min-height:44px; padding:10px 18px; border:1px solid var(--line); border-radius:999px; background:#fff; color:var(--orange); text-decoration:none; font-weight:850; box-shadow:0 8px 20px rgba(91,55,27,.06); }}
    .report-nav-link:hover {{ background:var(--soft); }}
    .footer {{ text-align:center; margin-top:32px; color:var(--muted); font-size:13px; }}
    @media (max-width:840px) {{ .page{{padding:20px 14px 42px;}} h1{{font-size:30px;}} .meta,.two,.three,.four,.result,.pill-row{{grid-template-columns:1fr;}} .card{{padding:22px;border-radius:18px;}} .report-nav{{flex-direction:column;}} }}
  </style>
</head>
<body>
  <main class="page">
    <div class="nav"><span>{_html(subtitle)}</span><span>{DISCLAIMER}</span></div>
    <section class="hero">
      <div class="kicker">{_html(subtitle)}</div>
      <h1>{_html(title)}</h1>
      <p>{DISCLAIMER} 报告基于用户提交问卷、已固化公开数据和可采集数据口径生成；签约、选址和投资决策前必须完成实地核验、合同审查和完整财务测算。</p>
    </section>
    {body}
    {_report_nav(session_id, report_type)}
    <div class="footer">{DISCLAIMER} 签约或开店前请核验铺位、人流、合同、品牌政策和财务模型。</div>
  </main>
</body>
</html>"""


def _hero_meta(ctx: dict, extra_label="意向品牌", extra_value=None) -> str:
    loc = ctx["location"]
    region = " / ".join([x for x in [loc.get("province"), loc.get("city"), loc.get("district"), loc.get("street")] if x]) or ctx["city"]
    return f"""
      <div class="meta">
        <div class="meta-item"><div class="meta-label">目标区域</div><div class="meta-value">{_html(region)}</div></div>
        <div class="meta-item"><div class="meta-label">意向赛道</div><div class="meta-value">{_html(ctx["track"])}</div></div>
        <div class="meta-item"><div class="meta-label">用户预算</div><div class="meta-value">{_html(ctx["budget"])} 万元</div></div>
        <div class="meta-item"><div class="meta-label">{_html(extra_label)}</div><div class="meta-value">{_html(extra_value or ctx["brand"])}</div></div>
      </div>
    """


def _city_metrics(ctx: dict) -> str:
    city_data = ctx["city_data"]
    return f"""
    <section class="card">
      <h2>公开城市数据</h2>
      <div class="grid four">
        <div class="metric"><div class="metric-label">常住人口</div><div class="metric-value">{_html(city_data["population"])}</div><div class="metric-note">城市基本盘，需细化到街道。</div></div>
        <div class="metric"><div class="metric-label">城镇化率</div><div class="metric-value">{_html(city_data["urbanization"])}</div><div class="metric-note">高密度消费场景基础。</div></div>
        <div class="metric"><div class="metric-label">社零总额</div><div class="metric-value">{_html(city_data["retail_sales"])}</div><div class="metric-note">消费市场规模参考。</div></div>
        <div class="metric"><div class="metric-label">人均可支配收入</div><div class="metric-value">{_html(city_data["income"])}</div><div class="metric-note">饮品消费支付能力参考。</div></div>
      </div>
    </section>"""


def _render_compatibility_report(survey_data: dict, session_id: str | None = None) -> str:
    ctx = _survey_context(survey_data)
    score = ctx["score"]
    deg = max(0, min(360, int(score * 3.6)))
    reasons = "".join(f"<li>{_html(r)}</li>" for r in ctx["reasons"]) or "<li>暂无明显风险原因，建议继续补齐选址和品牌数据。</li>"
    recs = "".join(f"<li>{_html(r)}</li>" for r in ctx["recommendations"]) or "<li>先完成轻资产测试、候选铺位核验和品牌合同审查。</li>"
    body = f"""
    {_hero_meta(ctx)}
    <section class="card result">
      <div style="text-align:center;"><div class="ring" style="--deg:{deg}deg"><div class="score">{score}<span>综合评分 / 100</span></div></div><div class="badge">{_html(ctx["level"])}</div></div>
      <div>
        <h2>核心结论</h2>
        <p class="summary">用户当前预算为 {_html(ctx["budget"])} 万元，意向赛道为 {_html(ctx["track"])}，目标城市为 {_html(ctx["city"])}。综合评分 {_html(score)} 分，适合作为网络初筛进入下一步，但最终需要选址、品牌和财务数据核验。</p>
        <div class="pill-row">
          <div class="pill"><div class="pill-label">资金匹配度</div><div class="pill-score">{ctx["dim_financial"]}<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">经验适配度</div><div class="pill-score">{ctx["dim_experience"]}<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">时间/心态适配度</div><div class="pill-score">{ctx["dim_time"]}<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">区域适配度</div><div class="pill-score">{ctx["dim_region"]}<small>/25</small></div></div>
        </div>
      </div>
    </section>
    {_city_metrics(ctx)}
    <section class="grid two">
      <div class="card"><h2>风险原因</h2><div class="block"><ul>{reasons}</ul></div></div>
      <div class="card"><h2>行动建议</h2><div class="block"><ul>{recs}</ul></div></div>
    </section>
    <section class="card">
      <h2>数据核验状态</h2>
      <table class="table">
        <tr><th>数据项</th><th>状态</th><th>说明</th></tr>
        <tr><td>用户画像与四维评分</td><td><span class="tag good">已由问卷生成</span></td><td>来自本次 survey.html 提交。</td></tr>
        <tr><td>城市公开数据</td><td><span class="tag good">已固化公开来源</span></td><td>当前内置南京公开统计数据。</td></tr>
        <tr><td>具体铺位、人流、租金</td><td><span class="tag bad">必须核验</span></td><td>需要地图 API、候选铺位资料和实地记录。</td></tr>
        <tr><td>品牌合同与真实回本</td><td><span class="tag bad">必须核验</span></td><td>需要招商确认、合同样本和加盟商访谈。</td></tr>
      </table>
    </section>
    """
    return _report_shell(f"{ctx['track']} · {ctx['city']}综合适配度报告", "功能一 · 综合适配度", body, session_id, "compatibility")


def _render_location_report(survey_data: dict, session_id: str | None = None) -> str:
    ctx = _survey_context(survey_data)
    score = min(100, max(35, ctx["dim_region"] * 2 + 22))
    deg = int(score * 3.6)
    body = f"""
    {_hero_meta(ctx, "报告类型", "选址网络初筛")}
    <section class="card result">
      <div style="text-align:center;"><div class="ring" style="--deg:{deg}deg"><div class="score">{score}<span>选址初筛分 / 100</span></div></div><div class="badge">进入候选铺位采集</div></div>
      <div>
        <h2>核心结论</h2>
        <p class="summary">当前只能做城市和商圈模型初筛，不能给出具体店铺排名。建议优先筛选社区入口、地铁通勤、写字楼边缘等轻资产点位；不建议直接进入高租金核心商场或品牌密集街区。</p>
        <div class="pill-row">
          <div class="pill"><div class="pill-label">城市基本盘</div><div class="pill-score">22<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">区域明确度</div><div class="pill-score">{ctx["dim_region"]}<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">预算承压</div><div class="pill-score">12<small>/25</small></div></div>
          <div class="pill"><div class="pill-label">数据完整度</div><div class="pill-score">10<small>/25</small></div></div>
        </div>
      </div>
    </section>
    {_city_metrics(ctx)}
    <section class="card">
      <h2>候选商圈模型</h2>
      <div class="grid three">
        <div class="block"><h3>优先：社区 + 地铁通勤</h3><ul><li>复购稳定，租金压力相对可控。</li><li>需要核验早晚高峰人流和外卖覆盖。</li></ul></div>
        <div class="block"><h3>备选：高校/写字楼边缘</h3><ul><li>客群明确，但假期和周末波动较大。</li><li>需要核验峰值时段和客单价。</li></ul></div>
        <div class="block"><h3>暂缓：核心商场</h3><ul><li>曝光高，但租金、扣点和竞争压力高。</li><li>当前预算和经验容错不足。</li></ul></div>
      </div>
    </section>
    <section class="card">
      <h2>需要进一步核实的数据</h2>
      <table class="table">
        <tr><th>数据</th><th>来源</th><th>状态</th></tr>
        <tr><td>500m/1000m 内奶茶、咖啡、甜品 POI</td><td>百度/高德地图 API</td><td><span class="tag mid">待接入 API</span></td></tr>
        <tr><td>竞品评分、评论、价格带、营业时间</td><td>点评/外卖公开页</td><td><span class="tag mid">待人工采集</span></td></tr>
        <tr><td>候选铺位租金、转让费、面积、工程条件</td><td>房东/中介/实地看铺</td><td><span class="tag bad">必须核验</span></td></tr>
        <tr><td>真实客流和峰值时段</td><td>实地蹲点统计</td><td><span class="tag bad">必须核验</span></td></tr>
      </table>
    </section>
    """
    return _report_shell(f"{ctx['city']} · {ctx['track']}选址分析报告", "功能二 · 选址分析", body, session_id, "location")


MATCH_DIMENSIONS = [
    ("品牌实力", 20, "品牌规模、城市认知、供应链、门店稳定性"),
    ("加盟扶持", 18, "培训、督导、选址、开业陪跑、运营支持"),
    ("资金匹配", 18, "用户预算 vs 品牌总投资、备用金、回本压力"),
    ("产品竞争力", 15, "产品价格带、复购、差异化、目标客群适配"),
    ("风险管控", 15, "闭店风险、合同风险、区域保护、供应链风险"),
    ("理念契合", 14, "用户目标、投入时间、经验与品牌经营要求是否匹配"),
]


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _match_level(score: float) -> str:
    if score >= 90:
        return "极佳匹配"
    if score >= 80:
        return "高度匹配"
    if score >= 70:
        return "一般匹配"
    if score >= 60:
        return "谨慎匹配"
    return "低匹配"


def _match_tag(score: float) -> str:
    if score >= 80:
        return "good"
    if score >= 60:
        return "mid"
    return "bad"


def _brand_profile(brand: str) -> dict:
    if brand in BRAND_PUBLIC_DATA:
        return BRAND_PUBLIC_DATA[brand]
    return {
        "category": "待确认品类",
        "headquarter": "待确认",
        "positioning": "未进入内置品牌库",
        "store_count": "待公开资料补充",
        "revenue": "待公开资料补充",
        "members": "待公开资料补充",
        "supply_chain": "待公开资料补充",
        "new_products": "待公开资料补充",
        "investment_min": 0,
        "investment_max": 0,
        "franchise_fee": None,
        "deposit": None,
        "decoration_fee": None,
        "equipment_fee": None,
        "design_fee": None,
        "rent_estimate": None,
        "first_material_fee": None,
        "reserve_fund": None,
        "gross_margin": 0.60,
        "avg_ticket": 12,
        "monthly_fixed_cost": 4.0,
        "fit_store_type": "待品牌确认",
        "support": ["待招商资料确认"],
        "risk_notes": ["该品牌未进入内置品牌库，所有费用和政策均需核验"],
        "ratings": {
            "brand_power": 0.50,
            "support": 0.50,
            "product": 0.50,
            "risk_control": 0.45,
            "concept": 0.50,
        },
        "source_label": "品牌官方公开资料，待接入",
        "source_url": "#",
        "updated_at": "待更新",
    }


def _score_to_weight(raw: float, weight: float) -> float:
    return round(max(0.0, min(float(weight), raw)), 1)


def _budget_ratio(ctx: dict, brand_data: dict) -> float:
    budget = _safe_float(ctx.get("budget"))
    investment = _safe_float(brand_data.get("investment_max"))
    if investment <= 0:
        return 0.55
    return max(0.0, min(1.25, budget / investment))


def _generate_brand_match_analysis(ctx: dict, brand: str, brand_data: dict) -> dict:
    ratings = brand_data.get("ratings", {})
    budget_ratio = _budget_ratio(ctx, brand_data)
    background = ctx["background"]
    experience = ctx["experience"]
    financial = ctx["financial"]
    investment = ctx["investment"]
    goals = investment.get("investment_goals") or []
    no_debt = financial.get("fund_source") != "银行贷款/负债"
    has_ops_skill = bool(set(experience.get("mgmt_skills") or []) & {"线上营销/外卖运营", "供应链/采购管理", "团队招聘与培训"})
    has_catering_exp = experience.get("catering_background") in {"基层经验", "管理经验"}
    is_managed = background.get("startup_form") == "兼职/托管模式"
    weekly_hours = _safe_float(background.get("weekly_hours"))
    max_loss = _safe_float(financial.get("max_loss"))

    score_inputs = {
        "品牌实力": (
            20 * (0.55 + 0.25 * min(budget_ratio, 1) + (0.10 if no_debt else 0) + (0.10 if "品牌溢价" in goals else 0)),
            20 * ratings.get("brand_power", 0.5),
            "投资人预算与资金结构达到品牌初筛门槛，但南京开放名额仍需确认。",
            f"{brand} 的品牌规模、会员与供应链公开信息支撑较强，符合品牌偏好型投资目标。",
            "公开数据+待招商确认",
        ),
        "加盟扶持": (
            18 * (ratings.get("support", 0.5) + (0.08 if not has_catering_exp else 0) + (0.04 if has_ops_skill else 0)),
            18 * ratings.get("support", 0.5),
            "用户餐饮经验不足，更依赖品牌培训、督导和开业陪跑。",
            "品牌扶持能力越强，越能覆盖用户首次创业和托管经营短板。",
            "公开数据+待合同确认",
        ),
        "资金匹配": (
            18 * min(budget_ratio, 1.0) - (2 if max_loss and max_loss < 10 else 0),
            18 * min(budget_ratio, 1.0) - (1.5 if is_managed else 0),
            "预算可覆盖基础投资时匹配度上升；若最大亏损容忍较低，品牌会视为风险点。",
            "投资人需要确认总投资、备用金和租金后仍不突破预算。",
            "内置品牌库+需招商报价确认",
        ),
        "产品竞争力": (
            15 * (0.65 + (0.12 if ctx["track"] == "现制饮品（奶茶/咖啡）" else 0) + (0.08 if has_ops_skill else 0)),
            15 * ratings.get("product", 0.5),
            "用户意向赛道与品牌品类一致，线上运营能力有助于放大产品效率。",
            "产品价格带、复购和新品效率需要与南京目标客群进一步匹配。",
            "公开数据+待本地口碑采集",
        ),
        "风险管控": (
            15 * ((0.45 if is_managed else 0.60) + (0.18 if no_debt else 0) + (0.10 if max_loss >= 10 else 0)),
            15 * ratings.get("risk_control", 0.5),
            "托管模式会提高执行风险；无负债和较高止损能力能改善品牌侧判断。",
            "投资人需重点核验闭店、区域保护、物料价格和合同退出条款。",
            "待合同/实地核验",
        ),
        "理念契合": (
            14 * ((0.55 if is_managed else 0.70) + (0.12 if weekly_hours >= 20 else 0) + (0.12 if "长期稳健" in goals else 0)),
            14 * (ratings.get("concept", 0.5) + (0.08 if "品牌溢价" in goals else 0)),
            "用户偏托管且追求稳健，适合标准化强、督导强的品牌。",
            "品牌调性与用户目标契合，但需要确认是否允许低驻店依赖经营。",
            "问卷数据+待招商确认",
        ),
    }

    scores = []
    for dimension, weight, _desc in MATCH_DIMENSIONS:
        brand_to_investor, investor_to_brand, reason_b, reason_i, data_status = score_inputs[dimension]
        missing_fee = brand_data.get("investment_max") in (None, 0)
        if missing_fee and dimension == "资金匹配":
            brand_to_investor -= 4
            investor_to_brand -= 4
            data_status = "待招商确认"
        scores.append({
            "dimension": dimension,
            "weight": weight,
            "brand_to_investor": _score_to_weight(brand_to_investor, weight),
            "investor_to_brand": _score_to_weight(investor_to_brand, weight),
            "reason_brand_to_investor": reason_b,
            "reason_investor_to_brand": reason_i,
            "data_status": data_status,
        })

    total_b = round(sum(item["brand_to_investor"] for item in scores), 1)
    total_i = round(sum(item["investor_to_brand"] for item in scores), 1)
    if total_i >= 80 and total_b >= 65:
        final = f"可优先沟通{brand}，但必须核验南京加盟名额、真实总投资和合同条款。"
    elif total_i >= 70:
        final = f"{brand}可进入备选清单，建议先完成招商确认和候选点位测算。"
    else:
        final = f"{brand}当前匹配度不足，建议先比较低投入或更强托管支持的品牌。"

    return {
        "brand_name": brand,
        "city": ctx["city"],
        "scores": scores,
        "total": {
            "brand_to_investor": total_b,
            "investor_to_brand": total_i,
        },
        "conclusions": {
            "brand_to_investor": _match_level(total_b),
            "investor_to_brand": _match_level(total_i),
            "final_recommendation": final,
        },
        "verification_required": [
            f"{ctx['city']}区域是否开放加盟",
            "真实总投资是否超过用户预算",
            "区域保护条款",
            "驻店或托管要求",
            "真实单店流水和回本周期",
        ],
    }


def _comparison_rows(selected_brand: str) -> str:
    rows = []
    for name in ["茶百道", "古茗", "蜜雪冰城", "沪上阿姨"]:
        data = BRAND_PUBLIC_DATA[name]
        selected = " <span class=\"tag good\">推荐</span>" if name == selected_brand else ""
        rows.append(
            f"<tr><td><strong>{_html(name)}</strong>{selected}</td>"
            f"<td>{_html(data['investment_min'])}-{_html(data['investment_max'])} 万</td>"
            f"<td>{_html(data['positioning'])}</td>"
            f"<td>{_html(data['fit_store_type'])}</td>"
            f"<td>{_html(data['updated_at'])}</td></tr>"
        )
    return "".join(rows)


def _fee_rows(brand_data: dict) -> str:
    items = [
        ("前期固定", "加盟费", brand_data.get("franchise_fee"), "官方/招商口径，需确认"),
        ("前期固定", "保证金", brand_data.get("deposit"), "合同可退条件需确认"),
        ("前期固定", "装修费", brand_data.get("decoration_fee"), "按标准店估算"),
        ("前期固定", "设备费", brand_data.get("equipment_fee"), "总部统一配置"),
        ("前期固定", "设计/培训/线上服务费", brand_data.get("design_fee"), "合同细则需确认"),
        ("运营投入", "租金（押一付三）", brand_data.get("rent_estimate"), "按南京普通铺位估算"),
        ("运营投入", "首批物料", brand_data.get("first_material_fee"), "品牌供应链价格需确认"),
        ("运营投入", "备用金", brand_data.get("reserve_fund"), "人力、营销、现金周转"),
    ]
    rows = []
    total = 0.0
    for category, label, value, note in items:
        if value is None:
            amount = "待确认"
        else:
            total += _safe_float(value)
            amount = f"{_safe_float(value):.1f}"
        rows.append(f"<tr><td>{_html(category)}</td><td>{_html(label)}</td><td>{_html(amount)}</td><td>{_html(note)}</td></tr>")
    rows.append(f"<tr><td colspan=\"2\"><strong>总投资估算</strong></td><td><strong>{total:.1f}</strong></td><td>万元；不替代招商正式报价</td></tr>")
    return "".join(rows)


def _payback_rows(brand_data: dict) -> str:
    avg_ticket = _safe_float(brand_data.get("avg_ticket"), 12)
    gross_margin = _safe_float(brand_data.get("gross_margin"), 0.60)
    fixed = _safe_float(brand_data.get("monthly_fixed_cost"), 4.0)
    investment = sum(_safe_float(brand_data.get(key)) for key in [
        "franchise_fee", "deposit", "decoration_fee", "equipment_fee", "design_fee",
        "rent_estimate", "first_material_fee", "reserve_fund",
    ])
    scenarios = [("保守", 250), ("中性", 360), ("乐观", 480)]
    rows = []
    for name, cups in scenarios:
        monthly_revenue = cups * avg_ticket * 30 / 10000
        gross_profit = monthly_revenue * gross_margin
        net_profit = max(0.1, gross_profit - fixed)
        months = investment / net_profit if net_profit else 99
        rows.append(f"<tr><td>{name}</td><td>{cups} 杯</td><td>{monthly_revenue:.1f} 万</td><td>{net_profit:.1f} 万</td><td>{months:.1f} 个月</td></tr>")
    return "".join(rows)


def _breakeven_text(brand_data: dict) -> str:
    avg_ticket = _safe_float(brand_data.get("avg_ticket"), 12)
    gross_margin = _safe_float(brand_data.get("gross_margin"), 0.60)
    fixed = _safe_float(brand_data.get("monthly_fixed_cost"), 4.0)
    daily_fixed = fixed * 10000 / 30
    contribution = avg_ticket * gross_margin
    cups = daily_fixed / contribution if contribution else 0
    return f"日固定成本约 {daily_fixed:.0f} 元；客单价 {avg_ticket:.0f} 元，毛利率 {gross_margin * 100:.0f}% 时，日盈亏平衡约 {cups:.0f} 杯。"


def _render_score_rows(analysis: dict) -> str:
    rows = []
    for item in analysis["scores"]:
        rows.append(
            f"<tr><td>{_html(item['dimension'])}</td><td>{item['weight']:.1f}</td>"
            f"<td style=\"color:var(--orange);font-weight:850;\">{item['brand_to_investor']:.1f}</td>"
            f"<td style=\"color:var(--green);font-weight:850;\">{item['investor_to_brand']:.1f}</td>"
            f"<td><span class=\"tag mid\">{_html(item['data_status'])}</span></td></tr>"
        )
    rows.append(
        f"<tr><td><strong>总分</strong></td><td><strong>100.0</strong></td>"
        f"<td><strong>{analysis['total']['brand_to_investor']:.1f}</strong></td>"
        f"<td><strong>{analysis['total']['investor_to_brand']:.1f}</strong></td><td></td></tr>"
    )
    return "".join(rows)


def _render_reason_blocks(analysis: dict) -> str:
    blocks = []
    for idx, item in enumerate(analysis["scores"], 1):
        blocks.append(
            f"<div class=\"block\"><h3>{idx}. {_html(item['dimension'])}</h3>"
            f"<ul><li>品牌对投资人：{_html(item['reason_brand_to_investor'])}</li>"
            f"<li>投资人对品牌：{_html(item['reason_investor_to_brand'])}</li>"
            f"<li>数据状态：{_html(item['data_status'])}</li></ul></div>"
        )
    return "".join(blocks)


def _render_brand_report(survey_data: dict, session_id: str | None = None) -> str:
    ctx = _survey_context(survey_data)
    brand = ctx["brand"] if ctx["brand"] != "待填写品牌" else "茶百道"
    brand_data = _brand_profile(brand)
    analysis = _generate_brand_match_analysis(ctx, brand, brand_data)
    total_b = analysis["total"]["brand_to_investor"]
    total_i = analysis["total"]["investor_to_brand"]
    score = round((total_b + total_i) / 2, 1)
    deg = int(score * 3.6)
    verify_items = "".join(f"<li>{_html(item)}</li>" for item in analysis["verification_required"])
    support_items = "".join(f"<li>{_html(item)}</li>" for item in brand_data.get("support", []))
    risk_items = "".join(f"<li>{_html(item)}</li>" for item in brand_data.get("risk_notes", []))
    city_data = ctx["city_data"]

    body = f"""
    {_hero_meta(ctx, "意向品牌", brand)}
    <section class="card result">
      <div style="text-align:center;"><div class="ring" style="--deg:{deg}deg"><div class="score">{score}<span>双向均分 / 100</span></div></div><div class="badge">{_html(analysis['conclusions']['final_recommendation'])}</div></div>
      <div>
        <h2>核心结论</h2>
        <p class="summary">品牌对投资人：<strong>{total_b:.1f}</strong>（{_html(analysis['conclusions']['brand_to_investor'])}）；投资人对品牌：<strong>{total_i:.1f}</strong>（{_html(analysis['conclusions']['investor_to_brand'])}）。{_html(analysis['conclusions']['final_recommendation'])}</p>
        <div class="pill-row">
          <div class="pill"><div class="pill-label">品牌对投资人</div><div class="pill-score">{total_b:.1f}<small>/100</small></div></div>
          <div class="pill"><div class="pill-label">投资人对品牌</div><div class="pill-score">{total_i:.1f}<small>/100</small></div></div>
          <div class="pill"><div class="pill-label">预算</div><div class="pill-score">{_html(ctx['budget'])}<small>万</small></div></div>
          <div class="pill"><div class="pill-label">数据模式</div><div class="pill-score" style="font-size:18px;">混合<small>模式</small></div></div>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>一、双向匹配打分结论及原因</h2>
      <table class="table">
        <tr><th>评估维度</th><th>权重</th><th>品牌对投资人</th><th>投资人对品牌</th><th>数据状态</th></tr>
        {_render_score_rows(analysis)}
      </table>
      <div class="grid two" style="margin-top:20px;">
        <div class="block"><h3>品牌对投资人 {total_b:.1f} · {_html(analysis['conclusions']['brand_to_investor'])}</h3><ul><li>预算、资金来源和投资目标达到初筛要求。</li><li>餐饮经验和托管投入仍需品牌确认可接受。</li><li>南京开放名额与驻店要求必须向招商确认。</li></ul></div>
        <div class="block"><h3>投资人对品牌 {total_i:.1f} · {_html(analysis['conclusions']['investor_to_brand'])}</h3><ul><li>品牌规模、供应链和产品力符合品牌偏好目标。</li><li>需要确认真实总投资和回本周期不会突破风险承受力。</li><li>适合先沟通，再进入选址和合同核验。</li></ul></div>
      </div>
      <div class="grid three" style="margin-top:20px;">{_render_reason_blocks(analysis)}</div>
    </section>

    <section class="card">
      <h2>二、市场分析（全国 / {_html(ctx['city'])} / 目标区域）</h2>
      <div class="grid four">
        <div class="metric"><div class="metric-label">全国品牌数据</div><div class="metric-value">{_html(brand_data['store_count'])}</div><div class="metric-note">{_html(brand_data['revenue'])}</div></div>
        <div class="metric"><div class="metric-label">{_html(ctx['city'])}消费基本盘</div><div class="metric-value">{_html(city_data['retail_sales'])}</div><div class="metric-note">社零总额，城市级公开数据</div></div>
        <div class="metric"><div class="metric-label">人口与收入</div><div class="metric-value">{_html(city_data['population'])}</div><div class="metric-note">人均可支配收入 {_html(city_data['income'])}</div></div>
        <div class="metric"><div class="metric-label">目标区域数据</div><div class="metric-value">待采集</div><div class="metric-note">需地图 POI、外卖和实地人流补充</div></div>
      </div>
      <div class="block" style="margin-top:18px;"><h3>公开信息摘要</h3><ul><li>{_html(brand_data['supply_chain'])}</li><li>{_html(brand_data['new_products'])}</li><li>{_html(brand_data['members'])}</li></ul></div>
    </section>

    <section class="card">
      <h2>三、四大品牌全方面互调</h2>
      <table class="table">
        <tr><th>对比品牌</th><th>单店投资</th><th>品牌定位</th><th>适配店型</th><th>数据更新时间</th></tr>
        {_comparison_rows(brand)}
      </table>
      <div class="block" style="margin-top:18px;"><strong>对比总结：</strong>{_html(brand)} 当前进入优先沟通清单，但不应跳过费用、合同、区域保护、真实门店经营数据核验。</div>
    </section>

    <section class="card">
      <h2>四、加盟品牌选择建议及理由</h2>
      <div class="block"><h3>核心建议</h3><p class="summary">{_html(analysis['conclusions']['final_recommendation'])}</p></div>
      <div class="grid two" style="margin-top:18px;">
        <div class="block"><h3>品牌扶持</h3><ul>{support_items}</ul></div>
        <div class="block"><h3>风险前置</h3><ul>{risk_items}</ul></div>
      </div>
    </section>

    <section class="card">
      <h2>五、投资预算汇总表（单位：万元）</h2>
      <table class="table">
        <tr><th>费用类别</th><th>费用明细</th><th>金额</th><th>备注</th></tr>
        {_fee_rows(brand_data)}
      </table>
    </section>

    <section class="grid two">
      <div class="card">
        <h2>六、回本周期测算表</h2>
        <table class="table">
          <tr><th>场景</th><th>日均销量</th><th>月营收</th><th>月净利</th><th>回本周期</th></tr>
          {_payback_rows(brand_data)}
        </table>
      </div>
      <div class="card">
        <h2>七、每日盈亏平衡表</h2>
        <div class="block"><h3>测算结论</h3><p class="summary">{_html(_breakeven_text(brand_data))}</p></div>
        <div class="block" style="margin-top:16px;"><h3>经营动作</h3><ul><li>第 1-90 天重点优化出杯效率、正式开业、外卖托管。</li><li>长期运营需每周复盘现金流、损耗、优化成本与客流。</li></ul></div>
      </div>
    </section>

    <section class="card">
      <h2>八、必须进一步核验的数据</h2>
      <table class="table">
        <tr><th>核验类别</th><th>核验内容</th><th>来源</th><th>状态</th></tr>
        <tr><td>招商</td><td>{_html(ctx['city'])}是否开放加盟、是否有区域名额</td><td>品牌招商顾问</td><td><span class="tag bad">必须核验</span></td></tr>
        <tr><td>合同</td><td>区域保护、退出条款、违约责任、物料价格机制</td><td>加盟合同样本</td><td><span class="tag bad">必须核验</span></td></tr>
        <tr><td>选址</td><td>品牌门店、竞品、学校/写字楼/小区 POI</td><td>地图 API + 实地</td><td><span class="tag mid">待采集</span></td></tr>
        <tr><td>财务</td><td>真实流水、净利、回本周期</td><td>加盟商访谈/经营数据</td><td><span class="tag bad">必须核验</span></td></tr>
      </table>
      <div class="block" style="margin-top:18px;"><h3>核验清单</h3><ul>{verify_items}</ul></div>
    </section>

    <section class="card">
      <h2>九、引用来源</h2>
      <table class="table">
        <tr><td>{_html(brand_data['source_label'])}</td><td><a href="{_html(brand_data['source_url'])}">{_html(brand_data['source_url'])}</a></td></tr>
        <tr><td>南京市统计局 / 南京市政府公开数据</td><td><a href="https://tjj.nanjing.gov.cn/njstjj/202504/t20250401_5108470.html">统计公报</a>；<a href="https://www.nanjing.gov.cn/sjfb/sjfb/202502/t20250207_5069723.html">主要指标</a></td></tr>
      </table>
    </section>
    """
    return _report_shell(f"{ctx['city']} · {brand}加盟品牌双向适配报告", "功能三 · 加盟品牌双向适配", body, session_id, "brand")

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
    SESSIONS[session_id] = {'analysis': analysis, 'survey': data, 'chat': []}
    reports = {
        "compatibility": f"/reports/{session_id}/compatibility",
        "location": f"/reports/{session_id}/location",
        "brand": f"/reports/{session_id}/brand",
    }
    return {"session_id": session_id, "analysis": analysis, "reports": reports}

# Root - serve survey.html
@app.get("/")
async def root():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'survey.html')
    if os.path.exists(path):
        with open(path) as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Survey not found")


@app.get("/reports/{session_id}/{report_type}")
async def dynamic_report(session_id: str, report_type: str):
    session = SESSIONS.get(session_id)
    if not session:
        return HTMLResponse(content="报告会话不存在，请重新提交问卷。", status_code=404)
    survey_data = session.get("survey") or {}
    if report_type == "compatibility":
        return HTMLResponse(content=_render_compatibility_report(survey_data, session_id))
    if report_type == "location":
        return HTMLResponse(content=_render_location_report(survey_data, session_id))
    if report_type == "brand":
        return HTMLResponse(content=_render_brand_report(survey_data, session_id))
    return HTMLResponse(content="未知报告类型。", status_code=404)
