#!/usr/bin/env python3
"""Maintainer-only rebuild from an already fetched exact upstream checkout.

Uses git object bytes (not Windows checkout line endings). Refuses to replace a
nonempty vendor directory. Ordinary replication uses the committed snapshot.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request

REVISION = "92ace75ac21efe19a620434e0ca4e356081fe807"
REPOSITORY = "https://github.com/K-Dense-AI/scientific-agent-skills"
SELECTION = [
    ("database-lookup", "靶点与管线公开证据", "公共数据库检索", "复现 PubChem、ChEMBL、UniProt 等公开数据库检索；不替代智慧芽商业管线库", "named APIs; public/registered/licensed access differs"),
    ("depmap", "靶点与管线公开证据", "癌症靶点依赖", "分析 CRISPR gene effect 与 PRISM 药敏，提出癌种选择性依赖假设", "release-specific DepMap downloads; no private datasets included"),
    ("rdkit", "药物发现与ADMET", "分子结构与性质", "解析 SMILES/SDF、分子描述符、指纹和结构相似性", "RDKit native package, isolated environment"),
    ("medchem", "药物发现与ADMET", "药化筛选与结构警示", "应用 Lipinski/Veber、PAINS 等结构规则进行候选物筛选；规则不证明安全或药效", "medchem/RDKit; optional catalogs have their own terms"),
    ("pytdc", "药物发现与ADMET", "ADMET基准与模型评估", "使用 Therapeutics Data Commons 数据集、任务切分与指标评价；预测不等同实测毒理", "PyTDC version/Python constraints; dataset/oracle download is optional"),
    ("pkpd-modeling", "PKPD与临床前安全", "PKPD建模", "NCA、群体PK准备、暴露反应等研究工作流；本包实际调用其离线NCA脚本", "NumPy/SciPy; licensed engines are separate and not invoked"),
    ("relsa-severity-assessment", "PKPD与临床前安全", "动物福利严重度", "整合体重、体温、行为等读数做RELSA严重度探索；不作人道终点自动决策", "RELSA/foRcast tooling; study-specific reference set needed"),
    ("analytical-method-validation", "PKPD与临床前安全", "分析方法验证材料", "组织准确度、精密度、线性、定量限及转移证据；不自动批准方法放行", "stdlib helpers; qualified review and applicable standards needed"),
    ("experimental-design", "实验设计与统计", "实验设计", "数据收集前定义实验单位、对照、随机化、区组、板布局，避免伪重复", "design-specific Python tools; biological assumptions required"),
    ("statistical-power", "实验设计与统计", "样本量与功效", "在实验前依据效应量、变异和设计计算样本量或模拟功效", "NumPy/SciPy/statsmodels and optional simulation dependencies"),
    ("statistical-analysis", "实验设计与统计", "统计分析与报告", "选择检验、核对假设、效应量和区间、校正多重比较并完整报告", "SciPy/pingouin/statsmodels; Bayesian alternatives need separate packages"),
    ("statsmodels", "实验设计与统计", "回归与混合模型", "OLS、GLM、混合模型和诊断；重复测量须正确建模依赖关系", "statsmodels isolated environment"),
    ("uncertainty-and-units", "实验设计与统计", "单位与测量不确定度", "单位换算、维度核对、误差传播及数量级合理性检查", "pint/uncertainties; measurement uncertainty assumptions"),
    ("biopython", "生信与机制", "序列与分子生物学", "FASTA/GenBank/PDB解析、序列操作及NCBI/PubMed批量访问", "Biopython; network only for external retrieval"),
    ("bulk-rnaseq", "生信与机制", "转录组计数准备", "FASTQ/Salmon/STAR到基因计数，保留参考基因组、链特异性及重复信息", "bioinformatics CLI/containers; hardware and reference downloads"),
    ("pydeseq2", "生信与机制", "差异表达分析", "有生物学重复的bulk RNA-seq差异表达、明确contrast与FDR", "PyDESeq2; validated counts, design matrix and replication required"),
    ("scanpy", "生信与机制", "单细胞分析", "scRNA-seq质控、归一化、聚类、标记探索与pseudobulk准备", "Scanpy/AnnData; counts/expression provenance and memory planning"),
    ("pathway-enrichment", "生信与机制", "通路与基因集富集", "ORA/GSEA与通路解释，核对基因ID、背景集合、重复检验和冗余", "gseapy/optional services; gene-set versions and licensing"),
    ("literature-review", "精选通用科研技能", "文献综述", "记录检索式、筛选、证据覆盖与局限，建立可复查的综述工作流", "network for databases; paid Parallel/OpenRouter and PDF engines are optional"),
    ("citation-management", "精选通用科研技能", "引文核对", "核实DOI与论文元数据并管理BibTeX，避免虚构引用", "requests and relevant public APIs; obey rate limits/access terms"),
    ("scientific-critical-thinking", "精选通用科研技能", "科学证据审阅", "识别偏倚、混杂、设计缺陷及统计解释边界", "evidence-bound document review; no external model/API needed by definition"),
    ("scientific-writing", "精选通用科研技能", "科学报告写作", "按证据provenance和报告规范起草科研材料，核对引用、表图和责任声明", "local helpers; optional external tools not enabled automatically"),
    ("exploratory-data-analysis", "精选通用科研技能", "探索性数据检查", "CSV等支持格式的缺失、异常、泄漏与敏感性检查", "stdlib core with optional format-specific packages"),
    ("scientific-visualization", "精选通用科研技能", "科学图表", "制作可追溯、显示不确定性与缺失数据的科研图表并核验导出", "Matplotlib/Seaborn/Plotly; separate from PPT Master deck construction"),
]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "knowledge-stack-snapshot/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-local", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    vendor = root.parents[1] / "vendor/scientific-agent-skills"
    if vendor.exists() and any(vendor.iterdir()):
        raise SystemExit("Refusing to replace existing vendor snapshot")
    names = [row[0] for row in SELECTION]
    paths = [f"skills/{name}" for name in names] + ["LICENSE.md", "CITATION.cff"]
    listing = subprocess.check_output(["git", "-C", str(args.upstream_local), "ls-tree", "-r", REVISION, "--", *paths], text=True)
    records = []
    for line in listing.splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, blob = meta.split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError(f"unexpected upstream object: {line}")
        data = subprocess.check_output(["git", "-C", str(args.upstream_local), "cat-file", "blob", blob])
        output = vendor / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        records.append({"path": path, "git_blob": blob, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    licenses = []
    sources = [
        ("rdkit", "rdkit/rdkit", "master", "license.txt"),
        ("scanpy", "scverse/scanpy", "main", "LICENSE"),
        ("statsmodels", "statsmodels/statsmodels", "main", "LICENSE.txt"),
        ("medchem", "datamol-io/medchem", "main", "LICENSE.md"),
        ("biopython", "biopython/biopython", "master", "LICENSE.rst"),
    ]
    for name, repository, branch, path in sources:
        commit = json.loads(get(f"https://api.github.com/repos/{repository}/commits/{branch}"))["sha"]
        url = f"https://raw.githubusercontent.com/{repository}/{commit}/{path}"
        data = get(url)
        local = f"licenses/{name}.txt"
        output = vendor / local
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        licenses.append({"skill": name, "path": local, "source_url": url, "revision": commit, "sha256": hashlib.sha256(data).hexdigest()})
    data = get("https://creativecommons.org/licenses/by/4.0/legalcode.txt")
    output = vendor / "licenses/CC-BY-4.0.txt"
    output.write_bytes(data)
    licenses.append({"skill": "depmap", "path": "licenses/CC-BY-4.0.txt", "source_url": "https://creativecommons.org/licenses/by/4.0/legalcode.txt", "sha256": hashlib.sha256(data).hexdigest()})
    catalog = []
    for name, category, title, purpose, dependencies in SELECTION:
        skill = (vendor / f"skills/{name}/SKILL.md").read_text(encoding="utf-8")
        declared = re.search(r"(?m)^license: (.+)$", skill).group(1)
        catalog.append({"name": name, "category": category, "title_zh": title, "purpose_zh": purpose,
                        "upstream_path": f"skills/{name}/SKILL.md", "vendor_path": f"vendor/scientific-agent-skills/skills/{name}",
                        "evidence_url": f"{REPOSITORY}/blob/{REVISION}/skills/{name}/SKILL.md",
                        "declared_license": declared, "dependency_notes": dependencies,
                        "execution_verified": False,
                        "verification_scope": "snapshot captured; runtime verification must be recorded after execution"})
    (root / "catalog.json").write_text(json.dumps({"schema_version": "1.0", "count": len(catalog), "skills": catalog}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lock = {"schema_version": "1.0", "repository": REPOSITORY, "revision": REVISION,
            "retrieved": "2026-10-09", "selection": names, "root_license": "MIT",
            "files": records, "additional_license_texts": licenses,
            "scope": "Selected full skill directories plus original LICENSE/CITATION. No upstream application, data, weights or all-package installation."}
    (root / "upstream-lock.json").write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {len(catalog)} skills, {len(records)} upstream files, {sum(x['bytes'] for x in records)} bytes")


if __name__ == "__main__":
    main()
