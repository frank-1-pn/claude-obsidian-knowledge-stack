"""Render scientific-pack analysis JSON through the actual pinned PPT Master exporter."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "vendor/ppt-master/skills/ppt-master"
FONT = "Microsoft YaHei"
COLOR = "#173C55"

def text(x, y, value, size=28, fill=COLOR, anchor="start", bold=False):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{700 if bold else 400}">{html.escape(str(value))}</text>'

def page(title, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="{FONT}" data-pptx-page-role="content"><rect id="page-background" data-pptx-role="background" width="1280" height="720" fill="#FFFFFF"/><g id="page-title" data-pptx-bounds="64 32 1152 76">{text(64,86,title,44,bold=True)}</g><g id="page-body" data-pptx-bounds="64 140 1152 490">{body}</g><g id="page-disclosure" data-pptx-bounds="64 640 1152 48">{text(64,674,"合成数据演示 · 不构成真实药效、安全性或临床证据",22)}</g></svg>'

def table_svg(key, columns, rows, widths, y=180, row_height=76, font_size=26):
    x, width = 64, 1152
    colwidths = [width * w / sum(widths) for w in widths]
    payload = {"schema":"ppt-master.semantic-table.v2", "name":key,"x":x,"y":y,"width":width,"height":row_height*(len(rows)+1),"columns":[{"text":c,"align":"l"} for c in columns],"rows":[[{"text":str(c),"align":"l"} for c in row] for row in rows],"column_widths":widths,"row_heights":[1]*(len(rows)+1),"style":{"font_family":FONT,"font_size":font_size,"header_font_size":font_size,"header_fill":COLOR,"header_text":"#FFFFFF","body_text":COLOR,"band_row":False,"padding":12,"valign":"middle"}}
    parts = [f'<g id="{key}" data-pptx-replace-with="table"><metadata type="application/json">{html.escape(json.dumps(payload,ensure_ascii=False))}</metadata>',f'<rect x="{x}" y="{y}" width="{width}" height="{row_height}" fill="{COLOR}"/>']
    for i, row in enumerate([columns]+rows):
        offset=x
        for j,value in enumerate(row):
            parts.append(text(round(offset+12,2),y+row_height*i+row_height/2+font_size/3,value,font_size,"#FFFFFF" if i==0 else COLOR))
            offset += colwidths[j]
    parts.append('</g>')
    return ''.join(parts)

def chart_svg(groups):
    categories = ["对照", "低剂量", "高剂量"]
    values = [groups[k]["mean_mm3"] for k in ["vehicle","low","high"]]
    maximum = math.ceil(max(values)/100)*100
    payload={"name":"endpoint-means","x":64,"y":166,"width":1152,"height":400,"plot_area":{"x":100,"y":170,"width":1060,"height":330},"type":"column","categories":categories,"series":[{"name":"终点均值 mm³","values":values}],"show_legend":False,"data_labels":{"show_value":True,"number_format":"0.00","position":"outside_end","font_family":FONT,"font_size":28,"color":COLOR},"axes":{"category":{"visible":True,"tick_marks":"none","font_family":FONT,"font_size":28,"color":COLOR},"value":{"visible":False,"minimum":0,"maximum":maximum,"major_gridlines":False}},"style":{"font_family":FONT,"axis_font_size":28,"text_color":COLOR,"colors":[COLOR],"chart_area_fill":"none","plot_area_fill":"none","axis_color":"none","grid_color":"none"}}
    parts=['<g id="endpoint-means" data-pptx-replace-with="chart"><metadata type="application/json">'+html.escape(json.dumps(payload,ensure_ascii=False))+'</metadata>']
    for i,value in enumerate(values):
        cx=276+i*360
        height=value/maximum*330
        parts.append(f'<rect x="{cx-76}" y="{500-height:.3f}" width="152" height="{height:.3f}" fill="{COLOR}"/>')
        parts.append(text(cx,500-height-16,f"{value:.2f}",28,anchor="middle"))
        parts.append(text(cx,550,categories[i],28,anchor="middle"))
    parts.append('</g>')
    return ''.join(parts)

def run(script, *arguments, log):
    command = [sys.executable,str(SKILL/"scripts"/script),*map(str,arguments)]
    result = subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
    log.append({"command":["python",f"vendor/ppt-master/skills/ppt-master/scripts/{script}",*map(str,arguments)],"exit_code":result.returncode,"output":result.stdout})
    print(result.stdout,flush=True)
    if result.returncode:
        raise RuntimeError(f"Upstream {script} failed with {result.returncode}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--analysis",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path,help="A NEW project directory, never overwritten")
    args=parser.parse_args()
    analysis_bytes=args.analysis.read_bytes()
    data=json.loads(analysis_bytes)
    import jsonschema
    jsonschema.validate(data,json.loads((ROOT/"integrations/scientific/output.schema.json").read_text(encoding="utf-8")))
    for comparison in data["efficacy"]["comparisons"]:
        group=comparison["contrast"].split("-")[0]
        baseline=data["efficacy"]["groups"]["vehicle"]["mean_mm3"]
        treated=data["efficacy"]["groups"][group]["mean_mm3"]
        if not math.isclose(comparison["mean_difference_mm3"],treated-baseline,rel_tol=1e-9,abs_tol=1e-9):
            raise ValueError("Input comparison differs from input group means")
        if not math.isclose(comparison["relative_endpoint_reduction_pct"],100*(baseline-treated)/baseline,rel_tol=1e-9,abs_tol=1e-9):
            raise ValueError("Input endpoint reduction differs from input group means")
    if data["pk"]["exit_code"] != 0:
        raise ValueError("PK upstream analysis is incomplete; refuse a complete-results deck")
    if args.output.exists():
        raise FileExistsError("Choose a fresh --output directory; existing project is preserved")
    output=args.output.resolve()
    output.mkdir(parents=True)
    (output/"sources").mkdir()
    (output/"sources/analysis.json").write_bytes(analysis_bytes)
    svg=output/"svg_output"
    svg.mkdir()
    (output/"notes").mkdir()
    log=[]
    try:
        run("attribution_guard.py",log=log)
        groups=data["efficacy"]["groups"]
        comparisons=data["efficacy"]["comparisons"]
        pk=next(t for t in data["pk"]["report"]["tables"] if t["title"]=="per-subject parameters")
        n=sum(g["n_animals"] for g in groups.values())
        slides=[page("临床前分析演示",text(64,240,"合成终点数据与独立模拟 PK 队列",38)+text(64,332,f"{n} 个虚拟终点观测，{len(pk['rows'])} 个虚拟 PK profile",30)+text(64,430,"输入分析 JSON 保留原始数据摘要与统计约定",28)+text(64,498,"所有数字从输入文件读取，可从同一输入重建",28))]
        detail="  ".join(f"{label} n={groups[k]['n_animals']}, SD={groups[k]['sd_mm3']:.2f}" for k,label in [("vehicle","对照"),("low","低剂量"),("high","高剂量")])
        slides.append(page("模拟终点体积均值（mm³）",chart_svg(groups)+text(64,614,detail,26)))
        rows=[]
        for c in comparisons:
            ci=c["mean_difference_ci95_unadjusted_mm3"]
            rows.append(["低剂量 vs 对照" if c["contrast"]=="low-vehicle" else "高剂量 vs 对照",f"{c['mean_difference_mm3']:.2f}",f"[{ci[0]:.2f}, {ci[1]:.2f}]",f"{c['p_holm']:.3g}",f"{c['relative_endpoint_reduction_pct']:.2f}%"])
        slides.append(page("预设比较与多重校正",table_svg("endpoint-tests",["比较","差值 mm³","95% CI 未校正","Holm P","终点降幅"],rows,[2.2,1.2,2.6,1.3,1.3],y=174)+text(64,470,"双侧 Welch t 检验，Holm 校正两个预设比较",28)+text(64,526,"CI 为逐比较区间，未作同时置信区间校正",28)+text(64,582,"终点降幅不是纵向肿瘤生长抑制率 TGI",28)))
        rows=[[r["id"],f"{r['cmax']:.3f}",f"{r['tmax']:.2f}",f"{r['auc_last']:.3f}",f"{r['t_half']:.2f}",f"{r['pct_auc_extrap']:.2f}"] for r in pk["rows"]]
        if len(rows)>4:
            raise ValueError("Demo design supports <= 4 PK subjects; redesign instead of dropping rows")
        slides.append(page("独立模拟队列的 PK 参数",table_svg("pk-parameters",["ID","Cmax mg/L","Tmax h","AUC mg·h/L","t½ h","外推 AUC %"],rows,[1.1,1.6,1.2,1.8,1.1,1.8],y=164,font_size=25)+text(64,538,f"AUC_last: {data['pk']['conventions']['auc_method']}；终末窗口 {data['pk']['conventions']['terminal_window_h']} h",26)+text(64,590,"PK 与终点队列分离，不能推断个体暴露与药效关系",26)))
        limitations=["合成数据中的显著性不能证明真实化合物有效。","单点体重描述不能代替毒理或 NOAEL 评估。","口服 CL/F 与 V/F 不能辨识生物利用度 F。","需真实实验设计、原始数据及专业审核才可用于决策。"]
        body=''.join(text(64,202+i*84,value,30) for i,value in enumerate(limitations))
        findings=data["pk"]["report"]["findings"]
        if findings:
            body+=text(64,574,f"PK 提示 {len(findings)} 项：详见讲者备注与输入 JSON",26)
        slides.append(page("解释范围与下一步",body))
        for i,content in enumerate(slides,1):
            (svg/f"slide_{i:02}.svg").write_text(content,encoding="utf-8")
            note={"data_kind":data["data_kind"],"analysis_sha256":hashlib.sha256(analysis_bytes).hexdigest(),"source_sha256":data["sources"],"analysis_plan":data["efficacy"]["analysis_plan"],"efficacy_limitations":data["efficacy"]["limitations"],"pk_conventions":data["pk"]["conventions"],"pk_limitations":data["pk"]["limitations"],"pk_findings":findings,"citation":data["citation"]}
            (output/"notes"/f"slide_{i:02}.md").write_text("# 合成数据演示\n\n"+json.dumps(note,ensure_ascii=False,indent=2),encoding="utf-8")
        (output/"spec_lock.md").write_text("<!-- ppt-master-schema: spec-lock/v1 -->\n# Execution Lock\n\n## canvas\n- viewBox: 0 0 1280 720\n- format: ppt169\n## communication\n- audience: R&D director\n- objective: Synthetic workflow demonstration\n- core_message: All figures derive from analysis JSON; no real efficacy or safety evidence\n## mode\n- mode: briefing\n## visual_style\n- visual_style: Flat editorial scientific report\n## colors\n- bg: #FFFFFF\n- primary: #173C55\n- accent: #173C55\n- text: #173C55\n## typography\n- font_family: Microsoft YaHei\n- title_family: Microsoft YaHei\n- body_family: Microsoft YaHei\n- title: 44\n- body: 28\n## icons\n- library: none\n- inventory: none\n## page_rhythm\n- P01: anchor\n- P02: dense\n- P03: dense\n- P04: dense\n- P05: anchor\n## pptx_structure\n- mode: flat\n## forbidden\n- Unsupported SVG constructs\n",encoding="utf-8")
        lock=output/"spec_lock.md"
        lock.write_text(lock.read_text(encoding="utf-8").replace("- body: 28\n", "- body: 28\n- table: 25\n- disclosure: 22\n").replace("- audience: R&D director\n", "- audience: R&D director\n- primary_language: zh-CN\n"),encoding="utf-8")
        outline=[("临床前分析演示","Identify the synthetic input and audience","Sample sizes and scope","none"),("模拟终点体积均值（mm³）","Compare synthetic endpoint means without real efficacy inference","One native editable mean chart and SD context","contrast: vehicle, low, high"),("预设比较与多重校正","Understand the declared statistical comparisons","Native statistics table and CI/multiplicity limitations","contrast: low vs vehicle, high vs vehicle"),("独立模拟队列的 PK 参数","Read PK parameters with units and cohort separation","Native per-subject PK table and method convention","membership: PK parameters belong to each synthetic profile"),("解释范围与下一步","Recognize limits before applying the workflow","Scientific limitations and input-bound notes","none")]
        design="<!-- ppt-master-schema: design-spec/v1 -->\n# Preclinical Demonstration - Design Spec\n\n## I. Project Information\n\nFive-slide synthetic analysis demonstration for an R&D director. Language zh-CN. Source: sources/analysis.json. Objective: reproduce computed evidence with explicit scientific limitations. Balanced reading mode, local editable PPTX. Speaker notes enabled; animation and narration disabled.\n\n## II. Canvas Specification\n\nPPT 16:9, 1280 × 720, viewBox `0 0 1280 720`, safe margins 64px.\n\n## III. Visual Theme\n\nFlat scientific report, white background and #173C55 text/data. Native data charts and tables carry the evidence. No decorative assets.\n\n## IV. Typography System\n\nMicrosoft YaHei. Titles 44px, body 28px, data tables 25px for complete column labels, persistent synthetic-data disclosure 22px to keep it visible without competing with the evidence.\n\n## V. Layout Strategy\n\nTitle above a single evidence composition; sufficient space below for interpretation. Chart compares groups; tables retain all required units and values.\n\n## VI. Icon Plan\n\nNo icons are needed for this report.\n\n## VIII. Image Resource List\n\nNo photographic or decorative image resources. Native editable evidence only.\n\n## IX. Content Outline\n\n"
        for i,(title,move,content,relationships) in enumerate(outline,1):
            design+=f"### Slide {i}: {title}\n\n- **Audience move**: {move}\n- **Content**: {content}\n- **Relationships**: {relationships}\n- **Data class**: scenario\n\n"
        design+="## X. Speaker Notes Requirements\n\n- **Generation**: enabled\n- **Filename**: match each SVG filename under notes/\n- **Content**: analysis hash, source hashes, declared methods, findings and all scientific limitations; synthetic data only\n- **Notes style**: formal source trace\n- **Presentation purpose**: reproducible synthetic analysis demonstration\n"
        (output/"design_spec.md").write_text(design,encoding="utf-8")
        run("stamp_native_fallbacks.py",svg,"--write",log=log)
        run("finalize_svg.py",output,log=log)
        run("svg_quality_checker.py",output,"--canonical-authoring","--stage","final","--json",log=log)
        pptx=output/"preclinical-demo.pptx"
        run("svg_to_pptx.py",output,"--native-charts-and-tables","--no-animations","-o",pptx,log=log)
        run("pptx_delivery_check.py",pptx,log=log)
        with zipfile.ZipFile(pptx) as archive:
            names=archive.namelist()
            nslides=sum(name.startswith("ppt/slides/slide") and name.endswith(".xml") for name in names)
            native_tables=sum(archive.read(name).count(b"<a:tbl>") for name in names if name.startswith("ppt/slides/") and name.endswith(".xml"))
            native_charts=sum(name.startswith("ppt/charts/chart") and name.endswith(".xml") for name in names)
            if (nslides,native_tables,native_charts)!=(5,2,1):
                raise RuntimeError(f"Unexpected native structure: {(nslides,native_tables,native_charts)}")
        receipt={"status":"local-generation-complete","workbuddy_runtime_verified":False,"generator":"pinned hugohe3/ppt-master svg_to_pptx.py","upstream_revision":"b4efe3ddf237a97a42880164759162f8e2412f2f","analysis_sha256":hashlib.sha256(analysis_bytes).hexdigest(),"pptx_sha256":hashlib.sha256(pptx.read_bytes()).hexdigest(),"slides":nslides,"native_tables":native_tables,"native_charts":native_charts,"commands":log}
        (output/"build-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in receipt.items() if k!="commands"},ensure_ascii=False),flush=True)
    except Exception:
        (output/"partial-build-log.json").write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding="utf-8")
        raise

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
