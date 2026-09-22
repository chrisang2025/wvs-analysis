"""Build the standalone synthetic WVS-style exploratory analysis page."""
from __future__ import annotations

import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "wvs-synthetic.csv"
OUT_PATH = ROOT / "index.html"
SEED = 20260922

NUMERIC = {
    "age", "life_satisfaction", "freedom_of_choice", "emancipative_values",
    "importance_of_god", "financial_satisfaction", "secular_values",
}
TYPES = {
    "country": "categorical text", "age": "numeric (years)", "urban_rural": "categorical text",
    "income_level": "ordered categorical text", "sex": "categorical text",
    "marital_status": "categorical text", "education": "ordered categorical text",
    "life_satisfaction": "numeric (1–10)", "freedom_of_choice": "numeric (1–10)",
    "emancipative_values": "numeric index (0–1)", "trust_people": "categorical text",
    "importance_of_god": "numeric (1–10)", "financial_satisfaction": "numeric (1–10)",
    "secular_values": "numeric index (0–1)",
}
COUNTRIES = ["China", "Singapore", "Turkey", "India", "Kazakhstan"]


def num(row, field):
    return float(row[field])


def build():
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        raw = list(reader)
    visible_fields = [f for f in fields if f != "respondent_id"]
    nonempty = {f: sum(bool(r[f].strip()) for r in raw) for f in visible_fields}
    complete = [r for r in raw if all(r[f].strip() for f in fields)]
    missing_rows = len(raw) - len(complete)
    duplicate_rows = len(raw) - len({tuple(r[f] for f in fields) for r in raw})

    by_country = {c: [r for r in complete if r["country"] == c] for c in COUNTRIES}
    averages = []
    radar = []
    for c, rows in by_country.items():
        averages.append({"country": c, "secular": mean(num(r, "secular_values") for r in rows),
                         "emancipative": mean(num(r, "emancipative_values") for r in rows)})
        radar.append({"country": c, "values": [
            mean(num(r, "life_satisfaction") for r in rows) / 10,
            sum(r["trust_people"] == "Trusted" for r in rows) / len(rows),
            mean(num(r, "importance_of_god") for r in rows) / 10,
            mean(num(r, "emancipative_values") for r in rows),
            mean(num(r, "secular_values") for r in rows),
            mean(num(r, "financial_satisfaction") for r in rows) / 10,
        ]})
    rng = random.Random(SEED)
    sample = []
    for c in ["China", "India"]:
        picked = rng.sample(by_country[c], min(300, len(by_country[c])))
        sample.extend({"country": c, "x": num(r, "secular_values"), "y": num(r, "emancipative_values")} for r in picked)
    heat = [[0] * 10 for _ in range(10)]
    for r in by_country["Singapore"]:
        heat[int(num(r, "life_satisfaction")) - 1][int(num(r, "financial_satisfaction")) - 1] += 1
    payload = {
        "fields": [{"name": f, "type": TYPES[f], "nonempty": nonempty[f]} for f in visible_fields],
        "rawN": len(raw), "analysisN": len(complete), "missingRows": missing_rows,
        "duplicates": duplicate_rows, "countryN": {c: len(by_country[c]) for c in COUNTRIES},
        "averages": averages, "radar": radar, "sample": sample, "heat": heat,
        "sourceHash": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()[:12], "seed": SEED,
    }
    page = HTML.replace("__DATA__", json.dumps(payload, separators=(",", ":")))
    OUT_PATH.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(page):,} bytes); {len(complete):,} complete rows analysed.")


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synthetic World Values Survey–style exploration</title>
<style>
:root{--ink:#17202a;--muted:#52616b;--paper:#fbfcfd;--line:#d8e0e5;--china:#E69F00;--singapore:#D55E00;--turkey:#CC79A7;--india:#0072B2;--kazakhstan:#009E73}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:1180px;margin:auto;padding:32px 22px 54px}h1{font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.12;margin:0 0 12px}h2{font-size:1.35rem;margin:0 0 6px}p{margin:0 0 14px}.lede{max-width:900px;font-size:1.08rem}.note{color:var(--muted);font-size:.92rem}.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:24px 0}.stat,section{background:white;border:1px solid var(--line);border-radius:10px}.stat{padding:14px}.stat b{display:block;font-size:1.4rem}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}section{padding:18px;margin-top:18px}.grid section{margin:0}.chart{width:100%;min-height:380px}.takeaway{border-top:1px solid var(--line);padding-top:11px;margin:8px 0 0}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line)}th:last-child,td:last-child{text-align:right}.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:.85rem;margin:8px 0}.key{display:inline-flex;align-items:center;gap:5px}.swatch{width:14px;height:14px;display:inline-block}.heatmap{display:grid;grid-template-columns:40px repeat(10,1fr);gap:2px;max-width:600px;margin:14px auto}.heatmap .label{font-size:.78rem;text-align:center;align-self:center}.cell{aspect-ratio:1;display:flex;align-items:center;justify-content:center;font-size:clamp(.55rem,1.6vw,.78rem);color:#13222a;min-width:0}.heat-title{text-align:center;font-size:.86rem;color:var(--muted)}.heat-y{writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;color:var(--muted);font-size:.82rem;margin:8px}.heat-layout{display:flex;align-items:center;justify-content:center}@media(max-width:760px){main{padding:24px 14px}.grid{grid-template-columns:1fr}.summary{grid-template-columns:1fr}.chart{min-height:320px}section{padding:14px}}
svg{overflow:visible}svg text{fill:var(--ink);font-family:inherit;font-size:12px}.axis{stroke:#87949c;stroke-width:1}.gridline{stroke:#e2e8eb;stroke-width:1}.point{stroke-width:1.5}.tooltip{position:fixed;display:none;background:#17202a;color:white;padding:6px 8px;border-radius:5px;font-size:12px;pointer-events:none;z-index:2}
</style></head><body><main>
<h1>Synthetic World Values Survey–style exploration</h1>
<p class="lede">This page explores <strong>synthetic (simulated)</strong> data: fabricated respondent records designed to resemble distributions and relationships in the <a href="https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp" target="_blank" rel="noopener">World Values Survey, Wave 7</a> model. It is not real survey data, and every pattern below is illustrative only. Countries represented: Turkey, India, Singapore, China, and Kazakhstan.</p>
<p class="note">Reference: World Values Survey Association, <a href="https://www.worldvaluessurvey.org/" target="_blank" rel="noopener">World Values Survey</a> (Wave 7 documentation). Source snapshot: <span id="hash"></span>.</p>
<div class="summary"><div class="stat"><b id="rawN"></b>source rows</div><div class="stat"><b id="analysisN"></b>complete rows analysed</div><div class="stat"><b id="missing"></b>rows excluded for ≥1 blank cell</div></div>
<section><h2>Data coverage and quality</h2><p id="quality"></p><div class="table-wrap"><table><thead><tr><th>Column</th><th>Data type</th><th>Non-empty observations</th></tr></thead><tbody id="fields"></tbody></table></div></section>
<div class="grid">
<section><h2>Cultural map — emancipative vs secular values</h2><p class="note">Country averages; each point represents a country, not an individual.</p><div id="cultural" class="chart"></div><p id="culturalTake" class="takeaway"></p></section>
<section><h2>Value fingerprints</h2><p class="note">Country averages normalised to a common 0–1 scale.</p><div id="radar" class="chart"></div><p id="radarTake" class="takeaway"></p></section>
</div>
<section><h2>Individual values — China vs India</h2><p class="note">Reproducible random sample of 300 complete respondents per country; outlined symbols show country averages.</p><div id="individual" class="chart"></div><p id="individualTake" class="takeaway"></p></section>
<section><h2>Life vs financial satisfaction — Singapore</h2><p class="note">Counts of complete respondents. Darker cells indicate more respondents.</p><div id="heatmap"></div><p id="heatTake" class="takeaway"></p></section>
</main><div id="tip" class="tooltip" role="status"></div>
<script>const D=__DATA__, C={China:'#E69F00',Singapore:'#D55E00',Turkey:'#CC79A7',India:'#0072B2',Kazakhstan:'#009E73'}, S={China:'circle',Singapore:'square',Turkey:'diamond',India:'triangle',Kazakhstan:'cross'}, fmt=n=>Number(n).toLocaleString(), q=n=>Math.round(n*100)/100;
document.querySelector('#hash').textContent=D.sourceHash;document.querySelector('#rawN').textContent=fmt(D.rawN);document.querySelector('#analysisN').textContent=fmt(D.analysisN);document.querySelector('#missing').textContent=fmt(D.missingRows);document.querySelector('#quality').textContent=`Duplicate-row check: ${D.duplicates===0?'no duplicate full rows found':fmt(D.duplicates)+' duplicate full rows found'}. All ${fmt(D.missingRows)} rows containing one or more empty cells were removed before analysis; country samples after that rule range from ${fmt(Math.min(...Object.values(D.countryN)))} to ${fmt(Math.max(...Object.values(D.countryN)))}.`;document.querySelector('#fields').innerHTML=D.fields.map(f=>`<tr><td>${f.name}</td><td>${f.type}</td><td>${fmt(f.nonempty)}</td></tr>`).join('');
function svg(el,w=600,h=360){el.innerHTML='';const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.setAttribute('viewBox',`0 0 ${w} ${h}`);s.setAttribute('width','100%');s.setAttribute('height',h);s.setAttribute('role','img');el.append(s);return s}function add(s,t,a={}){let e=document.createElementNS('http://www.w3.org/2000/svg',t);Object.entries(a).forEach(([k,v])=>e.setAttribute(k,v));s.append(e);return e}function text(s,x,y,v,a={}){let e=add(s,'text',{x,y,...a});e.textContent=v;return e}function mark(s,shape,x,y,color,r=5,outline=false){let e;if(shape==='square')e=add(s,'rect',{x:x-r,y:y-r,width:2*r,height:2*r,fill:outline?'white':color,stroke:color,'stroke-width':outline?3:1.5});else if(shape==='diamond')e=add(s,'path',{d:`M${x} ${y-r} L${x+r} ${y} L${x} ${y+r} L${x-r} ${y}Z`,fill:outline?'white':color,stroke:color,'stroke-width':outline?3:1.5});else if(shape==='triangle')e=add(s,'path',{d:`M${x} ${y-r} L${x+r} ${y+r} L${x-r} ${y+r}Z`,fill:outline?'white':color,stroke:color,'stroke-width':outline?3:1.5});else if(shape==='cross'){e=add(s,'path',{d:`M${x-r} ${y-r}L${x+r} ${y+r}M${x+r} ${y-r}L${x-r} ${y+r}`,stroke:color,'stroke-width':3,fill:'none'});}else e=add(s,'circle',{cx:x,cy:y,r,fill:outline?'white':color,stroke:color,'stroke-width':outline?3:1.5});return e}function tip(e,html){e.addEventListener('mousemove',x=>{let t=document.querySelector('#tip');t.innerHTML=html;t.style.display='block';t.style.left=x.clientX+12+'px';t.style.top=x.clientY+12+'px'});e.addEventListener('mouseleave',()=>document.querySelector('#tip').style.display='none')}
function scatter(id,data,opts){let s=svg(document.querySelector(id)),W=600,H=360,m={l:62,r:22,t:22,b:52},x0=opts.xd[0],x1=opts.xd[1],y0=opts.yd[0],y1=opts.yd[1],X=x=>m.l+(x-x0)/(x1-x0)*(W-m.l-m.r),Y=y=>H-m.b-(y-y0)/(y1-y0)*(H-m.t-m.b);for(let i=0;i<5;i++){let xv=x0+(x1-x0)*i/4,yv=y0+(y1-y0)*i/4;add(s,'line',{x1:X(xv),y1:m.t,x2:X(xv),y2:H-m.b,class:'gridline'});add(s,'line',{x1:m.l,y1:Y(yv),x2:W-m.r,y2:Y(yv),class:'gridline'});text(s,X(xv),H-30,q(xv),{'text-anchor':'middle'});text(s,54,Y(yv)+4,q(yv),{'text-anchor':'end'})}add(s,'rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'none',class:'axis'});text(s,W/2,H-7,opts.xlab,{'text-anchor':'middle'});text(s,16,H/2,opts.ylab,{transform:`rotate(-90 16 ${H/2})`,'text-anchor':'middle'});data.forEach(d=>{let e=mark(s,S[d.country],X(d.x),Y(d.y),C[d.country],opts.r||5,!!d.outline);tip(e,`${d.country}<br>${opts.xlab}: ${q(d.x)}<br>${opts.ylab}: ${q(d.y)}`);if(opts.labels)text(s,X(d.x)+8,Y(d.y)-8,d.country,{fill:C[d.country]})})}
const avg=D.averages.map(d=>({country:d.country,x:d.secular,y:d.emancipative}));scatter('#cultural',avg,{xd:[0,1],yd:[0,1],xlab:'Secular values (0–1)',ylab:'Emancipative values (0–1)',labels:true,r:7});let hi=[...avg].sort((a,b)=>b.y-a.y)[0],lo=[...avg].sort((a,b)=>a.y-b.y)[0];document.querySelector('#culturalTake').textContent=`Illustratively, ${hi.country} has the highest average emancipative-values score (${q(hi.y)}), while ${lo.country} is lowest (${q(lo.y)}). The five country averages occupy distinct positions on this synthetic cultural map.`;
function radar(){let s=svg(document.querySelector('#radar')),W=600,H=360,cx=300,cy=184,R=122,names=['Life satisfaction','Trust others','Importance of God','Emancipative values','Secular values','Financial satisfaction'],ang=i=>-Math.PI/2+i*Math.PI*2/6,pt=(v,i)=>[cx+Math.cos(ang(i))*R*v,cy+Math.sin(ang(i))*R*v];for(let lev=1;lev<=4;lev++){let p=Array.from({length:6},(_,i)=>pt(lev/4,i).join(',')).join(' ');add(s,'polygon',{points:p,fill:'none',class:'gridline'})}names.forEach((n,i)=>{let [x,y]=pt(1,i);add(s,'line',{x1:cx,y1:cy,x2:x,y2:y,class:'axis'});text(s,x+(x-cx)*.12,y+(y-cy)*.12,n,{'text-anchor':x<cx-5?'end':x>cx+5?'start':'middle'})});D.radar.forEach(d=>{let p=d.values.map((v,i)=>pt(v,i).join(',')).join(' ');add(s,'polygon',{points:p,fill:C[d.country],'fill-opacity':'.09',stroke:C[d.country],'stroke-width':2,'stroke-dasharray':d.country==='Turkey'?'6 3':'none'});d.values.forEach((v,i)=>mark(s,S[d.country],...pt(v,i),C[d.country],4));});let l=add(s,'g',{});D.radar.forEach((d,i)=>{mark(l,S[d.country],15+i*116,342,C[d.country],4);text(l,25+i*116,346,d.country)});let god=D.radar.map(d=>({country:d.country,v:d.values[2]})).sort((a,b)=>b.v-a.v)[0];document.querySelector('#radarTake').textContent=`The synthetic profiles differ most visibly in the balance between religiosity and the two values indices. ${god.country} has the highest average normalised importance-of-God score (${q(god.v)}); read the overlapping shapes as broad similarities, not real estimates.`}radar();
const cloud=D.sample.map(d=>({country:d.country,x:d.x,y:d.y}));scatter('#individual',cloud,{xd:[0,1],yd:[0,1],xlab:'Secular values (0–1)',ylab:'Emancipative values (0–1)',r:3});avg.filter(d=>d.country==='China'||d.country==='India').forEach(d=>{d.outline=true;let s=document.querySelector('#individual svg'),W=600,H=360,m={l:62,r:22,t:22,b:52},X=x=>m.l+x*(W-m.l-m.r),Y=y=>H-m.b-y*(H-m.t-m.b);let e=mark(s,S[d.country],X(d.x),Y(d.y),C[d.country],9,true);tip(e,`${d.country} average<br>Secular: ${q(d.x)}<br>Emancipative: ${q(d.y)}`)});let ca=avg.find(d=>d.country==='China'),ia=avg.find(d=>d.country==='India');document.querySelector('#individualTake').textContent=`The sampled China and India clouds overlap substantially across both dimensions, even though their average locations differ (China: ${q(ca.x)}, ${q(ca.y)}; India: ${q(ia.x)}, ${q(ia.y)}). This shows how country-average differences can coexist with considerable individual-level variation in the simulated data.`;
function heat(){let h=document.querySelector('#heatmap'),max=Math.max(...D.heat.flat()),out='<div class="heat-title">Financial satisfaction →</div><div class="heat-layout"><div class="heat-y">Life satisfaction →</div><div class="heatmap"><div></div>'+Array.from({length:10},(_,i)=>`<div class="label">${i+1}</div>`).join('');for(let r=9;r>=0;r--){out+=`<div class="label">${r+1}</div>`;for(let c=0;c<10;c++){let v=D.heat[r][c],a=.08+.82*v/max;out+=`<div class="cell" style="background:rgba(0,114,178,${a})" aria-label="Life ${r+1}, financial ${c+1}: ${v} respondents">${v||''}</div>`}}h.innerHTML=out+'</div></div>';let peak=0,pr=0,pc=0;D.heat.forEach((row,r)=>row.forEach((v,c)=>{if(v>peak){peak=v;pr=r+1;pc=c+1}}));document.querySelector('#heatTake').textContent=`In this synthetic Singapore sample, the most common pairing is life satisfaction ${pr} and financial satisfaction ${pc} (${fmt(peak)} respondents). The darker concentration along the lower-left to upper-right direction illustrates a positive association, not a causal relationship.`}heat();
</script></body></html>'''

if __name__ == "__main__":
    build()
