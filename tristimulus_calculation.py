#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
色彩科学与应用 - 作业 1.1
三刺激值计算及色品坐标、相关色温求解

基于 PhotoResearch PR-788 光谱辐射度计对某显示屏白场的测量数据，
计算 CIE 1931 XYZ 三刺激值、xy 色品坐标、CIE 1976 u'v' 色品坐标及相关色温(CCT)。
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import FancyArrowPatch
from pathlib import Path
import os
import json

# ============================================================
# 0. 配置
# ============================================================
matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'STHeiti']
matplotlib.rcParams['axes.unicode_minus'] = False

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# 1. 读取原始测量数据（SPD）
# ============================================================
print("=" * 60)
print("步骤 1：读取 PhotoResearch PR-788 原始测量数据")
print("=" * 60)

xlsx_path = SCRIPT_DIR / "data" / "PhotoResearch_Raw_Data.xlsx"
df_raw = pd.read_excel(xlsx_path, sheet_name="PhotoResearch_Raw_Data")

# 提取学号和姓名
student_id = df_raw.iloc[0, 0]
student_name = df_raw.iloc[0, 1]
print(f"学号: {student_id}, 姓名: {student_name}")

# 提取波长和光谱功率分布
# 列从第4列（索引3）开始为波长数据 380-780nm
wavelengths_header = df_raw.columns[3:].astype(int).values
spd_values_str = df_raw.iloc[0, 3:].values

# 将字符串科学计数法转换为浮点数
spd_values = np.array([float(v) for v in spd_values_str])

print(f"波长范围: {wavelengths_header[0]} - {wavelengths_header[-1]} nm")
print(f"波长间隔: {wavelengths_header[1] - wavelengths_header[0]} nm")
print(f"数据点数: {len(spd_values)}")
print(f"SPD 最大值: {spd_values.max():.6e} W/sr/m²/nm")
print(f"SPD 最小值: {spd_values.min():.6e} W/sr/m²/nm")
print(f"\n前10个SPD值 (380-389 nm):")
for i in range(10):
    print(f"  λ = {wavelengths_header[i]} nm, S(λ) = {spd_values[i]:.6e} W/sr/m²/nm")

# ============================================================
# 2. 读取 CIE 1931 2° 标准观察者颜色匹配函数 (CMFs)
# ============================================================
print("\n" + "=" * 60)
print("步骤 2：读取 CIE 1931 2° 标准观察者颜色匹配函数")
print("=" * 60)
print("数据来源: http://cvrl.ioo.ucl.ac.uk/cmfs.htm")
print("文件: CIE 1931 2-deg, XYZ CMFs, 1 nm 间隔")

cmf_path = SCRIPT_DIR / "data" / "cie1931_cmf_1nm.csv"
cmf_data = np.loadtxt(cmf_path, delimiter=',')
cmf_wavelengths = cmf_data[:, 0].astype(int)
cmf_x = cmf_data[:, 1]
cmf_y = cmf_data[:, 2]
cmf_z = cmf_data[:, 3]

print(f"CMF 波长范围: {cmf_wavelengths[0]} - {cmf_wavelengths[-1]} nm")
print(f"CMF 数据点数: {len(cmf_wavelengths)}")

# 截取 380-780nm 范围（与测量数据匹配）
mask = (cmf_wavelengths >= 380) & (cmf_wavelengths <= 780)
cmf_wl = cmf_wavelengths[mask]
x_bar = cmf_x[mask]
y_bar = cmf_y[mask]
z_bar = cmf_z[mask]

print(f"\n匹配后波长范围: {cmf_wl[0]} - {cmf_wl[-1]} nm, 共 {len(cmf_wl)} 个数据点")
print(f"\n部分 CMF 数据（每隔 50nm 采样）:")
print(f"{'λ (nm)':>8}  {'x̄(λ)':>12}  {'ȳ(λ)':>12}  {'z̄(λ)':>12}")
for i in range(0, len(cmf_wl), 50):
    print(f"{cmf_wl[i]:>8d}  {x_bar[i]:>12.6f}  {y_bar[i]:>12.6f}  {z_bar[i]:>12.6f}")

# 确认波长对齐
assert np.array_equal(cmf_wl, wavelengths_header), "波长不匹配！"
print("\n✓ 测量数据与 CMF 波长完全对齐 (380-780nm, Δλ = 1nm)")

# ============================================================
# 3. 计算 CIE 1931 XYZ 三刺激值
# ============================================================
print("\n" + "=" * 60)
print("步骤 3：计算 CIE 1931 XYZ 三刺激值")
print("=" * 60)

delta_lambda = 1  # nm（波长间隔）
Km = 683  # lm/W（最大光谱光视效能）

print(f"\n计算公式（离散求和形式）:")
print(f"  X = Km × Σ S(λ) × x̄(λ) × Δλ")
print(f"  Y = Km × Σ S(λ) × ȳ(λ) × Δλ")
print(f"  Z = Km × Σ S(λ) × z̄(λ) × Δλ")
print(f"\n其中:")
print(f"  S(λ) = 光谱辐亮度 (W/sr/m²/nm)，由 PR-788 测量")
print(f"  x̄(λ), ȳ(λ), z̄(λ) = CIE 1931 2° 标准观察者颜色匹配函数")
print(f"  Δλ = {delta_lambda} nm（波长间隔）")
print(f"  Km = {Km} lm/W（明视觉最大光谱光视效能）")
print(f"  求和范围: λ = 380 nm 到 780 nm")

# --- 思路 A：绝对三刺激值（Y = 绝对亮度，单位 cd/m²）---
print(f"\n--- Y 值标准化思路 A：绝对三刺激值 ---")
print(f"  直接使用 K = 683 lm/W 作为系数")
print(f"  此时 Y 值即为绝对亮度（luminance），单位为 cd/m²")

# 逐波长乘积（中间值）
product_x = spd_values * x_bar * delta_lambda
product_y = spd_values * y_bar * delta_lambda
product_z = spd_values * z_bar * delta_lambda

print(f"\n部分中间值 S(λ)×x̄(λ)×Δλ（每隔 50nm 采样）:")
print(f"{'λ (nm)':>8}  {'S(λ)':>12}  {'x̄(λ)':>10}  {'S×x̄×Δλ':>14}  {'S×ȳ×Δλ':>14}  {'S×z̄×Δλ':>14}")
for i in range(0, len(cmf_wl), 50):
    print(f"{cmf_wl[i]:>8d}  {spd_values[i]:>12.4e}  {x_bar[i]:>10.6f}  "
          f"{product_x[i]:>14.6e}  {product_y[i]:>14.6e}  {product_z[i]:>14.6e}")

# 求和
sum_x = np.sum(product_x)
sum_y = np.sum(product_y)
sum_z = np.sum(product_z)

print(f"\n求和结果:")
print(f"  Σ S(λ)×x̄(λ)×Δλ = {sum_x:.6e}")
print(f"  Σ S(λ)×ȳ(λ)×Δλ = {sum_y:.6e}")
print(f"  Σ S(λ)×z̄(λ)×Δλ = {sum_z:.6e}")

# 绝对三刺激值
X_abs = Km * sum_x
Y_abs = Km * sum_y
Z_abs = Km * sum_z

print(f"\n绝对三刺激值（K = {Km} lm/W）:")
print(f"  X = {Km} × {sum_x:.6e} = {X_abs:.4f}")
print(f"  Y = {Km} × {sum_y:.6e} = {Y_abs:.4f}")
print(f"  Z = {Km} × {sum_z:.6e} = {Z_abs:.4f}")
print(f"  此时 Y = {Y_abs:.4f} cd/m²（显示屏白场亮度）")

# --- 思路 B：相对三刺激值（归一化 Y = 100）---
print(f"\n--- Y 值标准化思路 B：相对三刺激值 (Y = 100) ---")
print(f"  将三刺激值归一化，使 Y = 100")
print(f"  归一化系数 k = 100 / Y_abs = 100 / {Y_abs:.4f} = {100/Y_abs:.4f}")

k_norm = 100.0 / Y_abs
X_rel = X_abs * k_norm
Y_rel = Y_abs * k_norm  # = 100
Z_rel = Z_abs * k_norm

print(f"\n相对三刺激值:")
print(f"  X = {X_rel:.4f}")
print(f"  Y = {Y_rel:.4f}")
print(f"  Z = {Z_rel:.4f}")

# 本报告采用绝对三刺激值
X, Y, Z = X_abs, Y_abs, Z_abs
print(f"\n★ 本报告采用思路 A（绝对三刺激值），Y 的参考单位为 cd/m²")
print(f"  X = {X:.4f}")
print(f"  Y = {Y:.4f} cd/m²")
print(f"  Z = {Z:.4f}")

# ============================================================
# 4. 计算 CIE 1931 xy 色品坐标
# ============================================================
print("\n" + "=" * 60)
print("步骤 4：计算 CIE 1931 xy 色品坐标")
print("=" * 60)

print(f"\n计算公式:")
print(f"  x = X / (X + Y + Z)")
print(f"  y = Y / (X + Y + Z)")

sum_XYZ = X + Y + Z
x_chrom = X / sum_XYZ
y_chrom = Y / sum_XYZ

print(f"\n计算过程:")
print(f"  X + Y + Z = {X:.4f} + {Y:.4f} + {Z:.4f} = {sum_XYZ:.4f}")
print(f"  x = {X:.4f} / {sum_XYZ:.4f} = {x_chrom:.6f}")
print(f"  y = {Y:.4f} / {sum_XYZ:.4f} = {y_chrom:.6f}")

print(f"\n★ CIE 1931 xy 色品坐标:")
print(f"  x = {x_chrom:.4f}")
print(f"  y = {y_chrom:.4f}")

# ============================================================
# 5. 计算 CIE 1976 u'v' 色品坐标
# ============================================================
print("\n" + "=" * 60)
print("步骤 5：计算 CIE 1976 u'v' 色品坐标")
print("=" * 60)

print(f"\n计算公式:")
print(f"  u' = 4X / (X + 15Y + 3Z)")
print(f"  v' = 9Y / (X + 15Y + 3Z)")

denom_uv = X + 15 * Y + 3 * Z
u_prime = 4 * X / denom_uv
v_prime = 9 * Y / denom_uv

print(f"\n计算过程:")
print(f"  X + 15Y + 3Z = {X:.4f} + 15×{Y:.4f} + 3×{Z:.4f} = {denom_uv:.4f}")
print(f"  u' = 4×{X:.4f} / {denom_uv:.4f} = {u_prime:.6f}")
print(f"  v' = 9×{Y:.4f} / {denom_uv:.4f} = {v_prime:.6f}")

print(f"\n★ CIE 1976 u'v' 色品坐标:")
print(f"  u' = {u_prime:.4f}")
print(f"  v' = {v_prime:.4f}")

# ============================================================
# 6. 计算相关色温 (CCT)
# ============================================================
print("\n" + "=" * 60)
print("步骤 6：计算相关色温 (CCT)")
print("=" * 60)

# --- 方法 1：McCamy 近似公式 (1992) ---
print(f"\n--- 方法 1：McCamy 近似公式 (1992) ---")
print(f"参考文献: McCamy, C.S. (1992). Correlated color temperature as an")
print(f"  explicit function of chromaticity coordinates. Color Research &")
print(f"  Application, 17(2), 142-144.")
print(f"\n公式:")
print(f"  n = (x - 0.3320) / (y - 0.1858)")
print(f"  CCT = -449n³ + 3525n² - 6823.3n + 5520.33")

n_mccamy = (x_chrom - 0.3320) / (y_chrom - 0.1858)
CCT_mccamy = -449.0 * n_mccamy**3 + 3525.0 * n_mccamy**2 - 6823.3 * n_mccamy + 5520.33

print(f"\n计算过程:")
print(f"  n = ({x_chrom:.6f} - 0.3320) / ({y_chrom:.6f} - 0.1858)")
print(f"    = {x_chrom - 0.3320:.6f} / {y_chrom - 0.1858:.6f}")
print(f"    = {n_mccamy:.6f}")
print(f"  CCT = -449×{n_mccamy:.4f}³ + 3525×{n_mccamy:.4f}² - 6823.3×{n_mccamy:.4f} + 5520.33")
print(f"      = {-449.0*n_mccamy**3:.2f} + {3525.0*n_mccamy**2:.2f} + {-6823.3*n_mccamy:.2f} + 5520.33")
print(f"      = {CCT_mccamy:.2f} K")

# --- 方法 2：Ohno (2014) 改进方法 (基于 CIE 1960 UCS) ---
print(f"\n--- 方法 2：Hernandez-Andres 近似公式 (1999) ---")
print(f"参考文献: Hernandez-Andres, J., Lee, R.L., Romero, J. (1999).")
print(f"  Calculating correlated color temperatures across the entire")
print(f"  gamut of daylight and skylight chromaticities. Applied Optics,")
print(f"  38(27), 5703-5709.")
print(f"\n该方法适用范围更广 (3000-50000 K)，使用三次多项式:")
print(f"  n = (x - xe) / (y - ye)")
print(f"  CCT = A0 + A1*exp(-n/t1) + A2*exp(-n/t2) + A3*exp(-n/t3)")

# Hernandez-Andres 系数 (3000-50000K)
xe, ye = 0.3366, 0.1735
A0 = -949.86315
A1 = 6253.80338
t1 = 0.92159
A2 = 28.70599
t2 = 0.20039
A3 = 0.00004
t3 = 0.07125

n_ha = (x_chrom - xe) / (y_chrom - ye)
CCT_ha = A0 + A1 * np.exp(-n_ha / t1) + A2 * np.exp(-n_ha / t2) + A3 * np.exp(-n_ha / t3)

print(f"\n计算过程:")
print(f"  n = ({x_chrom:.6f} - {xe}) / ({ye} - {y_chrom:.6f})")
print(f"    = {n_ha:.6f}")
print(f"  CCT = {CCT_ha:.2f} K")

# --- 方法 3: Robertson 方法 (精确迭代) ---
print(f"\n--- 方法 3：Robertson 方法 (1968) ---")
print(f"参考文献: Robertson, A.R. (1968). Computation of correlated color")
print(f"  temperature and distribution temperature. J. Opt. Soc. Am.,")
print(f"  58(11), 1528-1535.")
print(f"\n该方法使用 CIE 1960 UCS (u, v) 坐标，在普朗克轨迹上进行")
print(f"反向插值，精度最高。")

# CIE 1960 UCS 坐标
u_1960 = 4 * X / (X + 15 * Y + 3 * Z)  # 同 u'
v_1960 = 6 * Y / (X + 15 * Y + 3 * Z)  # = 2/3 * v'

print(f"\n  CIE 1960 UCS 坐标:")
print(f"  u = {u_1960:.6f}")
print(f"  v = {v_1960:.6f}")

# Robertson 查找表 (31个参考点)
robertson_mired = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90,
    100, 125, 150, 175, 200, 225, 250, 275, 300, 325,
    350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600
]
robertson_u = [
    0.18006, 0.18066, 0.18133, 0.18208, 0.18293, 0.18388,
    0.18494, 0.18611, 0.18740, 0.18880, 0.19032, 0.19462,
    0.19962, 0.20525, 0.21142, 0.21807, 0.22511, 0.23247,
    0.24010, 0.24792, 0.25591, 0.26400, 0.27218, 0.28039,
    0.28863, 0.29685, 0.30505, 0.31320, 0.32129, 0.32931,
    0.33724
]
robertson_v = [
    0.26352, 0.26589, 0.26846, 0.27119, 0.27407, 0.27709,
    0.28021, 0.28342, 0.28668, 0.28997, 0.29326, 0.30141,
    0.30921, 0.31647, 0.32312, 0.32909, 0.33439, 0.33904,
    0.34308, 0.34655, 0.34951, 0.35200, 0.35407, 0.35577,
    0.35714, 0.35823, 0.35907, 0.35968, 0.36011, 0.36038,
    0.36051
]
robertson_slope = [
    -0.24341, -0.25479, -0.26876, -0.28539, -0.30470,
    -0.32675, -0.35156, -0.37915, -0.40955, -0.44278,
    -0.47888, -0.58204, -0.70471, -0.84901, -1.0182,
    -1.2168, -1.4512, -1.7298, -2.0637, -2.4681,
    -2.9641, -3.5814, -4.3633, -5.3762, -6.7262,
    -8.5955, -11.324, -15.628, -23.325, -40.770,
    -116.45
]

# 计算 d_i
d_values = []
for i in range(len(robertson_mired)):
    di = (v_1960 - robertson_v[i]) - robertson_slope[i] * (u_1960 - robertson_u[i])
    d_values.append(di)

# 找到 d 值符号变化的位置
idx = -1
for i in range(len(d_values) - 1):
    if d_values[i] / d_values[i + 1] < 0:
        idx = i
        break

if idx >= 0:
    # 线性插值
    d0 = d_values[idx]
    d1 = d_values[idx + 1]
    mired0 = robertson_mired[idx]
    mired1 = robertson_mired[idx + 1]
    mired_interp = mired0 + d0 * (mired1 - mired0) / (d0 - d1)
    CCT_robertson = 1e6 / mired_interp
    print(f"\n  插值位置: mired[{idx}]={mired0}, mired[{idx+1}]={mired1}")
    print(f"  d[{idx}] = {d0:.6f}, d[{idx+1}] = {d1:.6f}")
    print(f"  插值 MRD = {mired0} + {d0:.6f} × ({mired1} - {mired0}) / ({d0:.6f} - {d1:.6f})")
    print(f"          = {mired_interp:.4f} MRD (micro reciprocal degree)")
    print(f"  CCT = 10⁶ / {mired_interp:.4f} = {CCT_robertson:.2f} K")
else:
    CCT_robertson = float('nan')
    print("  Robertson 方法未能找到插值点")

print(f"\n★ 相关色温 (CCT) 计算结果汇总:")
print(f"  McCamy (1992):           {CCT_mccamy:.0f} K")
print(f"  Hernandez-Andres (1999): {CCT_ha:.0f} K")
print(f"  Robertson (1968):        {CCT_robertson:.0f} K")
print(f"\n  本报告采用 Robertson 方法结果: CCT = {CCT_robertson:.0f} K")

# ============================================================
# 7. 结果汇总
# ============================================================
print("\n" + "=" * 60)
print("结果汇总")
print("=" * 60)
print(f"\n  测量设备: PhotoResearch PR-788 光谱辐射度计")
print(f"  测量对象: 显示屏白场")
print(f"  波长范围: 380 - 780 nm, Δλ = 1 nm")
print(f"  SPD 单位: W/sr/m²/nm（光谱辐亮度）")
print(f"\n  CIE 1931 XYZ 三刺激值（绝对值，参考单位 cd/m²）:")
print(f"    X = {X:.4f}")
print(f"    Y = {Y:.4f} cd/m²")
print(f"    Z = {Z:.4f}")
print(f"\n  CIE 1931 xy 色品坐标:")
print(f"    x = {x_chrom:.4f}")
print(f"    y = {y_chrom:.4f}")
print(f"\n  CIE 1976 u'v' 色品坐标:")
print(f"    u' = {u_prime:.4f}")
print(f"    v' = {v_prime:.4f}")
print(f"\n  相关色温 (CCT): {CCT_robertson:.0f} K (Robertson 方法)")

# 保存计算结果为 JSON
results = {
    "student_id": int(student_id),
    "student_name": student_name,
    "X_abs": float(X),
    "Y_abs": float(Y),
    "Z_abs": float(Z),
    "X_rel": float(X_rel),
    "Y_rel": float(Y_rel),
    "Z_rel": float(Z_rel),
    "x": float(x_chrom),
    "y": float(y_chrom),
    "u_prime": float(u_prime),
    "v_prime": float(v_prime),
    "CCT_mccamy": float(CCT_mccamy),
    "CCT_hernandez": float(CCT_ha),
    "CCT_robertson": float(CCT_robertson),
}
with open(OUTPUT_DIR / "results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# ============================================================
# 8. 绘图
# ============================================================
print("\n" + "=" * 60)
print("步骤 7：绘制图表")
print("=" * 60)

# --- 8.1 光谱功率分布 (SPD) 图 ---
fig_spd, ax_spd = plt.subplots(figsize=(10, 5))
ax_spd.plot(wavelengths_header, spd_values, 'b-', linewidth=1.2)
ax_spd.fill_between(wavelengths_header, spd_values, alpha=0.15, color='blue')
ax_spd.set_xlabel('Wavelength (nm)', fontsize=12)
ax_spd.set_ylabel('Spectral Radiance (W/sr/m²/nm)', fontsize=12)
ax_spd.set_title('Spectral Power Distribution - Display White Point\n'
                  f'(PR-788 Measurement, Student ID: {student_id})', fontsize=13)
ax_spd.set_xlim(380, 780)
ax_spd.grid(True, alpha=0.3)
ax_spd.ticklabel_format(axis='y', style='scientific')
fig_spd.tight_layout()
fig_spd.savefig(OUTPUT_DIR / "01_spd.png", dpi=200, bbox_inches='tight')
print("  已保存: output/01_spd.png")

# --- 8.2 CIE 1931 xy 色品图 ---
# 生成光谱轨迹
cmf_full = np.loadtxt(cmf_path, delimiter=',')
mask_full = (cmf_full[:, 0] >= 360) & (cmf_full[:, 0] <= 830)
cmf_vis = cmf_full[mask_full]
wl_locus = cmf_vis[:, 0]
x_locus = cmf_vis[:, 1] / (cmf_vis[:, 1] + cmf_vis[:, 2] + cmf_vis[:, 3])
y_locus = cmf_vis[:, 2] / (cmf_vis[:, 1] + cmf_vis[:, 2] + cmf_vis[:, 3])

# 绘制色品图
fig_xy, ax_xy = plt.subplots(figsize=(8, 8))

# 光谱轨迹（horseshoe）
ax_xy.plot(x_locus, y_locus, 'k-', linewidth=1.5, label='Spectral Locus')
# 连接紫色线 (purple line)
ax_xy.plot([x_locus[0], x_locus[-1]], [y_locus[0], y_locus[-1]], 'k-', linewidth=1.5)

# 填充色品图区域（浅灰色）
xy_boundary = np.column_stack([
    np.concatenate([x_locus, [x_locus[0]]]),
    np.concatenate([y_locus, [y_locus[0]]])
])
from matplotlib.patches import Polygon
poly = Polygon(xy_boundary, closed=True, facecolor='#f0f0f0', edgecolor='none', alpha=0.5)
ax_xy.add_patch(poly)

# 标注光谱轨迹上的波长
wl_labels = [380, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560,
             570, 580, 590, 600, 610, 620, 700]
for wl_label in wl_labels:
    idx_label = np.argmin(np.abs(wl_locus - wl_label))
    if wl_locus[idx_label] == wl_label:
        xl, yl = x_locus[idx_label], y_locus[idx_label]
        ax_xy.plot(xl, yl, 'k.', markersize=4)
        # 偏移文本避免重叠
        offset_x, offset_y = 0.01, 0.01
        if wl_label < 490:
            offset_x, offset_y = -0.03, -0.01
        elif wl_label >= 560 and wl_label <= 580:
            offset_x, offset_y = 0.01, 0.015
        ax_xy.annotate(str(int(wl_label)), (xl, yl),
                       xytext=(xl + offset_x, yl + offset_y),
                       fontsize=7, color='gray')

# 绘制普朗克轨迹
planck_temps = np.arange(1000, 25001, 25)
planck_x_list, planck_y_list = [], []
for T in planck_temps:
    # 计算普朗克黑体辐射的色坐标（近似）
    # 使用 CIE 提供的 Planckian locus 近似公式
    if 1667 <= T <= 4000:
        xp = -0.2661239e9 / T**3 - 0.2343589e6 / T**2 + 0.8776956e3 / T + 0.179910
    elif 4000 < T <= 25000:
        xp = -3.0258469e9 / T**3 + 2.1070379e6 / T**2 + 0.2226347e3 / T + 0.240390
    else:
        continue
    if 1667 <= T <= 2222:
        yp = -1.1063814 * xp**3 - 1.34811020 * xp**2 + 2.18555832 * xp - 0.20219683
    elif 2222 < T <= 4000:
        yp = -0.9549476 * xp**3 - 1.37418593 * xp**2 + 2.09137015 * xp - 0.16748867
    elif 4000 < T <= 25000:
        yp = 3.0817580 * xp**3 - 5.87338670 * xp**2 + 3.75112997 * xp - 0.37001483
    else:
        continue
    planck_x_list.append(xp)
    planck_y_list.append(yp)

ax_xy.plot(planck_x_list, planck_y_list, 'k--', linewidth=0.8, alpha=0.5, label='Planckian Locus')

# 标注色温点
for T_label in [2000, 3000, 4000, 5000, 6500, 10000, 15000]:
    if 1667 <= T_label <= 4000:
        xp = -0.2661239e9 / T_label**3 - 0.2343589e6 / T_label**2 + 0.8776956e3 / T_label + 0.179910
    else:
        xp = -3.0258469e9 / T_label**3 + 2.1070379e6 / T_label**2 + 0.2226347e3 / T_label + 0.240390
    if 1667 <= T_label <= 2222:
        yp = -1.1063814 * xp**3 - 1.34811020 * xp**2 + 2.18555832 * xp - 0.20219683
    elif 2222 < T_label <= 4000:
        yp = -0.9549476 * xp**3 - 1.37418593 * xp**2 + 2.09137015 * xp - 0.16748867
    else:
        yp = 3.0817580 * xp**3 - 5.87338670 * xp**2 + 3.75112997 * xp - 0.37001483
    ax_xy.plot(xp, yp, 'k.', markersize=3)
    ax_xy.annotate(f'{T_label}K', (xp, yp), fontsize=6, color='dimgray',
                   xytext=(5, 5), textcoords='offset points')

# 标注测量点
ax_xy.plot(x_chrom, y_chrom, 'r*', markersize=15, markeredgecolor='darkred',
           markeredgewidth=0.5, label=f'Measured ({x_chrom:.4f}, {y_chrom:.4f})', zorder=5)
ax_xy.annotate(f'({x_chrom:.4f}, {y_chrom:.4f})\nCCT≈{CCT_robertson:.0f}K',
               (x_chrom, y_chrom),
               xytext=(x_chrom + 0.03, y_chrom - 0.05),
               fontsize=9, color='red', fontweight='bold',
               arrowprops=dict(arrowstyle='->', color='red', lw=1.2))

ax_xy.set_xlabel('x', fontsize=13)
ax_xy.set_ylabel('y', fontsize=13)
ax_xy.set_title('CIE 1931 xy Chromaticity Diagram', fontsize=14)
ax_xy.set_xlim(-0.05, 0.85)
ax_xy.set_ylim(-0.05, 0.90)
ax_xy.set_aspect('equal')
ax_xy.grid(True, alpha=0.2)
ax_xy.legend(loc='upper right', fontsize=9)
fig_xy.tight_layout()
fig_xy.savefig(OUTPUT_DIR / "02_cie1931_xy.png", dpi=200, bbox_inches='tight')
print("  已保存: output/02_cie1931_xy.png")

# --- 8.3 CIE 1976 u'v' 色品图 ---
# 将光谱轨迹转换为 u'v'
sum_xyz_locus = cmf_vis[:, 1] + cmf_vis[:, 2] + cmf_vis[:, 3]
X_locus = cmf_vis[:, 1]
Y_locus = cmf_vis[:, 2]
Z_locus = cmf_vis[:, 3]
u_locus = 4 * X_locus / (X_locus + 15 * Y_locus + 3 * Z_locus)
v_locus = 9 * Y_locus / (X_locus + 15 * Y_locus + 3 * Z_locus)

fig_uv, ax_uv = plt.subplots(figsize=(8, 8))

# 光谱轨迹
ax_uv.plot(u_locus, v_locus, 'k-', linewidth=1.5, label='Spectral Locus')
ax_uv.plot([u_locus[0], u_locus[-1]], [v_locus[0], v_locus[-1]], 'k-', linewidth=1.5)

# 填充
uv_boundary = np.column_stack([
    np.concatenate([u_locus, [u_locus[0]]]),
    np.concatenate([v_locus, [v_locus[0]]])
])
poly_uv = Polygon(uv_boundary, closed=True, facecolor='#f0f0f0', edgecolor='none', alpha=0.5)
ax_uv.add_patch(poly_uv)

# 标注波长
for wl_label in wl_labels:
    idx_label = np.argmin(np.abs(wl_locus - wl_label))
    if wl_locus[idx_label] == wl_label:
        ul, vl = u_locus[idx_label], v_locus[idx_label]
        ax_uv.plot(ul, vl, 'k.', markersize=4)
        offset_u, offset_v = 0.008, 0.008
        if wl_label < 490:
            offset_u, offset_v = -0.025, -0.008
        ax_uv.annotate(str(int(wl_label)), (ul, vl),
                       xytext=(ul + offset_u, vl + offset_v),
                       fontsize=7, color='gray')

# 普朗克轨迹 (u'v')
planck_u_list, planck_v_list = [], []
for xp, yp in zip(planck_x_list, planck_y_list):
    denom = -2 * xp + 12 * yp + 3
    up = 4 * xp / denom
    vp = 9 * yp / denom
    planck_u_list.append(up)
    planck_v_list.append(vp)
ax_uv.plot(planck_u_list, planck_v_list, 'k--', linewidth=0.8, alpha=0.5, label='Planckian Locus')

# 标注色温点
for T_label in [2000, 3000, 4000, 5000, 6500, 10000, 15000]:
    if 1667 <= T_label <= 4000:
        xp = -0.2661239e9 / T_label**3 - 0.2343589e6 / T_label**2 + 0.8776956e3 / T_label + 0.179910
    else:
        xp = -3.0258469e9 / T_label**3 + 2.1070379e6 / T_label**2 + 0.2226347e3 / T_label + 0.240390
    if 1667 <= T_label <= 2222:
        yp = -1.1063814 * xp**3 - 1.34811020 * xp**2 + 2.18555832 * xp - 0.20219683
    elif 2222 < T_label <= 4000:
        yp = -0.9549476 * xp**3 - 1.37418593 * xp**2 + 2.09137015 * xp - 0.16748867
    else:
        yp = 3.0817580 * xp**3 - 5.87338670 * xp**2 + 3.75112997 * xp - 0.37001483
    denom_t = -2 * xp + 12 * yp + 3
    up_t = 4 * xp / denom_t
    vp_t = 9 * yp / denom_t
    ax_uv.plot(up_t, vp_t, 'k.', markersize=3)
    ax_uv.annotate(f'{T_label}K', (up_t, vp_t), fontsize=6, color='dimgray',
                   xytext=(5, 5), textcoords='offset points')

# 标注测量点
ax_uv.plot(u_prime, v_prime, 'r*', markersize=15, markeredgecolor='darkred',
           markeredgewidth=0.5, label=f"Measured (u'={u_prime:.4f}, v'={v_prime:.4f})", zorder=5)
ax_uv.annotate(f"(u'={u_prime:.4f}, v'={v_prime:.4f})\nCCT≈{CCT_robertson:.0f}K",
               (u_prime, v_prime),
               xytext=(u_prime + 0.03, v_prime - 0.04),
               fontsize=9, color='red', fontweight='bold',
               arrowprops=dict(arrowstyle='->', color='red', lw=1.2))

ax_uv.set_xlabel("u'", fontsize=13)
ax_uv.set_ylabel("v'", fontsize=13)
ax_uv.set_title("CIE 1976 u'v' Chromaticity Diagram", fontsize=14)
ax_uv.set_xlim(-0.02, 0.65)
ax_uv.set_ylim(-0.02, 0.62)
ax_uv.set_aspect('equal')
ax_uv.grid(True, alpha=0.2)
ax_uv.legend(loc='upper right', fontsize=9)
fig_uv.tight_layout()
fig_uv.savefig(OUTPUT_DIR / "03_cie1976_uv.png", dpi=200, bbox_inches='tight')
print("  已保存: output/03_cie1976_uv.png")

plt.close('all')
print("\n所有图表已生成完毕。")

# ============================================================
# 9. 保存中间数据表格（CSV）
# ============================================================
print("\n" + "=" * 60)
print("步骤 8：导出中间计算数据")
print("=" * 60)

df_calc = pd.DataFrame({
    'Wavelength_nm': cmf_wl,
    'SPD_W_sr_m2_nm': spd_values,
    'x_bar': x_bar,
    'y_bar': y_bar,
    'z_bar': z_bar,
    'S_x_x_bar': spd_values * x_bar,
    'S_x_y_bar': spd_values * y_bar,
    'S_x_z_bar': spd_values * z_bar,
})
csv_path = OUTPUT_DIR / "intermediate_data.csv"
df_calc.to_csv(csv_path, index=False, float_format='%.8e')
print(f"  中间数据已保存至: {csv_path}")

print("\n★ 计算完毕！")
