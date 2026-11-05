"""Shared styles and checked PNG/PDF export for the selected scientific figures.

Run from any directory: python3 src/make_presentation_figures.py
Dependencies: existing requirements.txt (NumPy, pandas, Matplotlib).
"""
from pathlib import Path
import hashlib
import json
import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'ass2-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/figures'
SITES=('figure_eight_pools','stockton')
LABELS={'figure_eight_pools':'Figure Eight Pools','stockton':'Stockton'}
COLORS={'figure_eight_pools':'#0072B2','stockton':'#D55E00'}
MARKERS={'figure_eight_pools':'o','stockton':'s'}
MEASURES={'height_mi':('Height MI',r'$I(H_o;\,H_n)$','I(Ho;Hn)'),
          'period_cmi':('Peak-period CMI',r'$I(T_{p,o};\,H_n\mid H_o)$','I(Tp_o;Hn|Ho)'),
          'direction_cmi':('Peak-direction CMI',r'$I((D_x,D_y);\,H_n\mid H_o)$','I((Dx,Dy);Hn|Ho)')}
SOURCE_FILES=[ROOT/'results/primary_information/primary_information_summary.csv',ROOT/'results/sensitivity_analysis/all_sensitivity_results.csv',*[ROOT/f'data/processed/{site}.csv' for site in SITES]]
CAPTIONS=[]
CHECKS=[]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.titlesize':16,
        'axes.labelsize':14,'xtick.labelsize':12,'ytick.labelsize':12,
        'legend.fontsize':12,'axes.spines.top':False,'axes.spines.right':False,
        'axes.linewidth':.8,'axes.edgecolor':'#555555','axes.labelcolor':'#222222',
        'text.color':'#222222','xtick.color':'#444444','ytick.color':'#444444',
        'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
        'pdf.fonttype':42,'ps.fonttype':42,'mathtext.fontset':'dejavusans',
        'axes.formatter.useoffset':False})


def axes_style(ax):
    ax.set_axisbelow(True);ax.grid(axis='y',color='#E6E6E6',linewidth=.7)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))


def save(fig,stem,description,caption):
    """Keep the full 16:9 canvas; check rendered text bounds before exporting."""
    fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=fig.bbox
    outside=[]
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():continue
        box=text.get_window_extent(renderer)
        if box.width>0 and box.height>0 and (box.x0<bounds.x0-1 or box.x1>bounds.x1+1 or box.y0<bounds.y0-1 or box.y1>bounds.y1+1):
            outside.append(text.get_text())
    if outside:raise RuntimeError(f'Text outside canvas for {stem}: {outside}')
    fig.savefig(OUT/f'{stem}.png',dpi=300)
    fig.savefig(OUT/f'{stem}.pdf',format='pdf',metadata={'Title':description,'Creator':'Matplotlib; make_presentation_figures.py'})
    CHECKS.append({'figure':stem,'canvas_inches':list(fig.get_size_inches()),'png_dpi':300,
                   'text_within_canvas':True,'png_pixels':[4800,2700],
                   'png_sha256':sha(OUT/f'{stem}.png'),'pdf_sha256':sha(OUT/f'{stem}.pdf')})
    CAPTIONS.append({'figure':stem,'description':description,'suggested_caption':caption})
    plt.close(fig)

