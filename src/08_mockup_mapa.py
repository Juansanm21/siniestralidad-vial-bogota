"""Genera docs/mockup_monitoreo_mapa.html: dashboard de monitoreo centrado en el mapa, con los datos reales
de fallecidos 2021-2025 (bases oficiales de los Anuarios) incrustados en el archivo.

Ejecutar desde la carpeta siniestros:  ..\\.venv\\Scripts\\python src\\08_mockup_mapa.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "raw" / "anuarios" / "parquet"


def prep(si, av, kcol, ycol):
    si = si.copy()
    for c in ["Latitud", "Longitud"]:
        si[c] = pd.to_numeric(si[c].astype(str).str.replace(",", "."), errors="coerce")
    f = av[av.Gravedad_Indicador_30d.str.upper() == "MUERTO"].copy()
    esp = f.Condicion_Especifica.fillna("")
    f["a"] = np.select([esp.isin(["Motociclista", "Pasajero Motocicleta"]), esp.eq("Peatón"),
                        esp.isin(["Ciclista", "Pasajero Bicicleta"])], [0, 1, 2], 3)
    f = f.merge(si[[kcol, "Latitud", "Longitud", "Con_Carga"]].rename(columns={"Con_Carga": "carga_s"}), on=kcol, how="left")
    f = f[f[ycol].astype(int) >= 2021].dropna(subset=["Latitud", "Longitud"])
    f = f[f.Latitud.between(4.4, 4.85) & f.Longitud.between(-74.25, -73.98)]
    hcol = [c for c in f.columns if c.lower().startswith("hour")][0]
    return pd.DataFrame({"y": f[ycol].astype(int), "la": f.Latitud.round(4), "lo": f.Longitud.round(4), "a": f.a,
                         "h": pd.to_numeric(f[hcol], errors="coerce").fillna(-1).astype(int),
                         "c": f.carga_s.astype(str).str.upper().eq("SI").astype(int),
                         "l": f.Localidad.astype(str).str.upper().str.strip()})


d = pd.concat([prep(pd.read_parquet(P / "siniestros_2024.parquet"), pd.read_parquet(P / "actor_vial_2024.parquet"),
                    "Codigo_Accidente", "AnnoAcc"),
               prep(pd.read_parquet(P / "siniestros_2025.parquet"), pd.read_parquet(P / "actor_vial_2025.parquet"),
                    "Codigo_Siniestro", "AnnoSiniestro")])
locs = sorted(d.l.unique())
d["l"] = d.l.map({n: i for i, n in enumerate(locs)})
data = json.dumps(d[["y", "la", "lo", "a", "h", "c", "l"]].values.tolist(), separators=(",", ":"))

HTML = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Monitoreo vial Bogotá</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0B1220;--card:#121B2D;--line:#1F2A40;--tx:#E6EDF5;--mu:#8A97AD;--moto:#F28C38;--pea:#4EA8F0;--bici:#4FBF9F;--otro:#7A869E}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font-family:Inter,sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:18px 22px}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:12px}
.top h1{margin:0;font-size:24px;font-weight:800;letter-spacing:-.02em}.top h1 em{font-style:normal;color:var(--moto)}
.top p{margin:4px 0 0;color:var(--mu);font-size:13px}
.filters{display:flex;flex-wrap:wrap;gap:18px;margin:14px 0}
.fg span{display:block;font-size:11px;color:var(--mu);letter-spacing:.1em;text-transform:uppercase;margin-bottom:5px;font-weight:700}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{border:1px solid var(--line);background:var(--card);color:var(--tx);border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer;font-family:inherit}
.chip.on{background:var(--tx);color:var(--bg);border-color:var(--tx)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:12px}
@media (max-width:900px){.grid{grid-template-columns:1fr !important}#map{height:480px !important}.top{flex-direction:column;align-items:flex-start;gap:6px}}
.k{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.k .q{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--moto);font-weight:700}
.k .v{font-size:30px;font-weight:800;margin:4px 0 0;letter-spacing:-.02em}.k .s{font-size:12px;color:var(--mu)}
.grid{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1fr);gap:12px}
#map{height:640px;border-radius:14px;border:1px solid var(--line);background:#0e1626}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:12px}
.panel h3{margin:0 0 4px;font-size:15px}.panel p{margin:0 0 10px;font-size:12px;color:var(--mu)}
.bars{display:flex;align-items:flex-end;gap:2px;height:120px}.bars div{flex:1;border-radius:2px 2px 0 0;background:var(--otro);position:relative}
.axis{display:flex;justify-content:space-between;font-size:10px;color:var(--mu);margin-top:4px}
.rank div{display:flex;align-items:center;gap:8px;margin:6px 0;font-size:12px}.rank b{width:118px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank i{display:block;height:8px;border-radius:4px;background:var(--moto)}
.leg{display:flex;gap:14px;font-size:12px;color:var(--mu);margin-top:8px}.leg i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:var(--card);color:var(--tx)}
.leaflet-container{font-family:Inter,sans-serif}
</style></head><body><div class="wrap">
<div class="top"><div><h1>¿A dónde se movió la muerte en las vías de <em>Bogotá</em>?</h1>
<p>Monitoreo de personas fallecidas en siniestros viales · cada punto es una persona · Anuarios SDM 2021–2025</p></div>
<div style="text-align:right;font-size:12px;color:var(--mu)">Definición oficial: fallecido a 30 días</div></div>

<div class="filters">
 <div class="fg"><span>Año</span><div class="chips" id="fy"></div></div>
 <div class="fg"><span>Actor vial</span><div class="chips" id="fa"></div></div>
 <div class="fg"><span>Hora</span><div class="chips" id="fh"></div></div>
 <div class="fg"><span>Contraparte</span><div class="chips" id="fc"></div></div>
 <div class="fg"><span>Vista del mapa</span><div class="chips" id="fv"></div></div>
</div>

<div class="kpis">
 <div class="k"><div class="q">Cuántos</div><div class="v" id="k1">—</div><div class="s">personas fallecidas</div></div>
 <div class="k"><div class="q">Quién</div><div class="v" id="k2">—</div><div class="s">eran motociclistas</div></div>
 <div class="k"><div class="q">Cuándo</div><div class="v" id="k3">—</div><div class="s">murieron entre 0 y 5 h</div></div>
 <div class="k"><div class="q">Contra qué</div><div class="v" id="k4">—</div><div class="s">con vehículo de carga</div></div>
 <div class="k"><div class="q">Dónde</div><div class="v" id="k5" style="font-size:20px;margin-top:10px">—</div><div class="s" id="k5s">localidad con más muertes</div></div>
</div>

<div class="grid">
 <div><div id="map"></div>
  <div class="leg"><span><i style="background:var(--moto)"></i>Motociclista</span><span><i style="background:var(--pea)"></i>Peatón</span><span><i style="background:var(--bici)"></i>Ciclista</span><span><i style="background:var(--otro)"></i>Otro</span><span>· clic en un punto para ver el detalle</span></div></div>
 <div>
  <div class="panel"><h3>¿A qué hora?</h3><p>Fallecidos por hora del día (naranja = 0 a 5 h)</p><div class="bars" id="hb"></div><div class="axis"><span>0h</span><span>6h</span><span>12h</span><span>18h</span><span>23h</span></div></div>
  <div class="panel"><h3>¿Cómo evoluciona?</h3><p>Fallecidos por año con los filtros actuales</p><div class="bars" id="yb" style="height:90px"></div><div class="axis" id="ya"></div></div>
  <div class="panel"><h3>¿Dónde se concentra?</h3><p>Top 6 localidades con los filtros actuales</p><div class="rank" id="rk"></div></div>
 </div>
</div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js"></script>
<script>
const D=__DATA__, LOC=__LOCS__;
const ACT=['Motociclista','Peatón','Ciclista','Otro'], COL=['#F28C38','#4EA8F0','#4FBF9F','#7A869E'];
const S={y:'all',a:'all',h:'all',c:'all',v:'pts'};
const map=L.map('map',{zoomControl:true,preferCanvas:true}).setView([4.64,-74.11],11.3);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',{attribution:'Esri, HERE, Garmin, © OpenStreetMap',maxZoom:16}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',{maxZoom:16,pane:'shadowPane'}).addTo(map);
let layer=null;
function chips(id,key,opts){const el=document.getElementById(id);el.innerHTML='';opts.forEach(([v,t])=>{const b=document.createElement('button');b.className='chip'+(S[key]===v?' on':'');b.textContent=t;b.onclick=()=>{S[key]=v;render()};el.appendChild(b)})}
function pass(r){return (S.y==='all'||r[0]==S.y)&&(S.a==='all'||r[3]==S.a)&&(S.h==='all'||(S.h==='n'?r[4]>=0&&r[4]<=5:S.h==='d'?r[4]>=6&&r[4]<=17:r[4]>=18))&&(S.c==='all'||r[5]==1)}
function render(){
 chips('fy','y',[['all','2021–2025'],[2021,'2021'],[2022,'2022'],[2023,'2023'],[2024,'2024'],[2025,'2025']]);
 chips('fa','a',[['all','Todos'],[0,'Motociclistas'],[1,'Peatones'],[2,'Ciclistas']]);
 chips('fh','h',[['all','Todo el día'],['n','0–5 h'],['d','6–17 h'],['e','18–23 h']]);
 chips('fc','c',[['all','Todas'],['c','Solo con carga']]);
 chips('fv','v',[['pts','Puntos'],['heat','Calor']]);
 const F=D.filter(pass), n=F.length||1;
 k1.textContent=F.length.toLocaleString('es-CO');
 k2.textContent=Math.round(F.filter(r=>r[3]==0).length/n*100)+'%';
 k3.textContent=Math.round(F.filter(r=>r[4]>=0&&r[4]<=5).length/n*100)+'%';
 k4.textContent=Math.round(F.filter(r=>r[5]==1).length/n*100)+'%';
 const lc={};F.forEach(r=>lc[r[6]]=(lc[r[6]]||0)+1);const top=Object.entries(lc).sort((a,b)=>b[1]-a[1]);
 k5.textContent=top.length?LOC[top[0][0]].charAt(0)+LOC[top[0][0]].slice(1).toLowerCase():'—';
 k5s.textContent=top.length?top[0][1]+' fallecidos ('+Math.round(top[0][1]/n*100)+'%)':'';
 if(layer)map.removeLayer(layer);
 if(S.v==='heat'){layer=L.heatLayer(F.map(r=>[r[1],r[2],0.6]),{radius:14,blur:18,maxZoom:14,gradient:{0.2:'#3a2412',0.5:'#C96A24',0.8:'#F28C38',1:'#FFE3C7'}}).addTo(map)}
 else{layer=L.layerGroup(F.map(r=>L.circleMarker([r[1],r[2]],{radius:r[3]==0?4:3.2,color:COL[r[3]],weight:0,fillOpacity:r[3]==0?.85:.6,fillColor:COL[r[3]]})
   .bindPopup('<b>'+ACT[r[3]]+'</b><br>Año '+r[0]+' · '+(r[4]>=0?r[4]+':00 h':'hora sin dato')+'<br>'+(r[5]?'Con vehículo de carga':'Sin vehículo de carga')+'<br>'+LOC[r[6]]))).addTo(map)}
 const hc=Array(24).fill(0);F.forEach(r=>{if(r[4]>=0)hc[r[4]]++});const hm=Math.max(...hc,1);
 hb.innerHTML=hc.map((v,i)=>'<div title="'+i+' h: '+v+'" style="height:'+(v/hm*100)+'%;background:'+(i<=5?'#F28C38':'#3A4558')+'"></div>').join('');
 const ys=[2021,2022,2023,2024,2025],yc=ys.map(y=>D.filter(r=>r[0]==y&&(S.a==='all'||r[3]==S.a)&&(S.h==='all'||(S.h==='n'?r[4]>=0&&r[4]<=5:S.h==='d'?r[4]>=6&&r[4]<=17:r[4]>=18))&&(S.c==='all'||r[5]==1)).length),ym=Math.max(...yc,1);
 yb.innerHTML=yc.map((v,i)=>'<div title="'+ys[i]+': '+v+'" style="height:'+(v/ym*100)+'%;background:'+(S.y==ys[i]?'#F28C38':'#3A4558')+'"></div>').join('');
 ya.innerHTML=ys.map(y=>'<span>'+y+'</span>').join('');
 const tm=top.length?top[0][1]:1;
 rk.innerHTML=top.slice(0,6).map(([l,v])=>'<div><b>'+LOC[l].charAt(0)+LOC[l].slice(1).toLowerCase()+'</b><span style="flex:1"><i style="width:'+(v/tm*100)+'%"></i></span><span>'+v+'</span></div>').join('');
}
render();
</script></body></html>"""

out = ROOT / "docs" / "mockup_monitoreo_mapa.html"
out.write_text(HTML.replace("__DATA__", data).replace("__LOCS__", json.dumps(locs, ensure_ascii=False)), encoding="utf-8")
print(f"{out} · {len(d)} puntos · {out.stat().st_size / 1e3:.0f} KB")
