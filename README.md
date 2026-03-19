# 作业 1.1 — 三刺激值计算

色彩科学与应用课程作业：基于 PhotoResearch PR-788 光谱辐射度计的测量数据，计算 CIE 1931 XYZ 三刺激值、色品坐标及相关色温。

## 项目结构

```
.
├── README.md                       # 项目说明
├── tristimulus_calculation.py      # 主计算脚本（XYZ / xy / u'v' / CCT）
├── generate_report.py              # PDF + Markdown 报告生成脚本
├── data/                           # 输入数据
│   ├── PhotoResearch_Raw_Data.xlsx   # PR-788 原始测量数据（380-780nm, 1nm）
│   └── cie1931_cmf_1nm.csv               # CIE 1931 2° CMF（来自 CVRL）
├── refs/                           # 参考资料
│   ├── 色彩科学与应用-第1次作业要求.pdf
│   ├── PR-7XX-SpectraScan-User-Manual-1.pdf
│   └── PhotoResearch PR-788.pdf
└── output/                         # 输出结果（由脚本自动生成）
    ├── 作业1.1_三刺激值计算报告.pdf       # 最终 PDF 报告
    ├── 作业1.1_三刺激值计算报告.md        # Markdown 可编辑版本
    ├── 01_spd.png                         # 光谱功率分布图
    ├── 02_cie1931_xy.png                  # CIE 1931 xy 色品图
    ├── 03_cie1976_uv.png                  # CIE 1976 u'v' 色品图
    ├── intermediate_data.csv              # 中间计算数据
    └── results.json                       # 计算结果汇总
```

## 运行方式

```bash
# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas matplotlib openpyxl reportlab

# 1. 运行计算（生成 output/ 下的图表、CSV、JSON）
python3 tristimulus_calculation.py

# 2. 生成报告（生成 PDF 和 Markdown）
python3 generate_report.py
```

## 计算内容

| 项目 | 结果 |
|------|------|
| CIE 1931 XYZ | X = 822.9879, Y = 915.6386 cd/m², Z = 1145.2742 |
| CIE 1931 xy | x = 0.2854, y = 0.3175 |
| CIE 1976 u'v' | u' = 0.1830, v' = 0.4580 |
| CCT (Robertson) | 8425 K |

## 计算方法

- **三刺激值**: X/Y/Z = 683 × Σ S(λ) × CMF(λ) × Δλ，采用绝对三刺激值（Y 单位 cd/m²）
- **色品坐标**: x = X/(X+Y+Z), y = Y/(X+Y+Z); u' = 4X/(X+15Y+3Z), v' = 9Y/(X+15Y+3Z)
- **CCT**: Robertson (1968) 方法，CIE 1960 UCS 上普朗克轨迹插值；McCamy、Hernandez-Andres 交叉验证

## 参考文献

1. CIE 015:2018, Colorimetry, 4th Edition
2. McCamy, C.S. (1992). Color Res. Appl., 17(2), 142-144
3. Hernandez-Andres, J. et al. (1999). Appl. Opt., 38(27), 5703-5709
4. Robertson, A.R. (1968). J. Opt. Soc. Am., 58(11), 1528-1535
5. CVRL — http://cvrl.ioo.ucl.ac.uk/cmfs.htm
