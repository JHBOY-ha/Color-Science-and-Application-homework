#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成作业 1.1 PDF 报告
使用 reportlab 生成包含完整计算过程的 PDF 文档
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, black, grey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# 注册中文字体
import platform
if platform.system() == 'Darwin':
    font_paths = [
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
    ]
    font_registered = False
    for fp in font_paths:
        if Path(fp).exists():
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', fp))
                font_registered = True
                print(f"已注册字体: {fp}")
                break
            except Exception as e:
                continue

    if not font_registered:
        # 尝试用 reportlab 自带
        print("警告: 未找到合适中文字体，尝试使用系统字体")
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', '/System/Library/Fonts/STHeiti Medium.ttc'))
            font_registered = True
        except:
            pass

FONT_CN = 'ChineseFont' if font_registered else 'Helvetica'
FONT_EN = 'Helvetica'

# 读取计算结果
with open(OUTPUT_DIR / "results.json", "r", encoding="utf-8") as f:
    R = json.load(f)

# ============================================================
# 样式定义
# ============================================================
styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    'TitleCN', parent=styles['Title'],
    fontName=FONT_CN, fontSize=22, leading=30,
    spaceAfter=6*mm, alignment=TA_CENTER
)
style_subtitle = ParagraphStyle(
    'SubtitleCN', parent=styles['Normal'],
    fontName=FONT_CN, fontSize=11, leading=16,
    spaceAfter=4*mm, alignment=TA_CENTER, textColor=HexColor('#555555')
)
style_h1 = ParagraphStyle(
    'H1CN', parent=styles['Heading1'],
    fontName=FONT_CN, fontSize=16, leading=22,
    spaceBefore=8*mm, spaceAfter=4*mm, textColor=HexColor('#1a1a2e')
)
style_h2 = ParagraphStyle(
    'H2CN', parent=styles['Heading2'],
    fontName=FONT_CN, fontSize=13, leading=18,
    spaceBefore=5*mm, spaceAfter=3*mm, textColor=HexColor('#16213e')
)
style_body = ParagraphStyle(
    'BodyCN', parent=styles['Normal'],
    fontName=FONT_CN, fontSize=10, leading=16,
    spaceAfter=2*mm, alignment=TA_JUSTIFY
)
style_formula = ParagraphStyle(
    'Formula', parent=styles['Normal'],
    fontName=FONT_EN, fontSize=11, leading=18,
    spaceAfter=2*mm, alignment=TA_CENTER,
    leftIndent=20*mm, rightIndent=20*mm
)
style_code = ParagraphStyle(
    'Code', parent=styles['Normal'],
    fontName='Courier', fontSize=9, leading=13,
    spaceAfter=1*mm, leftIndent=10*mm,
    backColor=HexColor('#f5f5f5')
)
style_result = ParagraphStyle(
    'Result', parent=styles['Normal'],
    fontName=FONT_CN, fontSize=11, leading=17,
    spaceAfter=2*mm, leftIndent=10*mm,
    textColor=HexColor('#0a3d62'), borderColor=HexColor('#0a3d62'),
    borderWidth=0, borderPadding=3
)

# ============================================================
# 构建文档内容
# ============================================================
elements = []

# --- 标题页 ---
elements.append(Spacer(1, 30*mm))
elements.append(Paragraph("色彩科学与应用 — 作业 1.1", style_title))
elements.append(Paragraph("三刺激值计算报告", ParagraphStyle(
    'Title2', parent=style_title, fontSize=18, spaceAfter=10*mm)))
elements.append(Spacer(1, 10*mm))
elements.append(Paragraph(f"学号: {R['student_id']}　　姓名: {R['student_name']}", style_subtitle))
elements.append(Paragraph("测量设备: PhotoResearch PR-788 光谱辐射度计", style_subtitle))
elements.append(Paragraph("测量对象: 显示屏白场 (White Point)", style_subtitle))
elements.append(Spacer(1, 10*mm))

# 结果概览表
summary_data = [
    ['计算项目', '结果'],
    ['CIE 1931 XYZ', f'X = {R["X_abs"]:.4f},  Y = {R["Y_abs"]:.4f} cd/m²,  Z = {R["Z_abs"]:.4f}'],
    ['CIE 1931 xy', f'x = {R["x"]:.4f},  y = {R["y"]:.4f}'],
    ["CIE 1976 u'v'", f"u' = {R['u_prime']:.4f},  v' = {R['v_prime']:.4f}"],
    ['CCT (Robertson)', f'{R["CCT_robertson"]:.0f} K'],
]
summary_table = Table(summary_data, colWidths=[50*mm, 110*mm])
summary_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), FONT_CN),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(summary_table)

elements.append(PageBreak())

# ============================================================
# 第一部分：原始数据
# ============================================================
elements.append(Paragraph("一、原始测量数据", style_h1))

elements.append(Paragraph(
    "使用 PhotoResearch PR-788 光谱辐射度计对某显示屏白场进行测量，"
    "获得 380–780 nm 波长范围内的光谱功率分布 (SPD) 数据。PR-788 的波长分辨率为 1 nm，"
    "光谱带宽可选 2/5/8 nm，测量结果为光谱辐亮度 (spectral radiance)，单位为 W/sr/m²/nm。",
    style_body
))

# 读取SPD数据并显示部分
xlsx_path = SCRIPT_DIR / "副本PhotoResearch_Raw_Data.xlsx"
df_raw = pd.read_excel(xlsx_path, sheet_name="PhotoResearch_Raw_Data")
wavelengths = df_raw.columns[3:].astype(int).values
spd_values = np.array([float(v) for v in df_raw.iloc[0, 3:].values])

elements.append(Paragraph("原始数据概况:", style_h2))
info_data = [
    ['参数', '值'],
    ['波长范围', '380 – 780 nm'],
    ['波长间隔 (Δλ)', '1 nm'],
    ['数据点数', '401'],
    ['SPD 最大值', f'{spd_values.max():.4e} W/sr/m²/nm (λ ≈ {wavelengths[np.argmax(spd_values)]} nm)'],
    ['SPD 最小值', f'{spd_values.min():.4e} W/sr/m²/nm'],
]
info_table = Table(info_data, colWidths=[45*mm, 120*mm])
info_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
elements.append(info_table)
elements.append(Spacer(1, 4*mm))

# SPD 图
elements.append(Paragraph("光谱功率分布 (SPD) 图:", style_h2))
spd_img = Image(str(OUTPUT_DIR / "01_spd.png"), width=160*mm, height=80*mm)
elements.append(spd_img)
elements.append(Paragraph(
    "图 1: PR-788 测量的显示屏白场光谱功率分布。可见典型的 LED 背光 LCD 显示屏特征 — "
    "蓝光区 (~450 nm) 和红光区 (~630 nm) 各有一个显著峰值，绿光区 (~530 nm) 有一个宽峰。",
    ParagraphStyle('Caption', parent=style_body, fontSize=9, textColor=grey, alignment=TA_CENTER)
))

elements.append(PageBreak())

# ============================================================
# 第二部分：CIE 1931 XYZ 三刺激值
# ============================================================
elements.append(Paragraph("二、CIE 1931 XYZ 三刺激值计算", style_h1))

elements.append(Paragraph("2.1 颜色匹配函数 (CMFs)", style_h2))
elements.append(Paragraph(
    "CIE 1931 2° 标准观察者颜色匹配函数 x̄(λ)、ȳ(λ)、z̄(λ) 数据来源于 "
    "CVRL (Colour &amp; Vision Research Laboratory) 数据库 "
    "(http://cvrl.ioo.ucl.ac.uk/cmfs.htm)，采用 1 nm 间隔的离散数据。"
    "该数据与 CIE 015:2018 标准一致。",
    style_body
))

# CMF 部分数据表
cmf_data = np.loadtxt(SCRIPT_DIR / "cie1931_cmf_1nm.csv", delimiter=',')
mask = (cmf_data[:, 0] >= 380) & (cmf_data[:, 0] <= 780)
cmf_vis = cmf_data[mask]

cmf_table_data = [['λ (nm)', 'x̄(λ)', 'ȳ(λ)', 'z̄(λ)']]
for i in range(0, len(cmf_vis), 40):
    wl = int(cmf_vis[i, 0])
    cmf_table_data.append([
        str(wl),
        f'{cmf_vis[i, 1]:.6f}',
        f'{cmf_vis[i, 2]:.6f}',
        f'{cmf_vis[i, 3]:.6f}'
    ])
cmf_table = Table(cmf_table_data, colWidths=[25*mm, 40*mm, 40*mm, 40*mm])
cmf_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_EN),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
]))
elements.append(cmf_table)
elements.append(Paragraph(
    "表: CIE 1931 2° CMF 部分数据（每隔 40nm 采样显示，完整数据见附件 CSV）",
    ParagraphStyle('Caption', parent=style_body, fontSize=9, textColor=grey, alignment=TA_CENTER)
))
elements.append(Spacer(1, 3*mm))

elements.append(Paragraph("2.2 计算公式", style_h2))
elements.append(Paragraph(
    "对于自发光光源（如显示屏），三刺激值由光谱辐亮度 S(λ) 与颜色匹配函数的乘积在可见光"
    "波长范围内积分得到。采用离散求和近似（矩形法则）:",
    style_body
))
elements.append(Paragraph(
    "X = K<sub>m</sub> × Σ S(λ) × x̄(λ) × Δλ　　(λ = 380 → 780 nm)",
    style_formula
))
elements.append(Paragraph(
    "Y = K<sub>m</sub> × Σ S(λ) × ȳ(λ) × Δλ　　(λ = 380 → 780 nm)",
    style_formula
))
elements.append(Paragraph(
    "Z = K<sub>m</sub> × Σ S(λ) × z̄(λ) × Δλ　　(λ = 380 → 780 nm)",
    style_formula
))
elements.append(Paragraph(
    "其中 K<sub>m</sub> = 683 lm/W 为明视觉最大光谱光视效能常数，Δλ = 1 nm 为波长间隔。"
    "参考: PR-7XX User Manual, Chapter 3, p.32; CIE 015:2018。",
    style_body
))

elements.append(Paragraph("2.3 中间计算值", style_h2))

# 中间值表
mid_table_data = [['λ (nm)', 'S(λ) (W/sr/m²/nm)', 'S(λ)×x̄(λ)', 'S(λ)×ȳ(λ)', 'S(λ)×z̄(λ)']]
x_bar = cmf_vis[:, 1]
y_bar = cmf_vis[:, 2]
z_bar = cmf_vis[:, 3]
for i in range(0, len(cmf_vis), 40):
    wl = int(cmf_vis[i, 0])
    s = spd_values[i]
    mid_table_data.append([
        str(wl),
        f'{s:.4e}',
        f'{s*x_bar[i]:.4e}',
        f'{s*y_bar[i]:.4e}',
        f'{s*z_bar[i]:.4e}'
    ])
# 加求和行
sum_sx = np.sum(spd_values * x_bar)
sum_sy = np.sum(spd_values * y_bar)
sum_sz = np.sum(spd_values * z_bar)
mid_table_data.append(['Σ (合计)', '—', f'{sum_sx:.6e}', f'{sum_sy:.6e}', f'{sum_sz:.6e}'])

mid_table = Table(mid_table_data, colWidths=[22*mm, 38*mm, 32*mm, 32*mm, 32*mm])
mid_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_EN),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, -1), (-1, -1), HexColor('#dfe6e9')),
    ('FONTNAME', (0, -1), (-1, -1), FONT_EN),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 2),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
]))
elements.append(mid_table)
elements.append(Spacer(1, 3*mm))

elements.append(Paragraph("2.4 计算结果", style_h2))
elements.append(Paragraph(
    f"Σ S(λ)×x̄(λ)×Δλ = {sum_sx:.6e}<br/>"
    f"Σ S(λ)×ȳ(λ)×Δλ = {sum_sy:.6e}<br/>"
    f"Σ S(λ)×z̄(λ)×Δλ = {sum_sz:.6e}",
    style_code
))
elements.append(Spacer(1, 2*mm))
elements.append(Paragraph(
    f"<b>X</b> = 683 × {sum_sx:.6e} = <b>{R['X_abs']:.4f}</b><br/>"
    f"<b>Y</b> = 683 × {sum_sy:.6e} = <b>{R['Y_abs']:.4f}</b> cd/m²<br/>"
    f"<b>Z</b> = 683 × {sum_sz:.6e} = <b>{R['Z_abs']:.4f}</b>",
    style_result
))

elements.append(Paragraph("2.5 关于 Y 值标准化的讨论", style_h2))
elements.append(Paragraph(
    "<b>思路 A（本报告采用）: 绝对三刺激值</b><br/>"
    f"直接使用 K<sub>m</sub> = 683 lm/W。此时 Y 值即为绝对亮度 (luminance) = {R['Y_abs']:.4f} cd/m²，"
    "具有明确的物理意义——表示显示屏白场的亮度。这是 PR-788 等光谱辐射度计的标准做法，"
    "与仪器手册 (Chapter 3, p.32) 中给出的公式一致。",
    style_body
))
elements.append(Paragraph(
    "<b>思路 B: 相对三刺激值 (Y = 100)</b><br/>"
    f"将三刺激值归一化使 Y = 100。归一化系数 k = 100/{R['Y_abs']:.4f} = {100/R['Y_abs']:.6f}。"
    f"此时 X = {R['X_rel']:.4f}，Y = {R['Y_rel']:.4f}，Z = {R['Z_rel']:.4f}。"
    "此思路常用于反射/透射物体色的表达，其中 Y=100 表示完美漫反射体。"
    "对于自发光体，此标准化会丢失绝对亮度信息。",
    style_body
))
elements.append(Paragraph(
    "<b>思路 C: K = 1（无物理单位）</b><br/>"
    f"省略 K<sub>m</sub> 系数，直接对 S(λ)×CMF×Δλ 求和。此时三刺激值无特定物理单位，"
    "仅为相对量。虽然色品坐标 (x, y) 和 (u', v') 不受 K 值影响，但三刺激值本身缺乏物理意义。",
    style_body
))

elements.append(PageBreak())

# ============================================================
# 第三部分：CIE 1931 xy 色品坐标
# ============================================================
elements.append(Paragraph("三、CIE 1931 xy 色品坐标", style_h1))

elements.append(Paragraph("3.1 计算公式与过程", style_h2))
elements.append(Paragraph("x = X / (X + Y + Z)　　y = Y / (X + Y + Z)", style_formula))
elements.append(Paragraph(
    f"X + Y + Z = {R['X_abs']:.4f} + {R['Y_abs']:.4f} + {R['Z_abs']:.4f} "
    f"= {R['X_abs']+R['Y_abs']+R['Z_abs']:.4f}",
    style_code
))
sum_xyz = R['X_abs'] + R['Y_abs'] + R['Z_abs']
elements.append(Paragraph(
    f"<b>x</b> = {R['X_abs']:.4f} / {sum_xyz:.4f} = <b>{R['x']:.4f}</b><br/>"
    f"<b>y</b> = {R['Y_abs']:.4f} / {sum_xyz:.4f} = <b>{R['y']:.4f}</b>",
    style_result
))

elements.append(Paragraph("3.2 CIE 1931 xy 色品图", style_h2))
xy_img = Image(str(OUTPUT_DIR / "02_cie1931_xy.png"), width=140*mm, height=140*mm)
elements.append(xy_img)
elements.append(Paragraph(
    f"图 2: CIE 1931 xy 色品图。红色星号标注测量点 (x={R['x']:.4f}, y={R['y']:.4f})，"
    f"位于普朗克轨迹附近，对应约 {R['CCT_robertson']:.0f} K 色温的冷白色区域。",
    ParagraphStyle('Caption', parent=style_body, fontSize=9, textColor=grey, alignment=TA_CENTER)
))

elements.append(PageBreak())

# ============================================================
# 第四部分：CIE 1976 u'v' 色品坐标
# ============================================================
elements.append(Paragraph("四、CIE 1976 u'v' 色品坐标", style_h1))

elements.append(Paragraph("4.1 计算公式与过程", style_h2))
elements.append(Paragraph(
    "u' = 4X / (X + 15Y + 3Z)　　v' = 9Y / (X + 15Y + 3Z)",
    style_formula
))
denom_uv = R['X_abs'] + 15 * R['Y_abs'] + 3 * R['Z_abs']
elements.append(Paragraph(
    f"X + 15Y + 3Z = {R['X_abs']:.4f} + 15×{R['Y_abs']:.4f} + 3×{R['Z_abs']:.4f} "
    f"= {denom_uv:.4f}",
    style_code
))
elements.append(Paragraph(
    f"<b>u'</b> = 4×{R['X_abs']:.4f} / {denom_uv:.4f} = <b>{R['u_prime']:.4f}</b><br/>"
    f"<b>v'</b> = 9×{R['Y_abs']:.4f} / {denom_uv:.4f} = <b>{R['v_prime']:.4f}</b>",
    style_result
))
elements.append(Paragraph(
    "CIE 1976 u'v' 均匀色品空间 (UCS) 相对于 CIE 1931 xy 色品图具有更好的感知均匀性，"
    "即图上等距离对应更接近等视觉色差。",
    style_body
))

elements.append(Paragraph("4.2 CIE 1976 u'v' 色品图", style_h2))
uv_img = Image(str(OUTPUT_DIR / "03_cie1976_uv.png"), width=140*mm, height=140*mm)
elements.append(uv_img)
elements.append(Paragraph(
    f"图 3: CIE 1976 u'v' 色品图。红色星号标注测量点 "
    f"(u'={R['u_prime']:.4f}, v'={R['v_prime']:.4f})。",
    ParagraphStyle('Caption', parent=style_body, fontSize=9, textColor=grey, alignment=TA_CENTER)
))

elements.append(PageBreak())

# ============================================================
# 第五部分：相关色温 (CCT)
# ============================================================
elements.append(Paragraph("五、相关色温 (CCT) 计算", style_h1))

elements.append(Paragraph(
    "相关色温 (Correlated Color Temperature, CCT) 是指与被测光源色品坐标最接近的"
    "普朗克辐射体 (黑体) 温度，在 CIE 1960 UCS 色品图上，测量点到普朗克轨迹的最短距离"
    "对应的黑体温度即为 CCT。本报告采用三种算法进行计算和交叉验证。",
    style_body
))

elements.append(Paragraph("5.1 McCamy 近似公式 (1992)", style_h2))
elements.append(Paragraph(
    "参考文献: McCamy, C.S. (1992). <i>Correlated color temperature as an explicit function "
    "of chromaticity coordinates.</i> Color Res. Appl., 17(2), 142–144.",
    style_body
))
elements.append(Paragraph(
    "n = (x − 0.3320) / (y − 0.1858)<br/>"
    "CCT = −449n³ + 3525n² − 6823.3n + 5520.33",
    style_formula
))
n_val = (R['x'] - 0.3320) / (R['y'] - 0.1858)
elements.append(Paragraph(
    f"n = ({R['x']:.4f} − 0.3320) / ({R['y']:.4f} − 0.1858) = {n_val:.6f}<br/>"
    f"CCT = {R['CCT_mccamy']:.2f} K",
    style_code
))

elements.append(Paragraph("5.2 Hernandez-Andres 近似公式 (1999)", style_h2))
elements.append(Paragraph(
    "参考文献: Hernandez-Andres, J. et al. (1999). <i>Calculating correlated color temperatures "
    "across the entire gamut of daylight and skylight chromaticities.</i> Appl. Opt., 38(27), 5703–5709.",
    style_body
))
elements.append(Paragraph(
    "n = (x − x<sub>e</sub>) / (y − y<sub>e</sub>)，其中 x<sub>e</sub> = 0.3366, y<sub>e</sub> = 0.1735<br/>"
    "CCT = A₀ + A₁·exp(−n/t₁) + A₂·exp(−n/t₂) + A₃·exp(−n/t₃)",
    style_formula
))
elements.append(Paragraph(f"CCT = {R['CCT_hernandez']:.2f} K", style_code))

elements.append(Paragraph("5.3 Robertson 方法 (1968)（本报告采用）", style_h2))
elements.append(Paragraph(
    "参考文献: Robertson, A.R. (1968). <i>Computation of correlated color temperature and "
    "distribution temperature.</i> J. Opt. Soc. Am., 58(11), 1528–1535.",
    style_body
))
elements.append(Paragraph(
    "Robertson 方法在 CIE 1960 UCS (u, v) 色品图上，使用 31 个普朗克轨迹参考点的"
    "查找表和线性插值。该方法是 CIE 推荐的经典 CCT 计算方法，精度高、适用范围广。",
    style_body
))
u_1960 = R['u_prime']  # u' = u in CIE 1960
v_1960 = 2/3 * R['v_prime']  # v = 2/3 * v'
elements.append(Paragraph(
    f"CIE 1960 UCS 坐标: u = {u_1960:.6f},  v = {v_1960:.6f}<br/>"
    f"(其中 u = u' = 4X/(X+15Y+3Z),  v = (2/3)v' = 6Y/(X+15Y+3Z))",
    style_code
))
elements.append(Paragraph(
    f"通过在普朗克轨迹参考点之间线性插值，得到 MRD (micro reciprocal degree) 值，"
    f"再由 CCT = 10⁶ / MRD 转换为色温。",
    style_body
))

elements.append(Spacer(1, 3*mm))
elements.append(Paragraph("5.4 CCT 计算结果汇总", style_h2))
cct_data = [
    ['算法', 'CCT (K)', '适用范围', '备注'],
    ['McCamy (1992)', f'{R["CCT_mccamy"]:.0f}', '2000–12500 K', '三次多项式近似'],
    ['Hernandez-Andres (1999)', f'{R["CCT_hernandez"]:.0f}', '3000–50000 K', '指数函数近似'],
    ['Robertson (1968)', f'{R["CCT_robertson"]:.0f}', '1000–∞ K', 'CIE 推荐，查找表插值'],
]
cct_table = Table(cct_data, colWidths=[48*mm, 25*mm, 35*mm, 50*mm])
cct_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 3), (-1, 3), HexColor('#e8f5e9')),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
elements.append(cct_table)
elements.append(Paragraph(
    f"三种方法结果高度一致 (偏差 < 30 K)，最终采用 Robertson 方法: <b>CCT = {R['CCT_robertson']:.0f} K</b>。"
    f"此色温约 {R['CCT_robertson']:.0f} K 属于冷白色，略偏蓝，高于标准 D65 光源的 6504 K。",
    style_body
))

elements.append(PageBreak())

# ============================================================
# 第六部分：参考文献
# ============================================================
elements.append(Paragraph("六、参考文献", style_h1))
refs = [
    "[1] CIE 015:2018, Colorimetry, 4th Edition. Commission Internationale de l'Éclairage.",
    "[2] McCamy, C.S. (1992). Correlated color temperature as an explicit function of "
    "chromaticity coordinates. Color Research &amp; Application, 17(2), 142–144.",
    "[3] Hernandez-Andres, J., Lee, R.L., Romero, J. (1999). Calculating correlated color "
    "temperatures across the entire gamut of daylight and skylight chromaticities. "
    "Applied Optics, 38(27), 5703–5709.",
    "[4] Robertson, A.R. (1968). Computation of correlated color temperature and distribution "
    "temperature. Journal of the Optical Society of America, 58(11), 1528–1535.",
    "[5] CVRL - Colour &amp; Vision Research Laboratory. CIE 1931 2° CMFs. http://cvrl.ioo.ucl.ac.uk/cmfs.htm",
    "[6] PhotoResearch PR-7XX SpectraScan User's Manual. Novanta/JADAK, 2019.",
    "[7] Lindbloom, B. Useful Color Equations. http://www.brucelindbloom.com/",
]
for ref in refs:
    elements.append(Paragraph(ref, ParagraphStyle(
        'Ref', parent=style_body, fontSize=9, leading=14, leftIndent=10*mm,
        firstLineIndent=-10*mm
    )))

# ============================================================
# 构建 PDF
# ============================================================
pdf_path = OUTPUT_DIR / "作业1.1_三刺激值计算报告.pdf"
doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=20*mm, bottomMargin=20*mm
)
doc.build(elements)
print(f"\n✓ PDF 报告已生成: {pdf_path}")
