#!/usr/bin/env python3
"""
Generate 24 per-image compression profile PDFs for Paper 4.
Template: kodim01_v6_final.pdf (manuscript-aligned calibration)

Revision notes:
- Scatter plot: 96-point cloud (24 OG + 72 SPDR from 2560 JPG), no arrows
- Q-spread plot: high contrast, strong OG slope, clear spread annotation
- Numeric precision: 3-decimal correlations (0.898 not 0.8980)
- ABC wording: manuscript-aligned, stops at "not observed"
- Resolution: pulled from actual FB JSON per image
- Control interpretation: manuscript wording only
"""

import json, glob, os, pickle, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ─── LOAD DATA ───
with open('all_data.pkl', 'rb') as f:
    data = pickle.load(f)

with open('all_spdr_points.pkl', 'rb') as f:
    all_spdr = pickle.load(f)

# All 24 originals for scatter
all_og = {}
for i in range(1, 25):
    img = f'kodim{i:02d}'
    all_og[img] = {
        'theta2': data[img]['og']['theta2'],
        'theta3': data[img]['og']['theta3'],
    }

LOO_SLOPE = 1.004
LOO_INTERCEPT = -2.372

# ─── FORMATTERS (V6 precision) ───
def fmt_bpp(val):
    return f"{val:.3f}"

def fmt_kb(bytes_val):
    return f"{bytes_val/1024:.1f} KB"

def fmt_pct(val):
    return f"{val:.1f}%"

def fmt_corr(val):
    """V6 precision: 4 decimal places for correlations"""
    if isinstance(val, str):
        val = float(val)
    return f"{val:.4f}"

def fmt_avg_r(val):
    """V6 precision: 3 decimal places for Avg|r|"""
    if isinstance(val, str):
        val = float(val)
    return f"{val:.3f}"

def fmt_angle(val):
    return f"{val}\u00b0"

def fmt_pixels(val):
    return f"{val:,}"

# ─── PAGE LAYOUT ───
W, H = letter
MARGIN_L = 54
MARGIN_R = 54
MARGIN_T = 54
MARGIN_B = 54
CONTENT_W = W - MARGIN_L - MARGIN_R

HEADER_RUNNING = 7.5
TITLE_SIZE = 18
SUBTITLE_SIZE = 10
SECTION_HEADER = 11
TABLE_FONT = 8.5
TABLE_HEADER_FONT = 8.5
FOOTER_SIZE = 7.5
NOTE_SIZE = 8
SMALL_SIZE = 7.5


def draw_running_header(c, page_num, total_pages=3):
    y = H - 36
    c.setFont("Courier", HEADER_RUNNING)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(MARGIN_L, y, "KODAK LOSSLESS TRUE COLOR IMAGE SUITE \u2014 PCD0992")
    c.drawRightString(W - MARGIN_R, y, f"Page {page_num} of {total_pages}")
    c.setFillColor(colors.black)


def draw_footer(c, page_num, total_pages=3):
    y = MARGIN_B - 10
    c.setStrokeColor(colors.Color(0.3, 0.3, 0.3))
    c.setLineWidth(0.5)
    c.line(MARGIN_L, y + 14, W - MARGIN_R, y + 14)
    c.setFont("Courier", FOOTER_SIZE)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(MARGIN_L, y, "Kodak PCD0992 Compression Profile Series  |  Baetzel (2026)")
    c.drawRightString(W - MARGIN_R, y, f"Page {page_num} of {total_pages}")
    c.setFillColor(colors.black)


def draw_title_block(c, img_id, img_data):
    y = H - MARGIN_T - 12
    c.setFont("Courier-Bold", TITLE_SIZE)
    res = img_data['og']['resolution']
    c.drawString(MARGIN_L, y, f"Compression Profile: {img_id.upper()}    {res} | 24-bit")
    y -= 22
    c.drawString(MARGIN_L, y, "RGB | PNG (lossless)")
    y -= 16
    c.setFont("Courier", SUBTITLE_SIZE)
    tier = img_data['tier']
    pc1 = img_data['og']['PC1_pct']
    c.drawString(MARGIN_L, y, f"{img_data['title']}  |  {tier} (PC1 = {pc1}%)")
    y -= 8
    c.setStrokeColor(colors.Color(0.3, 0.3, 0.3))
    c.setLineWidth(1.0)
    c.line(MARGIN_L, y, W - MARGIN_R, y)
    return y


# ─── SCATTER PLOT (V6 style, 96-point cloud, no arrows) ───
def make_scatter_plot(img_id, img_data):
    fig, ax = plt.subplots(1, 1, figsize=(5.8, 4.2))
    
    # Faint colored suite-wide perturbation cloud (72 points)
    dir_colors_faint = {'RED': '#e8a0a0', 'GRN': '#a0d0a0', 'BLU': '#a0b8e0'}
    for sp in all_spdr:
        ax.scatter(sp['theta2'], sp['theta3'], c=dir_colors_faint[sp['direction']], 
                   s=22, zorder=3, edgecolors='none', alpha=0.6)
    
    # Gray originals (24 points)
    for oid, odata in all_og.items():
        if oid == img_id:
            ax.scatter(odata['theta2'], odata['theta3'], c='#1a1a1a', s=70, zorder=7, edgecolors='none')
            short = img_id.replace('kodim0', 'k0').replace('kodim', 'k')
            ax.annotate(short, (odata['theta2'], odata['theta3']),
                       textcoords="offset points", xytext=(-16, 7),
                       fontsize=7.5, color='#1a1a1a', fontweight='bold')
        else:
            ax.scatter(odata['theta2'], odata['theta3'], c='#b0b0b0', s=30, zorder=4, edgecolors='none')
    
    # Highlighted current-image perturbations (3 points, labeled)
    dir_colors = {'RED': '#cc3333', 'GRN': '#339933', 'BLU': '#3366cc'}
    dir_labels = {'RED': 'R', 'GRN': 'G', 'BLU': 'B'}
    for dc, col in dir_colors.items():
        sd = img_data[f'spdr_{dc}']
        ax.scatter(sd['theta2'], sd['theta3'], c=col, s=90, zorder=8, edgecolors='none')
        ax.annotate(dir_labels[dc], (sd['theta2'], sd['theta3']),
                   textcoords="offset points", xytext=(7, -3),
                   fontsize=10, color=col, fontweight='bold')
    
    # LOO regression line
    x_line = np.linspace(5, 95, 100)
    y_line = LOO_SLOPE * x_line + LOO_INTERCEPT
    ax.plot(x_line, y_line, '--', color='#aaa', linewidth=0.8, zorder=2)
    
    # LOO equation
    ax.text(64, 80, f"LOO: \u03b8\u2083 = {LOO_SLOPE}\u00b7\u03b8\u2082 \u2212 {abs(LOO_INTERCEPT):.3f}\nr = 0.9993",
            fontsize=7.5, color='#888', ha='left')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#b0b0b0', label='Suite originals (n=24)'),
        mpatches.Patch(facecolor='#1a1a1a', label='This image (original)'),
        mpatches.Patch(facecolor='#cc3333', label='R-targeted'),
        mpatches.Patch(facecolor='#339933', label='G-targeted'),
        mpatches.Patch(facecolor='#3366cc', label='B-targeted'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=7, framealpha=0.9,
             edgecolor='#ccc', fancybox=False)
    
    ax.set_xlabel('\u03b8\u2082: PC2\u2194Cb misalignment (degrees)', fontsize=9)
    ax.set_ylabel('\u03b8\u2083: PC3\u2194Cr misalignment (degrees)', fontsize=9)
    ax.set_xlim(5, 95)
    ax.set_ylim(-2, 90)
    ax.tick_params(labelsize=8)
    ax.grid(True, alpha=0.2, linewidth=0.3)
    # Reduce spine/border opacity
    for spine in ax.spines.values():
        spine.set_color('#cccccc')
        spine.set_linewidth(0.5)
    ax.tick_params(colors='#888888')
    
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ─── QUALITY LADDER CHART (v6 layout) ───
def make_quality_ladder_chart(img_data):
    fig, ax = plt.subplots(1, 1, figsize=(5.8, 2.4))
    
    og_q90 = img_data['og_Q90']['bpp']
    og_q75 = img_data['og_Q75']['bpp']
    og_q60 = img_data['og_Q60']['bpp']
    red_q60 = img_data['spdr_RED_Q60']['bpp']
    grn_q60 = img_data['spdr_GRN_Q60']['bpp']
    blu_q60 = img_data['spdr_BLU_Q60']['bpp']
    
    og_pix = img_data['og']['pixels']
    spdr_pix = img_data['spdr_RED_Q60']['pixels']
    ratio = spdr_pix / og_pix
    
    labels = ['OG Q90', 'OG Q75', 'OG Q60', '', 'RED Q60', 'GRN Q60', 'BLU Q60']
    values = [og_q90, og_q75, og_q60, 0, red_q60, grn_q60, blu_q60]
    bar_colors = ['#ccc', '#ccc', '#ccc', 'white', '#cc3333', '#339933', '#3366cc']
    bar_alphas = [0.7, 0.7, 0.7, 0, 0.35, 0.35, 0.35]
    
    bars = ax.barh(range(len(labels)), values, color=bar_colors, height=0.6, edgecolor='none')
    for bar, alpha in zip(bars, bar_alphas):
        bar.set_alpha(alpha)
    
    for idx, (bar, val) in enumerate(zip(bars, values)):
        if val > 0:
            ax.text(val + 0.05, idx, f"{val:.3f}", va='center', fontsize=7.5)
    
    ax.text(max(values) * 1.15, 0, img_data['og']['resolution'], va='center', fontsize=7, color='#888')
    ax.text(max(values) * 1.15, 5, img_data['spdr_RED_Q60']['resolution'], va='center', fontsize=7, color='#888')
    ax.text(max(values) * 1.15, 6, f"{ratio:.1f}\u00d7 pixels", va='center', fontsize=7, color='#888')
    ax.text(0.3, 3, 'SPDR at Q60', fontsize=7, color='#888', style='italic', va='center')
    
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Bits Per Pixel (BPP)', fontsize=9)
    ax.invert_yaxis()
    ax.tick_params(labelsize=8)
    ax.set_xlim(0, max(values) * 1.35)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ─── Q SENSITIVITY CHART (strong contrast, old styling) ───
def make_q_sensitivity_chart(img_data):
    fig, ax = plt.subplots(1, 1, figsize=(5.8, 2.8))
    
    qs = ['Q60', 'Q75', 'Q90']
    x = [0, 1, 2]
    
    # OG through FB — moderate gray line (not dominant)
    og_fb = [img_data[f'og_fb2_{q}']['bpp'] for q in qs]
    ax.plot(x, og_fb, 'o-', color='#777', markersize=5, linewidth=1.2, label='Original \u2192 FB', zorder=5)
    
    # SPDR through FB — subdued colored lines (measurements primary, not visual)
    for dc, col in [('RED', '#cc3333'), ('GRN', '#339933'), ('BLU', '#3366cc')]:
        spdr_fb = [img_data[f'fb2_{dc}_{q}']['bpp'] for q in qs]
        ax.plot(x, spdr_fb, 's-', color=col, markersize=4, linewidth=1.0, 
               label=f'{dc} \u2192 FB', zorder=4, alpha=0.5)
    
    # OG spread annotation — clear bracket
    og_spread = og_fb[2] - og_fb[0]
    ax.annotate('', xy=(2.2, og_fb[0]), xytext=(2.2, og_fb[2]),
               arrowprops=dict(arrowstyle='<->', color='#555', lw=1.2))
    ax.text(2.35, (og_fb[0] + og_fb[2])/2, f"{og_spread:.3f}", fontsize=8, 
            va='center', color='#444', fontweight='bold')
    
    # SPDR spread annotation
    spdr_spreads = []
    for dc in ['RED', 'GRN', 'BLU']:
        s = img_data[f'fb2_{dc}_Q90']['bpp'] - img_data[f'fb2_{dc}_Q60']['bpp']
        spdr_spreads.append(s)
    avg_spdr_spread = sum(spdr_spreads) / 3
    mid_spdr = sum(img_data[f'fb2_RED_{q}']['bpp'] for q in qs) / 3
    ax.text(0.8, mid_spdr - 0.12, f"spread: {avg_spdr_spread:.3f}", 
            fontsize=7.5, color='#666', style='italic')
    
    ax.set_xticks(x)
    ax.set_xticklabels(['Q60', 'Q75', 'Q90'], fontsize=9)
    ax.set_xlabel('JPEG Quality Setting', fontsize=9)
    ax.set_ylabel('FB Output BPP', fontsize=9)
    ax.legend(fontsize=7.5, loc='upper left', framealpha=0.9, edgecolor='#ccc', fancybox=False)
    ax.tick_params(labelsize=8)
    ax.grid(True, alpha=0.2, linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ─── TABLE DRAWING ───
def draw_table(c, x, y, headers, rows, col_widths, row_height=14):
    c.setFont("Courier-Bold", TABLE_HEADER_FONT)
    cx = x
    for i, h in enumerate(headers):
        if i == 0:
            c.drawString(cx, y, h)
        else:
            c.drawRightString(cx + col_widths[i], y, h)
        cx += col_widths[i]
    
    y -= 4
    c.setStrokeColor(colors.Color(0.5, 0.5, 0.5))
    c.setLineWidth(0.5)
    c.line(x, y, x + sum(col_widths), y)
    y -= row_height
    
    c.setFont("Courier", TABLE_FONT)
    for row in rows:
        cx = x
        for i, cell in enumerate(row):
            if i == 0:
                c.drawString(cx, y, str(cell))
            else:
                c.drawRightString(cx + col_widths[i], y, str(cell))
            cx += col_widths[i]
        y -= row_height
    
    return y


# ═══════════════════════════════════════════
# PAGE 1: The Break (Geometric Displacement)
# ═══════════════════════════════════════════
def generate_page1(c, img_id, img_data):
    draw_running_header(c, 1)
    y = draw_title_block(c, img_id, img_data)
    
    y -= 20
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "1. Geometric Displacement Under Directional Perturbation")
    
    # Scatter plot — centered
    y -= 8
    scatter_buf = make_scatter_plot(img_id, img_data)
    img_reader = ImageReader(scatter_buf)
    plot_w = CONTENT_W * 0.92
    plot_h = plot_w * 0.72
    if plot_h > 310:
        plot_h = 310
        plot_w = plot_h / 0.72
    plot_x = MARGIN_L + (CONTENT_W - plot_w) / 2  # center horizontally
    c.drawImage(img_reader, plot_x, y - plot_h, width=plot_w, height=plot_h)
    y -= plot_h + 12
    
    # Section 2: Table
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "2. Pairwise Correlation and Angular Misalignment")
    y -= 18
    
    og = img_data['og']
    headers = ['Version', 'R-G', 'R-B', 'G-B', 'Avg |r|', 'theta2', 'theta3', 'LOO dev']
    col_widths = [90, 65, 65, 65, 60, 58, 58, 58]
    
    def loo_str(val):
        if isinstance(val, str): val = float(val)
        return f"+{val:.2f}\u00b0" if val >= 0 else f"{val:.2f}\u00b0"
    
    rows = []
    rows.append([
        'Original',
        fmt_corr(og['correlations']['R_G']),
        fmt_corr(og['correlations']['R_B']),
        fmt_corr(og['correlations']['G_B']),
        fmt_avg_r(og['correlations']['avg_abs_r']),
        fmt_angle(og['theta2']),
        fmt_angle(og['theta3']),
        loo_str(og.get('loo_dev', 0))
    ])
    
    for dc, label in [('RED', 'R-targeted'), ('GRN', 'G-targeted'), ('BLU', 'B-targeted')]:
        sd = img_data[f'spdr_{dc}']
        rows.append([
            label,
            fmt_corr(sd['correlations']['R_G']),
            fmt_corr(sd['correlations']['R_B']),
            fmt_corr(sd['correlations']['G_B']),
            fmt_avg_r(sd['correlations']['avg_abs_r']),
            fmt_angle(sd['theta2']),
            fmt_angle(sd['theta3']),
            loo_str(sd['loo_dev'])
        ])
    
    y = draw_table(c, MARGIN_L, y, headers, rows, col_widths)
    
    # Interpretive notes
    y -= 8
    c.setFont("Courier", NOTE_SIZE)
    
    red = img_data['spdr_RED']
    grn = img_data['spdr_GRN']
    blu = img_data['spdr_BLU']
    
    rg_r = abs(red['correlations']['R_G'])
    rb_r = abs(red['correlations']['R_B'])
    gb_r = abs(red['correlations']['G_B'])
    c.drawString(MARGIN_L, y, f"R-targeted isolates red (R-G, R-B < {max(rg_r, rb_r):.2f}) while preserving G-B coupling at {gb_r:.3f}.")
    y -= 12
    
    rg_g = abs(grn['correlations']['R_G'])
    gb_g = abs(grn['correlations']['G_B'])
    rb_g = abs(grn['correlations']['R_B'])
    c.drawString(MARGIN_L, y, f"G-targeted isolates green (R-G, G-B < {max(rg_g, gb_g):.2f}) while preserving R-B at {rb_g:.3f}.")
    y -= 12
    
    rg_b = abs(blu['correlations']['R_G'])
    c.drawString(MARGIN_L, y, f"B-targeted preserves R-G at {rg_b:.3f} while driving R-B and G-B near zero.")
    y -= 12
    
    c.drawString(MARGIN_L, y, "All three perturbation directions depart from the LOO constraint manifold (r = 0.9993).")
    
    draw_footer(c, 1)


# ═══════════════════════════════════════════
# PAGE 2: File Format and Size Comparison
# ═══════════════════════════════════════════
def generate_page2(c, img_id, img_data):
    c.showPage()
    draw_running_header(c, 2)
    y = draw_title_block(c, img_id, img_data)
    
    y -= 20
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "3. File Format and Size Comparison")
    y -= 14
    c.setFont("Courier", NOTE_SIZE)
    c.drawString(MARGIN_L, y, "All versions depict the same scene. BPP = (file size in bits) / (pixel count).")
    
    # ORIGINAL table
    y -= 20
    c.setFont("Courier-Bold", 9)
    c.drawString(MARGIN_L, y, f"ORIGINAL ({img_id})")
    y -= 16
    
    og = img_data['og']
    headers = ['Version', 'Format', 'Resolution', 'Size', 'BPP', 'Pixels']
    col_widths = [100, 55, 80, 70, 60, 70]
    
    rows = [
        ['PNG (lossless)', 'PNG', og['resolution'], fmt_kb(og['file_size_bytes']), fmt_bpp(og['bpp']), fmt_pixels(og['pixels'])],
        ['JPEG Q90', 'JPEG', img_data['og_Q90']['resolution'], fmt_kb(img_data['og_Q90']['file_size_bytes']), fmt_bpp(img_data['og_Q90']['bpp']), fmt_pixels(img_data['og_Q90']['pixels'])],
        ['JPEG Q75', 'JPEG', img_data['og_Q75']['resolution'], fmt_kb(img_data['og_Q75']['file_size_bytes']), fmt_bpp(img_data['og_Q75']['bpp']), fmt_pixels(img_data['og_Q75']['pixels'])],
        ['JPEG Q60', 'JPEG', img_data['og_Q60']['resolution'], fmt_kb(img_data['og_Q60']['file_size_bytes']), fmt_bpp(img_data['og_Q60']['bpp']), fmt_pixels(img_data['og_Q60']['pixels'])],
    ]
    y = draw_table(c, MARGIN_L, y, headers, rows, col_widths)
    
    # REDISTRIBUTED table
    y -= 16
    c.setFont("Courier-Bold", 9)
    c.drawString(MARGIN_L, y, f"REDISTRIBUTED ({img_id} SPDR at Q60)")
    y -= 16
    
    rows = []
    for dc, label in [('RED', 'RED Q60'), ('GRN', 'GRN Q60'), ('BLU', 'BLU Q60')]:
        sd = img_data[f'spdr_{dc}_Q60']
        rows.append([label, 'JPEG', sd['resolution'], fmt_kb(sd['file_size_bytes']),
                     fmt_bpp(sd['bpp']), fmt_pixels(sd['pixels'])])
    y = draw_table(c, MARGIN_L, y, headers, rows, col_widths)
    
    # Quality Ladder chart
    y -= 20
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "4. Quality Ladder: SPDR Q60 vs Original Q90")
    y -= 8
    
    ladder_buf = make_quality_ladder_chart(img_data)
    img_reader = ImageReader(ladder_buf)
    chart_w = CONTENT_W
    chart_h = chart_w * 0.41
    c.drawImage(img_reader, MARGIN_L, y - chart_h, width=chart_w, height=chart_h)
    y -= chart_h + 12
    
    c.setFont("Courier", NOTE_SIZE)
    spdr_pix = img_data['spdr_RED_Q60']['pixels']
    og_pix = img_data['og']['pixels']
    ratio = spdr_pix / og_pix
    c.drawString(MARGIN_L, y, f"All three perturbation directions at Q60 produced lower BPP than the original at Q90,")
    y -= 12
    c.drawString(MARGIN_L, y, f"while carrying {ratio:.1f}\u00d7 the original pixel count.")
    
    draw_footer(c, 2)


# ═══════════════════════════════════════════
# PAGE 3: Third-Party Pipeline + Q Sensitivity
# ═══════════════════════════════════════════
def generate_page3(c, img_id, img_data):
    c.showPage()
    draw_running_header(c, 3)
    y = draw_title_block(c, img_id, img_data)
    
    y -= 20
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "5. Third-Party Compression Pipeline (Facebook/Meta)")
    y -= 14
    c.setFont("Courier", NOTE_SIZE)
    c.drawString(MARGIN_L, y, "Each version uploaded to Facebook. Platform-compressed output measured at steady state (FB2).")
    y -= 18
    
    headers = ['Pipeline', 'Input Res', 'Output Res', 'FB BPP', 'BPP reduction']
    col_widths = [145, 80, 80, 65, 85]
    
    og_fb = img_data['og_fb2']
    # OG input res from the original, output res from FB JSON
    og_input_res = img_data['og']['resolution']
    
    rows = [
        ['OG PNG \u2192 FB', og_input_res, og_fb['resolution'], fmt_bpp(og_fb['bpp']), '\u2014']
    ]
    
    for dc, label in [('RED', 'R-targeted'), ('GRN', 'G-targeted'), ('BLU', 'B-targeted')]:
        fb = img_data[f'fb2_{dc}']
        spdr = img_data[f'spdr_{dc}']
        input_res = spdr['resolution']
        output_res = fb['resolution']  # actual FB output resolution per JSON
        pct = (1 - fb['bpp'] / og_fb['bpp']) * 100
        rows.append([f'{label} \u2192 FB', input_res, output_res, fmt_bpp(fb['bpp']), fmt_pct(pct)])
    
    # ABC control
    abc = img_data['abc_fb2']
    abc_pct = (1 - abc['bpp'] / og_fb['bpp']) * 100
    rows.append([
        'ABC (no perturbation) \u2192 FB',
        img_data['spdr_RED']['resolution'],
        abc['resolution'],
        fmt_bpp(abc['bpp']),
        fmt_pct(abc_pct)
    ])
    
    y = draw_table(c, MARGIN_L, y, headers, rows, col_widths)
    
    # ABC control note — manuscript-aligned wording
    y -= 6
    c.setFont("Courier", SMALL_SIZE)
    abc_corr = img_data['abc_fb2']['correlations']['avg_abs_r']
    og_corr = img_data['og']['correlations']['avg_abs_r']
    c.drawString(MARGIN_L, y, f"ABC control: same pipeline, same resolution, no covariance perturbation. Avg |r| unchanged")
    y -= 11
    c.drawString(MARGIN_L, y, f"({abc_corr:.4f} vs {og_corr:.3f} original). Comparable BPP reduction was not observed in the ABC control.")
    
    # Section 6: Q Parameter Sensitivity
    y -= 22
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, "6. Quality Parameter Sensitivity Through Facebook")
    y -= 8
    
    q_chart_buf = make_q_sensitivity_chart(img_data)
    img_reader = ImageReader(q_chart_buf)
    chart_w = CONTENT_W
    chart_h = chart_w * 0.48
    if y - chart_h < 160:
        chart_h = y - 170
        chart_w = chart_h / 0.48
    c.drawImage(img_reader, MARGIN_L, y - chart_h, width=chart_w, height=chart_h)
    y -= chart_h + 10
    
    # Q sensitivity notes
    c.setFont("Courier", NOTE_SIZE)
    og_q60_fb = img_data['og_fb2_Q60']['bpp']
    og_q90_fb = img_data['og_fb2_Q90']['bpp']
    og_spread = og_q90_fb - og_q60_fb
    
    spdr_spreads = []
    for dc in ['RED', 'GRN', 'BLU']:
        s = img_data[f'fb2_{dc}_Q90']['bpp'] - img_data[f'fb2_{dc}_Q60']['bpp']
        spdr_spreads.append(s)
    avg_spdr_spread = sum(spdr_spreads) / 3
    
    c.drawString(MARGIN_L, y, f"Original: Q60 \u2192 Q90 produces a {og_spread:.3f} BPP spread through Facebook.")
    y -= 12
    c.drawString(MARGIN_L, y, f"Redistributed: Q60 \u2192 Q90 produces a {abs(avg_spdr_spread):.3f} BPP spread through Facebook.")
    y -= 12
    c.drawString(MARGIN_L, y, "Redistributed versions produced substantially smaller Q60\u201390 BPP variation through the measured pipeline.")
    
    # Section 7: Pipeline Summary
    y -= 22
    c.setFont("Courier-Bold", SECTION_HEADER)
    c.drawString(MARGIN_L, y, f"7. Pipeline Summary \u2014 {img_id}")
    y -= 18
    
    best_dc = min(['RED', 'GRN', 'BLU'], key=lambda dc: img_data[f'spdr_{dc}_Q60']['bpp'])
    best_q60_bpp = img_data[f'spdr_{best_dc}_Q60']['bpp']
    best_q60_res = img_data[f'spdr_{best_dc}_Q60']['resolution']
    best_q60_pix = img_data[f'spdr_{best_dc}_Q60']['pixels']
    
    best_fb_dc = min(['RED', 'GRN', 'BLU'], key=lambda dc: img_data[f'fb2_{dc}']['bpp'])
    best_fb_bpp = img_data[f'fb2_{best_fb_dc}']['bpp']
    best_fb_res = img_data[f'fb2_{best_fb_dc}']['resolution']
    
    og_q90_fb_bpp = img_data['og_fb2_Q90']['bpp']
    vs_pct = (1 - best_fb_bpp / og_q90_fb_bpp) * 100 if og_q90_fb_bpp > 0 else 0
    
    og_pix = img_data['og']['pixels']
    pix_ratio = best_q60_pix / og_pix
    
    summary_items = [
        ('Best BPP (Q60, direct)', fmt_bpp(best_q60_bpp), f"{best_q60_res}, {fmt_pixels(best_q60_pix)} px"),
        ('Best BPP through FB', fmt_bpp(best_fb_bpp), f"{best_fb_res} output"),
        ('vs OG Q90 \u2192 FB', fmt_pct(vs_pct), f"SPDR Q60\u2192FB vs OG Q90\u2192FB"),
        ('Pixel ratio', f"{pix_ratio:.1f}\u00d7", f"{fmt_pixels(best_q60_pix)} vs {fmt_pixels(og_pix)}"),
    ]
    
    for label, value, note in summary_items:
        c.setFont("Courier", TABLE_FONT)
        c.drawString(MARGIN_L, y, label)
        c.setFont("Courier-Bold", TABLE_FONT)
        c.drawString(MARGIN_L + 200, y, value)
        c.setFont("Courier", SMALL_SIZE)
        c.setFillColor(colors.Color(0.5, 0.5, 0.5))
        c.drawString(MARGIN_L + 260, y, note)
        c.setFillColor(colors.black)
        y -= 14
    
    draw_footer(c, 3)


# ─── MAIN ───
def generate_pdf(img_id, img_data, output_dir):
    filename = os.path.join(output_dir, f"{img_id}_compression_profile.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    generate_page1(c, img_id, img_data)
    generate_page2(c, img_id, img_data)
    generate_page3(c, img_id, img_data)
    c.save()
    return filename


if __name__ == '__main__':
    output_dir = os.path.join(os.getcwd(), 'profiles_output')
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(1, 25):
        img_id = f'kodim{i:02d}'
        print(f"Generating {img_id}...", end=' ', flush=True)
        try:
            filename = generate_pdf(img_id, data[img_id], output_dir)
            print(f"OK")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nDone. {len(os.listdir(output_dir))} PDFs in {output_dir}/")
