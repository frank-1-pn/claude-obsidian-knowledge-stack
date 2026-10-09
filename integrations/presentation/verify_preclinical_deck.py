"""Verify analysis-to-native-PPTX correspondence, not scientific truth."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET

NS={"a":"http://schemas.openxmlformats.org/drawingml/2006/main","c":"http://schemas.openxmlformats.org/drawingml/2006/chart","p":"http://schemas.openxmlformats.org/presentationml/2006/main"}

def verify(analysis:Path,project:Path):
    data=json.loads(analysis.read_bytes())
    receipt=json.loads((project/"build-receipt.json").read_text(encoding="utf-8"))
    digest=hashlib.sha256(analysis.read_bytes()).hexdigest()
    assert data["data_kind"]=="synthetic-preclinical-demo", "Unexpected data kind"
    assert receipt["analysis_sha256"]==digest, "Analysis lineage mismatch"
    pptx=project/"preclinical-demo.pptx"
    assert receipt["pptx_sha256"]==hashlib.sha256(pptx.read_bytes()).hexdigest(), "Deck differs from receipt"
    with zipfile.ZipFile(pptx) as archive:
        assert archive.testzip() is None, "Corrupt ZIP member"
        charts=[n for n in archive.namelist() if n.startswith("ppt/charts/chart") and n.endswith(".xml")]
        assert len(charts)==1, "One native evidence chart expected"
        chart=ET.fromstring(archive.read(charts[0]))
        values=[float(e.text) for e in chart.findall('.//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v',NS)]
        expected=[data["efficacy"]["groups"][k]["mean_mm3"] for k in ["vehicle","low","high"]]
        assert values==expected, ("Chart data mismatch",values,expected)
        tables=[]
        for i in range(1,6):
            root=ET.fromstring(archive.read(f"ppt/slides/slide{i}.xml"))
            visible=''.join(e.text or '' for e in root.findall('.//a:t',NS))
            assert "合成数据演示" in visible, f"Slide {i} lacks disclosure"
            tables.extend(root.findall('.//a:tbl',NS))
            notes=archive.read(f"ppt/notesSlides/notesSlide{i}.xml").decode()
            assert digest in notes, f"Slide {i} lacks source hash in notes"
        assert len(tables)==2, "Two native tables expected"
        table_text=[''.join(e.text or '' for e in t.findall('.//a:t',NS)) for t in tables]
        assert all(unit in table_text[0] for unit in ["差值 mm³","95% CI","Holm P","终点降幅"]), "Statistical labels or units missing"
        assert all(unit in table_text[1] for unit in ["Cmax mg/L","Tmax h","AUC mg·h/L","t½ h","外推 AUC %"]), "PK labels or units missing"
        for c in data["efficacy"]["comparisons"]:
            ci=c["mean_difference_ci95_unadjusted_mm3"]
            for value in [f"{c['mean_difference_mm3']:.2f}",f"[{ci[0]:.2f}, {ci[1]:.2f}]",f"{c['p_holm']:.3g}",f"{c['relative_endpoint_reduction_pct']:.2f}%"]:
                assert value in table_text[0], f"Statistical table missing {value}"
        pk=next(t for t in data["pk"]["report"]["tables"] if t["title"]=="per-subject parameters")
        rows=tables[1].findall('./a:tr',NS)[1:]
        assert len(rows)==len(pk["rows"]), "PK profile omitted"
        for actual,r in zip(rows,pk["rows"]):
            cells=[''.join(e.text or '' for e in c.findall('.//a:t',NS)) for c in actual.findall('./a:tc',NS)]
            expected=[r["id"],f"{r['cmax']:.3f}",f"{r['tmax']:.2f}",f"{r['auc_last']:.3f}",f"{r['t_half']:.2f}",f"{r['pct_auc_extrap']:.2f}"]
            assert cells==expected, ("PK row mismatch",cells,expected)
    return {"status":"passed","slides":5,"native_charts":1,"native_tables":2,"analysis_sha256":digest,"checked":"source lineage, numeric native chart values, statistics, all PK rows, units/disclosures and notes"}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--analysis",required=True,type=Path)
    parser.add_argument("--project",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.analysis,args.project),ensure_ascii=True))
