#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成作业 1.1 PDF 报告 + Markdown 可编辑版本
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, grey
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"

# 注册中文字体 — 优先 PingFang (Unicode 覆盖更好)
import platform
font_registered = False
if platform.system() == 'Darwin':
    font_candidates = [
        ('/System/Library/Fonts/PingFang.ttc', 0),
        ('/System/Library/Fonts/STHeiti Light.ttc', None),
        ('/System/Library/Fonts/Supplemental/Songti.ttc', None),
        ('/Library/Fonts/Arial Unicode.ttf', None),
    ]
    for fp, subfont in font_candidates:
        if Path(fp).exists():
            try:
                if subfont is not None:
                    pdfmetrics.registerFont(TTFont('ChineseFont', fp, subfontIndex=subfont))
                else:
                    pdfmetrics.registerFont(TTFont('ChineseFont', fp))
                font_registered = True
                print(f"已注册字体: {fp} (subfont={subfont})")
                break
            except Exception:
                continue

FONT_CN = 'ChineseFont' if font_registered else 'Helvetica'
FONT_EN = 'Helvetica'

# ============================================================
# PDF 安全文本: 将 combining macron 替换为 ASCII 安全表示
# ============================================================
# x̄ = x + U+0304  →  用 "x_bar" 替代
# 在 PDF 中统一使用 xbar / ybar / zbar 表示颜色匹配函数
def pdf_safe(text):
    """将含有 combining macron 的文本转为 PDF 安全文本"""
    # 替换 combining macron (U+0304) 的情况
    text = text.replace('x\u0304', 'xbar')
    text = text.replace('y\u0304', 'ybar')
    text = text.replace('z\u0304', 'zbar')
    text = text.replace('\u0304', 'bar')  # 兜底
    return text


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
    textColor=HexColor('#0a3d62')
)
style_caption = ParagraphStyle(
    'Caption', parent=styles['Normal'],
    fontName=FONT_CN, fontSize=9, textColor=grey, alignment=TA_CENTER
)

# ============================================================
# 读取数据
# ============================================================
xlsx_path = SCRIPT_DIR / "data" / "PhotoResearch_Raw_Data.xlsx"
df_raw = pd.read_excel(xlsx_path, sheet_name="PhotoResearch_Raw_Data")
wavelengths = df_raw.columns[3:].astype(int).values
spd_values = np.array([float(v) for v in df_raw.iloc[0, 3:].values])

cmf_data = np.loadtxt(SCRIPT_DIR / "data" / "cie1931_cmf_1nm.csv", delimiter=',')
mask = (cmf_data[:, 0] >= 380) & (cmf_data[:, 0] <= 780)
cmf_vis = cmf_data[mask]
x_bar = cmf_vis[:, 1]
y_bar = cmf_vis[:, 2]
z_bar = cmf_vis[:, 3]
sum_sx = np.sum(spd_values * x_bar)
sum_sy = np.sum(spd_values * y_bar)
sum_sz = np.sum(spd_values * z_bar)
sum_xyz = R['X_abs'] + R['Y_abs'] + R['Z_abs']
denom_uv = R['X_abs'] + 15 * R['Y_abs'] + 3 * R['Z_abs']
n_val = (R['x'] - 0.3320) / (R['y'] - 0.1858)
u_1960 = R['u_prime']
v_1960 = 2/3 * R['v_prime']

# ============================================================
# 通用表格样式
# ============================================================
def header_table_style():
    return TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ])

# ============================================================
# 构建 PDF 文档
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

summary_data = [
    ['计算项目', '结果'],
    ['CIE 1931 XYZ', f'X = {R["X_abs"]:.4f},  Y = {R["Y_abs"]:.4f} cd/m\u00b2,  Z = {R["Z_abs"]:.4f}'],
    ['CIE 1931 xy', f'x = {R["x"]:.4f},  y = {R["y"]:.4f}'],
    ["CIE 1976 u'v'", f"u' = {R['u_prime']:.4f},  v' = {R['v_prime']:.4f}"],
    ['CCT (Robertson)', f'{R["CCT_robertson"]:.0f} K'],
]
t = Table(summary_data, colWidths=[50*mm, 110*mm])
t.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_CN), ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f8f9fa')),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(t)
elements.append(PageBreak())

# ===== 一、原始测量数据 =====
elements.append(Paragraph("一、原始测量数据", style_h1))
elements.append(Paragraph(
    "使用 PhotoResearch PR-788 光谱辐射度计对某显示屏白场进行测量，"
    "获得 380-780 nm 波长范围内的光谱功率分布 (SPD) 数据。PR-788 的波长分辨率为 1 nm，"
    "光谱带宽可选 2/5/8 nm，测量结果为光谱辐亮度 (spectral radiance)，单位为 W/sr/m\u00b2/nm。",
    style_body))

elements.append(Paragraph("原始数据概况:", style_h2))
info = Table([
    ['参数', '值'],
    ['波长范围', '380 - 780 nm'],
    ['波长间隔', '1 nm'],
    ['数据点数', '401'],
    ['SPD 最大值', f'{spd_values.max():.4e} W/sr/m\u00b2/nm (at {wavelengths[np.argmax(spd_values)]} nm)'],
    ['SPD 最小值', f'{spd_values.min():.4e} W/sr/m\u00b2/nm'],
], colWidths=[45*mm, 120*mm])
info.setStyle(header_table_style())
elements.append(info)
elements.append(Spacer(1, 4*mm))

elements.append(Paragraph("光谱功率分布 (SPD) 图:", style_h2))
elements.append(Image(str(OUTPUT_DIR / "01_spd.png"), width=160*mm, height=80*mm))
elements.append(Paragraph(
    "图 1: PR-788 测量的显示屏白场光谱功率分布。可见典型 LED 背光 LCD 特征: "
    "蓝光区 (~450 nm) 和红光区 (~630 nm) 各有显著峰值，绿光区 (~530 nm) 有宽峰。",
    style_caption))
elements.append(PageBreak())

# ===== 二、XYZ 三刺激值 =====
elements.append(Paragraph("二、CIE 1931 XYZ 三刺激值计算", style_h1))

elements.append(Paragraph("2.1 颜色匹配函数 (CMFs)", style_h2))
elements.append(Paragraph(
    "CIE 1931 2\u00b0 标准观察者颜色匹配函数 xbar, ybar, zbar 数据来源于 "
    "CVRL (Colour &amp; Vision Research Laboratory) 数据库 "
    "(http://cvrl.ioo.ucl.ac.uk/cmfs.htm)，采用 1 nm 间隔的离散数据，"
    "与 CIE 015:2018 标准一致。（注: xbar 即文献中的 x 上加横线符号，下同）",
    style_body))

# CMF 表 — 使用 ASCII 安全的表头
cmf_hdr = ['wavelength (nm)', 'xbar(lambda)', 'ybar(lambda)', 'zbar(lambda)']
cmf_rows = [cmf_hdr]
for i in range(0, len(cmf_vis), 40):
    cmf_rows.append([
        str(int(cmf_vis[i, 0])),
        f'{cmf_vis[i, 1]:.6f}', f'{cmf_vis[i, 2]:.6f}', f'{cmf_vis[i, 3]:.6f}'
    ])
ct = Table(cmf_rows, colWidths=[30*mm, 38*mm, 38*mm, 38*mm])
ct.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_EN), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
]))
elements.append(ct)
elements.append(Paragraph(
    "表: CIE 1931 2\u00b0 CMF 部分数据 (每隔 40nm 采样，完整数据见附件 CSV)", style_caption))
elements.append(Spacer(1, 3*mm))

elements.append(Paragraph("2.2 计算公式", style_h2))
elements.append(Paragraph(
    "对于自发光光源 (如显示屏)，三刺激值由光谱辐亮度 S(lambda) 与颜色匹配函数的乘积"
    "在可见光波长范围内积分得到。采用离散求和近似 (矩形法则):",
    style_body))
elements.append(Paragraph("X = Km * Sum[ S(lambda) * xbar(lambda) * d_lambda ]  (380-780 nm)", style_formula))
elements.append(Paragraph("Y = Km * Sum[ S(lambda) * ybar(lambda) * d_lambda ]  (380-780 nm)", style_formula))
elements.append(Paragraph("Z = Km * Sum[ S(lambda) * zbar(lambda) * d_lambda ]  (380-780 nm)", style_formula))
elements.append(Paragraph(
    "其中 Km = 683 lm/W 为明视觉最大光谱光视效能常数，d_lambda = 1 nm 为波长间隔。"
    "参考: PR-7XX User Manual, Chapter 3, p.32; CIE 015:2018。",
    style_body))

elements.append(Paragraph("2.3 中间计算值", style_h2))
mid_hdr = ['lambda (nm)', 'S(lambda)', 'S*xbar', 'S*ybar', 'S*zbar']
mid_rows = [mid_hdr]
for i in range(0, len(cmf_vis), 40):
    s = spd_values[i]
    mid_rows.append([
        str(int(cmf_vis[i, 0])), f'{s:.4e}',
        f'{s*x_bar[i]:.4e}', f'{s*y_bar[i]:.4e}', f'{s*z_bar[i]:.4e}'
    ])
mid_rows.append(['Sum', '-', f'{sum_sx:.6e}', f'{sum_sy:.6e}', f'{sum_sz:.6e}'])
mt = Table(mid_rows, colWidths=[24*mm, 36*mm, 32*mm, 32*mm, 32*mm])
mt.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_EN), ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, -1), (-1, -1), HexColor('#dfe6e9')),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
]))
elements.append(mt)
elements.append(Spacer(1, 3*mm))

elements.append(Paragraph("2.4 计算结果", style_h2))
elements.append(Paragraph(
    f"Sum S*xbar*d_lambda = {sum_sx:.6e}<br/>"
    f"Sum S*ybar*d_lambda = {sum_sy:.6e}<br/>"
    f"Sum S*zbar*d_lambda = {sum_sz:.6e}",
    style_code))
elements.append(Spacer(1, 2*mm))
elements.append(Paragraph(
    f"<b>X</b> = 683 x {sum_sx:.6e} = <b>{R['X_abs']:.4f}</b><br/>"
    f"<b>Y</b> = 683 x {sum_sy:.6e} = <b>{R['Y_abs']:.4f}</b> cd/m\u00b2<br/>"
    f"<b>Z</b> = 683 x {sum_sz:.6e} = <b>{R['Z_abs']:.4f}</b>",
    style_result))

elements.append(Paragraph("2.5 关于 Y 值标准化的讨论", style_h2))
elements.append(Paragraph(
    "<b>思路 A (本报告采用): 绝对三刺激值</b><br/>"
    f"直接使用 Km = 683 lm/W，此时 Y 即为绝对亮度 (luminance) = {R['Y_abs']:.4f} cd/m\u00b2，"
    "具有明确物理意义。这是 PR-788 等光谱辐射度计的标准做法，"
    "与仪器手册 (Chapter 3, p.32) 中给出的公式一致。",
    style_body))
elements.append(Paragraph(
    "<b>思路 B: 相对三刺激值 (Y = 100)</b><br/>"
    f"将三刺激值归一化使 Y = 100。归一化系数 k = 100/{R['Y_abs']:.4f} = {100/R['Y_abs']:.6f}。"
    f"此时 X = {R['X_rel']:.4f}, Y = {R['Y_rel']:.4f}, Z = {R['Z_rel']:.4f}。"
    "此思路常用于反射/透射物体色，其中 Y=100 表示完美漫反射体。"
    "对于自发光体，此标准化会丢失绝对亮度信息。",
    style_body))
elements.append(Paragraph(
    "<b>思路 C: K = 1 (无物理单位)</b><br/>"
    "省略 Km 系数，直接对 S*CMF*d_lambda 求和。此时三刺激值无特定物理单位，仅为相对量。"
    "虽然色品坐标 (x, y) 和 (u', v') 不受 K 值影响，但三刺激值本身缺乏物理意义。",
    style_body))
elements.append(PageBreak())

# ===== 三、xy 色品坐标 =====
elements.append(Paragraph("三、CIE 1931 xy 色品坐标", style_h1))
elements.append(Paragraph("3.1 计算公式与过程", style_h2))
elements.append(Paragraph("x = X / (X + Y + Z)        y = Y / (X + Y + Z)", style_formula))
elements.append(Paragraph(
    f"X + Y + Z = {R['X_abs']:.4f} + {R['Y_abs']:.4f} + {R['Z_abs']:.4f} = {sum_xyz:.4f}",
    style_code))
elements.append(Paragraph(
    f"<b>x</b> = {R['X_abs']:.4f} / {sum_xyz:.4f} = <b>{R['x']:.4f}</b><br/>"
    f"<b>y</b> = {R['Y_abs']:.4f} / {sum_xyz:.4f} = <b>{R['y']:.4f}</b>",
    style_result))

elements.append(Paragraph("3.2 CIE 1931 xy 色品图", style_h2))
elements.append(Image(str(OUTPUT_DIR / "02_cie1931_xy.png"), width=140*mm, height=140*mm))
elements.append(Paragraph(
    f"图 2: CIE 1931 xy 色品图。红色星号标注测量点 (x={R['x']:.4f}, y={R['y']:.4f})，"
    f"位于普朗克轨迹附近，对应约 {R['CCT_robertson']:.0f} K 色温的冷白色区域。",
    style_caption))
elements.append(PageBreak())

# ===== 四、u'v' 色品坐标 =====
elements.append(Paragraph("四、CIE 1976 u'v' 色品坐标", style_h1))
elements.append(Paragraph("4.1 计算公式与过程", style_h2))
elements.append(Paragraph("u' = 4X / (X + 15Y + 3Z)        v' = 9Y / (X + 15Y + 3Z)", style_formula))
elements.append(Paragraph(
    f"X + 15Y + 3Z = {R['X_abs']:.4f} + 15*{R['Y_abs']:.4f} + 3*{R['Z_abs']:.4f} = {denom_uv:.4f}",
    style_code))
elements.append(Paragraph(
    f"<b>u'</b> = 4*{R['X_abs']:.4f} / {denom_uv:.4f} = <b>{R['u_prime']:.4f}</b><br/>"
    f"<b>v'</b> = 9*{R['Y_abs']:.4f} / {denom_uv:.4f} = <b>{R['v_prime']:.4f}</b>",
    style_result))
elements.append(Paragraph(
    "CIE 1976 u'v' 均匀色品空间 (UCS) 相对于 CIE 1931 xy 色品图具有更好的感知均匀性，"
    "即图上等距离更接近等视觉色差。", style_body))

elements.append(Paragraph("4.2 CIE 1976 u'v' 色品图", style_h2))
elements.append(Image(str(OUTPUT_DIR / "03_cie1976_uv.png"), width=140*mm, height=140*mm))
elements.append(Paragraph(
    f"图 3: CIE 1976 u'v' 色品图。红色星号标注测量点 "
    f"(u'={R['u_prime']:.4f}, v'={R['v_prime']:.4f})。",
    style_caption))
elements.append(PageBreak())

# ===== 五、CCT =====
elements.append(Paragraph("五、相关色温 (CCT) 计算", style_h1))
elements.append(Paragraph(
    "相关色温 (Correlated Color Temperature, CCT) 是指与被测光源色品坐标最接近的"
    "普朗克辐射体 (黑体) 温度，在 CIE 1960 UCS 色品图上测量点到普朗克轨迹的最短距离"
    "对应的黑体温度即为 CCT。本报告采用三种算法进行计算和交叉验证。",
    style_body))

elements.append(Paragraph("5.1 McCamy 近似公式 (1992)", style_h2))
elements.append(Paragraph(
    "参考: McCamy, C.S. (1992). <i>Correlated color temperature as an explicit function "
    "of chromaticity coordinates.</i> Color Res. Appl., 17(2), 142-144.",
    style_body))
elements.append(Paragraph(
    "n = (x - 0.3320) / (y - 0.1858)<br/>"
    "CCT = -449n^3 + 3525n^2 - 6823.3n + 5520.33", style_formula))
elements.append(Paragraph(
    f"n = ({R['x']:.4f} - 0.3320) / ({R['y']:.4f} - 0.1858) = {n_val:.6f}<br/>"
    f"CCT = {R['CCT_mccamy']:.2f} K", style_code))

elements.append(Paragraph("5.2 Hernandez-Andres 近似公式 (1999)", style_h2))
elements.append(Paragraph(
    "参考: Hernandez-Andres, J. et al. (1999). <i>Calculating correlated color temperatures "
    "across the entire gamut of daylight and skylight chromaticities.</i> Appl. Opt., 38(27), 5703-5709.",
    style_body))
elements.append(Paragraph(
    "n = (x - xe) / (y - ye),  xe = 0.3366, ye = 0.1735<br/>"
    "CCT = A0 + A1*exp(-n/t1) + A2*exp(-n/t2) + A3*exp(-n/t3)", style_formula))
elements.append(Paragraph(f"CCT = {R['CCT_hernandez']:.2f} K", style_code))

elements.append(Paragraph("5.3 Robertson 方法 (1968) (本报告采用)", style_h2))
elements.append(Paragraph(
    "参考: Robertson, A.R. (1968). <i>Computation of correlated color temperature and "
    "distribution temperature.</i> J. Opt. Soc. Am., 58(11), 1528-1535.",
    style_body))
elements.append(Paragraph(
    "Robertson 方法在 CIE 1960 UCS (u, v) 色品图上，使用 31 个普朗克轨迹参考点的"
    "查找表和线性插值。该方法是 CIE 推荐的经典 CCT 计算方法，精度高、适用范围广。",
    style_body))
elements.append(Paragraph(
    f"CIE 1960 UCS: u = {u_1960:.6f},  v = {v_1960:.6f}<br/>"
    f"(u = u' = 4X/(X+15Y+3Z),  v = (2/3)v' = 6Y/(X+15Y+3Z))", style_code))
elements.append(Paragraph(
    "通过在普朗克轨迹参考点之间线性插值得到 MRD (micro reciprocal degree) 值，"
    "再由 CCT = 10^6 / MRD 转换为色温。", style_body))

elements.append(Spacer(1, 3*mm))
elements.append(Paragraph("5.4 CCT 计算结果汇总", style_h2))
cct = Table([
    ['算法', 'CCT (K)', '适用范围', '备注'],
    ['McCamy (1992)', f'{R["CCT_mccamy"]:.0f}', '2000-12500 K', '三次多项式近似'],
    ['Hernandez-Andres (1999)', f'{R["CCT_hernandez"]:.0f}', '3000-50000 K', '指数函数近似'],
    ['Robertson (1968)', f'{R["CCT_robertson"]:.0f}', '1000-inf K', 'CIE 推荐，查找表插值'],
], colWidths=[48*mm, 25*mm, 35*mm, 50*mm])
cct.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), FONT_CN), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2d3436')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 3), (-1, 3), HexColor('#e8f5e9')),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dfe6e9')),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
elements.append(cct)
elements.append(Paragraph(
    f"三种方法结果高度一致 (偏差 &lt; 30 K)，最终采用 Robertson 方法: "
    f"<b>CCT = {R['CCT_robertson']:.0f} K</b>。"
    f"此色温约 {R['CCT_robertson']:.0f} K 属于冷白色，略偏蓝，高于标准 D65 光源的 6504 K。",
    style_body))
elements.append(PageBreak())

# ===== 六、参考文献 =====
elements.append(Paragraph("六、参考文献", style_h1))
refs = [
    "[1] CIE 015:2018, Colorimetry, 4th Edition.",
    "[2] McCamy, C.S. (1992). Correlated color temperature as an explicit function of "
    "chromaticity coordinates. Color Research &amp; Application, 17(2), 142-144.",
    "[3] Hernandez-Andres, J., Lee, R.L., Romero, J. (1999). Calculating correlated color "
    "temperatures across the entire gamut. Applied Optics, 38(27), 5703-5709.",
    "[4] Robertson, A.R. (1968). Computation of correlated color temperature. "
    "J. Opt. Soc. Am., 58(11), 1528-1535.",
    "[5] CVRL. CIE 1931 2-deg CMFs. http://cvrl.ioo.ucl.ac.uk/cmfs.htm",
    "[6] PhotoResearch PR-7XX SpectraScan User's Manual. Novanta/JADAK, 2019.",
    "[7] Lindbloom, B. Useful Color Equations. http://www.brucelindbloom.com/",
]
ref_style = ParagraphStyle('Ref', parent=style_body, fontSize=9, leading=14,
                           leftIndent=10*mm, firstLineIndent=-10*mm)
for ref in refs:
    elements.append(Paragraph(ref, ref_style))

# ===== 构建 PDF =====
pdf_path = OUTPUT_DIR / "作业1.1_三刺激值计算报告.pdf"
doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                        leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=20*mm, bottomMargin=20*mm)
doc.build(elements)
print(f"PDF 已生成: {pdf_path}")

# ============================================================
# 生成 Markdown 可编辑版本
# ============================================================
md_path = OUTPUT_DIR / "作业1.1_三刺激值计算报告.md"
md = f"""# 色彩科学与应用 — 作业 1.1  三刺激值计算报告

- **学号**: {R['student_id']}
- **姓名**: {R['student_name']}
- **测量设备**: PhotoResearch PR-788 光谱辐射度计
- **测量对象**: 显示屏白场 (White Point)

---

## 结果概览

| 计算项目 | 结果 |
|---------|------|
| CIE 1931 XYZ | X = {R['X_abs']:.4f},  Y = {R['Y_abs']:.4f} cd/m²,  Z = {R['Z_abs']:.4f} |
| CIE 1931 xy | x = {R['x']:.4f},  y = {R['y']:.4f} |
| CIE 1976 u'v' | u' = {R['u_prime']:.4f},  v' = {R['v_prime']:.4f} |
| CCT (Robertson) | {R['CCT_robertson']:.0f} K |

---

## 一、原始测量数据

使用 PhotoResearch PR-788 光谱辐射度计对某显示屏白场进行测量，获得 380–780 nm 波长范围内的光谱功率分布 (SPD) 数据。PR-788 的波长分辨率为 1 nm，光谱带宽可选 2/5/8 nm，测量结果为光谱辐亮度 (spectral radiance)，单位为 W/sr/m²/nm。

| 参数 | 值 |
|------|-----|
| 波长范围 | 380 – 780 nm |
| 波长间隔 (Δλ) | 1 nm |
| 数据点数 | 401 |
| SPD 最大值 | {spd_values.max():.4e} W/sr/m²/nm (λ ≈ {wavelengths[np.argmax(spd_values)]} nm) |
| SPD 最小值 | {spd_values.min():.4e} W/sr/m²/nm |

![SPD](01_spd.png)

*图 1: PR-788 测量的显示屏白场光谱功率分布。可见典型 LED 背光 LCD 特征——蓝光区 (~450 nm) 和红光区 (~630 nm) 各有显著峰值，绿光区 (~530 nm) 有宽峰。*

---

## 二、CIE 1931 XYZ 三刺激值计算

### 2.1 颜色匹配函数 (CMFs)

CIE 1931 2° 标准观察者颜色匹配函数 x̄(λ)、ȳ(λ)、z̄(λ) 数据来源于 CVRL (Colour & Vision Research Laboratory) 数据库 (http://cvrl.ioo.ucl.ac.uk/cmfs.htm)，采用 1 nm 间隔的离散数据，与 CIE 015:2018 标准一致。

### 2.2 计算公式

对于自发光光源（如显示屏），三刺激值计算公式为（离散求和形式）：

$$X = K_m \\times \\sum_{{\\lambda=380}}^{{780}} S(\\lambda) \\cdot \\bar{{x}}(\\lambda) \\cdot \\Delta\\lambda$$

$$Y = K_m \\times \\sum_{{\\lambda=380}}^{{780}} S(\\lambda) \\cdot \\bar{{y}}(\\lambda) \\cdot \\Delta\\lambda$$

$$Z = K_m \\times \\sum_{{\\lambda=380}}^{{780}} S(\\lambda) \\cdot \\bar{{z}}(\\lambda) \\cdot \\Delta\\lambda$$

其中：
- $S(\\lambda)$ = 光谱辐亮度 (W/sr/m²/nm)，由 PR-788 测量
- $\\bar{{x}}(\\lambda), \\bar{{y}}(\\lambda), \\bar{{z}}(\\lambda)$ = CIE 1931 2° 标准观察者颜色匹配函数
- $\\Delta\\lambda = 1$ nm（波长间隔）
- $K_m = 683$ lm/W（明视觉最大光谱光视效能）
- 参考: PR-7XX User Manual, Chapter 3, p.32; CIE 015:2018

### 2.3 中间计算值

| λ (nm) | S(λ) (W/sr/m²/nm) | S(λ)×x̄(λ) | S(λ)×ȳ(λ) | S(λ)×z̄(λ) |
|-------:|-------------------:|------------:|------------:|------------:|
"""

for i in range(0, len(cmf_vis), 40):
    s = spd_values[i]
    md += f"| {int(cmf_vis[i,0])} | {s:.4e} | {s*x_bar[i]:.4e} | {s*y_bar[i]:.4e} | {s*z_bar[i]:.4e} |\n"
md += f"| **Sum** | — | **{sum_sx:.6e}** | **{sum_sy:.6e}** | **{sum_sz:.6e}** |\n"

md += f"""
### 2.4 计算结果

```
Σ S(λ)×x̄(λ)×Δλ = {sum_sx:.6e}
Σ S(λ)×ȳ(λ)×Δλ = {sum_sy:.6e}
Σ S(λ)×z̄(λ)×Δλ = {sum_sz:.6e}
```

- **X** = 683 × {sum_sx:.6e} = **{R['X_abs']:.4f}**
- **Y** = 683 × {sum_sy:.6e} = **{R['Y_abs']:.4f}** cd/m²
- **Z** = 683 × {sum_sz:.6e} = **{R['Z_abs']:.4f}**

### 2.5 关于 Y 值标准化的讨论

**思路 A（本报告采用）：绝对三刺激值**
直接使用 Km = 683 lm/W，此时 Y 即为绝对亮度 (luminance) = {R['Y_abs']:.4f} cd/m²，具有明确物理意义。这是 PR-788 等光谱辐射度计的标准做法，与仪器手册 (Chapter 3, p.32) 中给出的公式一致。

**思路 B：相对三刺激值 (Y = 100)**
将三刺激值归一化使 Y = 100。归一化系数 k = 100/{R['Y_abs']:.4f} = {100/R['Y_abs']:.6f}。此时 X = {R['X_rel']:.4f}，Y = {R['Y_rel']:.4f}，Z = {R['Z_rel']:.4f}。此思路常用于反射/透射物体色的表达，其中 Y=100 表示完美漫反射体。对于自发光体，此标准化会丢失绝对亮度信息。

**思路 C：K = 1（无物理单位）**
省略 Km 系数，直接对 S(λ)×CMF×Δλ 求和。此时三刺激值无特定物理单位，仅为相对量。虽然色品坐标 (x, y) 和 (u', v') 不受 K 值影响，但三刺激值本身缺乏物理意义。

---

## 三、CIE 1931 xy 色品坐标

### 3.1 计算公式与过程

$$x = \\frac{{X}}{{X+Y+Z}}, \\quad y = \\frac{{Y}}{{X+Y+Z}}$$

```
X + Y + Z = {R['X_abs']:.4f} + {R['Y_abs']:.4f} + {R['Z_abs']:.4f} = {sum_xyz:.4f}
x = {R['X_abs']:.4f} / {sum_xyz:.4f} = {R['x']:.4f}
y = {R['Y_abs']:.4f} / {sum_xyz:.4f} = {R['y']:.4f}
```

**结果: x = {R['x']:.4f},  y = {R['y']:.4f}**

### 3.2 CIE 1931 xy 色品图

![CIE 1931 xy](02_cie1931_xy.png)

*图 2: CIE 1931 xy 色品图。红色星号标注测量点 (x={R['x']:.4f}, y={R['y']:.4f})，位于普朗克轨迹附近，对应约 {R['CCT_robertson']:.0f} K 色温的冷白色区域。*

---

## 四、CIE 1976 u'v' 色品坐标

### 4.1 计算公式与过程

$$u' = \\frac{{4X}}{{X+15Y+3Z}}, \\quad v' = \\frac{{9Y}}{{X+15Y+3Z}}$$

```
X + 15Y + 3Z = {R['X_abs']:.4f} + 15×{R['Y_abs']:.4f} + 3×{R['Z_abs']:.4f} = {denom_uv:.4f}
u' = 4×{R['X_abs']:.4f} / {denom_uv:.4f} = {R['u_prime']:.4f}
v' = 9×{R['Y_abs']:.4f} / {denom_uv:.4f} = {R['v_prime']:.4f}
```

**结果: u' = {R['u_prime']:.4f},  v' = {R['v_prime']:.4f}**

CIE 1976 u'v' 均匀色品空间 (UCS) 相对于 CIE 1931 xy 色品图具有更好的感知均匀性。

### 4.2 CIE 1976 u'v' 色品图

![CIE 1976 u'v'](03_cie1976_uv.png)

*图 3: CIE 1976 u'v' 色品图。红色星号标注测量点 (u'={R['u_prime']:.4f}, v'={R['v_prime']:.4f})。*

---

## 五、相关色温 (CCT) 计算

相关色温 (Correlated Color Temperature, CCT) 是指与被测光源色品坐标最接近的普朗克辐射体 (黑体) 温度。本报告采用三种算法进行计算和交叉验证。

### 5.1 McCamy 近似公式 (1992)

> McCamy, C.S. (1992). *Correlated color temperature as an explicit function of chromaticity coordinates.* Color Res. Appl., 17(2), 142–144.

$$n = \\frac{{x - 0.3320}}{{y - 0.1858}}, \\quad CCT = -449n^3 + 3525n^2 - 6823.3n + 5520.33$$

```
n = ({R['x']:.4f} - 0.3320) / ({R['y']:.4f} - 0.1858) = {n_val:.6f}
CCT = {R['CCT_mccamy']:.2f} K
```

### 5.2 Hernandez-Andres 近似公式 (1999)

> Hernandez-Andres, J. et al. (1999). *Calculating correlated color temperatures across the entire gamut of daylight and skylight chromaticities.* Appl. Opt., 38(27), 5703–5709.

$$n = \\frac{{x - x_e}}{{y - y_e}}, \\quad CCT = A_0 + A_1 e^{{-n/t_1}} + A_2 e^{{-n/t_2}} + A_3 e^{{-n/t_3}}$$

CCT = {R['CCT_hernandez']:.2f} K

### 5.3 Robertson 方法 (1968)（本报告采用）

> Robertson, A.R. (1968). *Computation of correlated color temperature and distribution temperature.* J. Opt. Soc. Am., 58(11), 1528–1535.

Robertson 方法在 CIE 1960 UCS (u, v) 色品图上，使用 31 个普朗克轨迹参考点的查找表和线性插值。该方法是 CIE 推荐的经典 CCT 计算方法。

```
CIE 1960 UCS: u = {u_1960:.6f},  v = {v_1960:.6f}
CCT = {R['CCT_robertson']:.2f} K
```

### 5.4 CCT 计算结果汇总

| 算法 | CCT (K) | 适用范围 | 备注 |
|------|---------|---------|------|
| McCamy (1992) | {R['CCT_mccamy']:.0f} | 2000–12500 K | 三次多项式近似 |
| Hernandez-Andres (1999) | {R['CCT_hernandez']:.0f} | 3000–50000 K | 指数函数近似 |
| **Robertson (1968)** | **{R['CCT_robertson']:.0f}** | 1000–∞ K | **CIE 推荐，查找表插值** |

三种方法结果高度一致（偏差 < 30 K），最终采用 Robertson 方法：**CCT = {R['CCT_robertson']:.0f} K**。此色温属于冷白色，略偏蓝，高于标准 D65 光源的 6504 K。

---

## 六、参考文献

1. CIE 015:2018, Colorimetry, 4th Edition.
2. McCamy, C.S. (1992). Correlated color temperature as an explicit function of chromaticity coordinates. *Color Research & Application*, 17(2), 142–144.
3. Hernandez-Andres, J., Lee, R.L., Romero, J. (1999). Calculating correlated color temperatures across the entire gamut of daylight and skylight chromaticities. *Applied Optics*, 38(27), 5703–5709.
4. Robertson, A.R. (1968). Computation of correlated color temperature and distribution temperature. *J. Opt. Soc. Am.*, 58(11), 1528–1535.
5. CVRL - Colour & Vision Research Laboratory. CIE 1931 2° CMFs. http://cvrl.ioo.ucl.ac.uk/cmfs.htm
6. PhotoResearch PR-7XX SpectraScan User's Manual. Novanta/JADAK, 2019.
7. Lindbloom, B. Useful Color Equations. http://www.brucelindbloom.com/
"""

with open(md_path, 'w', encoding='utf-8') as f:
    f.write(md)
print(f"Markdown 已生成: {md_path}")
