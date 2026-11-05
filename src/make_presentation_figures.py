"""Generate only the three selected presentation figures from saved results. No JIDT."""
from artifact_paths import resolve_artifact_path
from decimal import Decimal
from pathlib import Path
import json
import pandas as pd
import figure_style as m

def main(figures_dir=None, checks_dir=None):
    ROOT=m.ROOT
    OUT=Path(checks_dir) if checks_dir is not None else ROOT/'results/presentation_checks'
    FIGURES=Path(figures_dir) if figures_dir is not None else ROOT/'deliverables/figures'
    protected=[p for folder in ['data/processed','results/primary_information','results/sensitivity_analysis'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    before={str(p.relative_to(ROOT)):m.sha(p) for p in protected}
    manifest=json.loads((ROOT/'config/verified_sources.json').read_text())
    for path,digest in manifest['sources_sha256'].items(): assert m.sha(resolve_artifact_path(path))==digest,path
    OUT.mkdir(parents=True,exist_ok=True)
    FIGURES.mkdir(parents=True,exist_ok=True)
    m.OUT=FIGURES;m.style()
    p=pd.read_csv(ROOT/'results/primary_information/primary_information_summary.csv',float_precision='round_trip')
    r=pd.read_csv(ROOT/'results/sensitivity_analysis/all_sensitivity_results.csv',float_precision='round_trip')
    c=pd.read_csv(ROOT/'results/primary_information/between_site_contrasts.csv',dtype=str)
    for row in c.itertuples():
        f=p[(p.site=='figure_eight_pools')&(p.measure==row.measure)].iloc[0]
        s=p[(p.site=='stockton')&(p.measure==row.measure)].iloc[0]
        assert f.bits==float(row.FigureEight_bits) and s.bits==float(row.Stockton_bits)
        delta=Decimal(row.FigureEight_bits)-Decimal(row.Stockton_bits)
        if row.contrast!='delta_height':delta=-delta
        assert abs(delta-Decimal(row.observed_delta_bits))<Decimal('1e-15')
    for site,n in zip(m.SITES,[6867,10522]):
        d=pd.read_csv(ROOT/f'data/processed/{site}.csv')
        assert len(d)==n and not d.timestamp_utc.duplicated().any()
        assert d[['Ho','Hn','Tp_o','Dx','Dy']].notna().all().all()
        assert (d.Qflag==1).all() and (d.WAVE_quality_control==1).all()
    
    fig,axes=m.plt.subplots(1,3,figsize=(16,9))
    fig.subplots_adjust(left=.065,right=.97,top=.72,bottom=.30,wspace=.37)
    fig.suptitle('Observed offshore–nearshore information contrasts',y=.95,fontsize=24)
    fig.text(.5,.87,'Between-site differences in the original zero-lag estimates · descriptive, not inferential',ha='center',fontsize=15)
    for i,(ax,row,(key,(name,math,_))) in enumerate(zip(axes,c.itertuples(),m.MEASURES.items())):
        v=float(row.observed_delta_bits)
        color=m.COLORS['figure_eight_pools' if i==0 else 'stockton']
        ax.bar([0],[v],color=color,width=.45,zorder=3)
        ax.axhline(0,color='#555555',lw=1)
        ax.set_ylim((0,v*1.5) if v>0 else (v*1.5,0.012))
        ax.annotate(f'{v:+.6f}',(0,v),xytext=(0,12 if v>0 else -12),textcoords='offset points',ha='center',va='bottom' if v>0 else 'top',fontsize=20)
        order='Figure Eight Pools − Stockton' if i==0 else 'Stockton − Figure Eight Pools'
        ax.set_title(f'{chr(65+i)}  {name}\n{math}',loc='left',pad=23)
        ax.set(xticks=[0],xticklabels=[order],ylabel='Observed difference (bits)',xlim=(-.7,.7))
        ax.text(.5,-.24,f'FEP: {float(row.FigureEight_bits):.6f} bits\nStockton: {float(row.Stockton_bits):.6f} bits',transform=ax.transAxes,ha='center',fontsize=13,linespacing=1.6)
        m.axes_style(ax)
    fig.text(.065,.12,'Figure Eight Pools: Port Kembla / Wollongong offshore → Figure Eight Pools · N = 6,867',fontsize=12)
    fig.text(.065,.075,'Stockton: Sydney offshore → Stockton · N = 10,522. Independent panel scales; no validated between-site test.',fontsize=12)
    m.save(fig,'figure_1_between_site_contrasts','Observed between-site information contrasts','')
    
    fig,axes=m.plt.subplots(2,2,figsize=(16,9))
    fig.subplots_adjust(left=.08,right=.97,bottom=.22,top=.79,hspace=.68,wspace=.23)
    fig.suptitle('Temporal sensitivity of the observed site relationships',y=.96,fontsize=24)
    fig.text(.5,.89,'k = 4 throughout · saved Step 9 estimates · descriptive comparisons',ha='center',fontsize=15)
    for i,measure in enumerate(['height_mi','direction_cmi']):
        for j,(analysis,col,ticks,base,cohort) in enumerate([('lag','lag_hours',[0,.5,1,2],0,'common_source_timestamps'),('theiler','theiler_hours',[30,45,60],45,'original_cleaned')]):
            ax=axes[i,j]
            data=r[(r.measure==measure)&(r.analysis==analysis)&(r.cohort==cohort)]
            for site,n in zip(m.SITES,[6316,10307] if j==0 else [6867,10522]):
                rows=data[data.site==site].sort_values(col)
                assert list(rows[col])==ticks and (rows.sample_size==n).all() and (rows.k==4).all()
                assert (rows.theiler_hours==45).all() if j==0 else (rows.lag_hours==0).all()
                ax.plot(rows[col],rows.bits,color=m.COLORS[site],marker=m.MARKERS[site],lw=2,label=m.LABELS[site])
                b=rows[rows[col]==base]
                ax.scatter(b[col],b.bits,s=145,facecolors='none',edgecolors='#222222',zorder=4)
                if j==1:
                    value=p[(p.site==site)&(p.measure==m.MEASURES[measure][2])].iloc[0].bits
                    assert abs(b.iloc[0].bits-value)<1e-14
            ax.axvline(base,color='#888888',ls=':',lw=1)
            ax.set_title(f'{chr(65+i*2+j)}  {m.MEASURES[measure][0]} · '+('common source times' if j==0 else 'original observations'),loc='left',fontsize=14)
            ax.set(xticks=ticks,ylabel='Information estimate (bits)',xlabel=r'Positive propagation lag, $\tau$ (h)' if j==0 else 'Exact Theiler window, W (h)')
            ax.set_ylim(0,float(data.bits.max())*1.15);m.axes_style(ax)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.86),ncol=2,frameon=False)
    fig.text(.08,.135,'Lag panels: site-specific common source times, N = 6,316 / 10,307 (FEP / Stockton); W = 45 h.',fontsize=12)
    fig.text(.08,.09,'Window panels: original N = 6,867 / 10,522, zero lag. Rings mark the reference within each cohort.',fontsize=12)
    fig.text(.08,.045,'Positive lag: offshore(t) → nearshore(t + τ). Common-cohort lag = 0 differs from Step 7. Panel scales differ.',fontsize=12)
    m.save(fig,'figure_2_temporal_sensitivity','Lag and temporal-exclusion sensitivity','')
    audit={row['site']:row for row in json.loads((ROOT/'results/preprocessing/preprocessing_audit.json').read_text())}
    fig,axes=m.plt.subplots(1,2,figsize=(16,9))
    fig.subplots_adjust(left=.07,right=.96,bottom=.22,top=.77,wspace=.28)
    fig.suptitle('Concurrent offshore and nearshore wave heights',y=.95,fontsize=23,fontweight='semibold')
    fig.text(.5,.885,'Quality-filtered observations · zero propagation lag',ha='center',fontsize=15,color='#555555')
    for i,(ax,site) in enumerate(zip(axes,m.SITES)):
        d=pd.read_csv(ROOT/f'data/processed/{site}.csv')
        ax.scatter(d.Ho,d.Hn,s=11,marker=m.MARKERS[site],edgecolors='none',alpha=.20,color=m.COLORS[site],zorder=2)
        ax.plot([0,7],[0,7],color='#666666',ls='--',lw=1.3,label='Equal wave height',zorder=3)
        ax.set(xlim=(0,7),ylim=(0,7),xlabel=r'Offshore significant wave height, $H_o$ (m)',ylabel=r'Nearshore significant wave height, $H_n$ (m)')
        ax.set_aspect('equal',adjustable='box')
        ax.set_title(f'{chr(65+i)}  {m.LABELS[site]}',loc='left',color=m.COLORS[site],fontsize=19,pad=17)
        ax.text(.045,.95,f"Pearson r = {audit[site]['pearson_r']:.3f}\nN = {len(d):,}",transform=ax.transAxes,va='top',fontsize=14,bbox=dict(facecolor='white',edgecolor='none',alpha=.90,pad=5))
        ax.legend(loc='lower right',fontsize=11.5,frameon=True,facecolor='white',edgecolor='none')
        ax.set_axisbelow(True);ax.grid(color='#ECECEC',lw=.6)
    fig.text(.07,.125,'Matched time-domain significant wave heights (offshore WHTH; nearshore Hsig). Identical axes and equal aspect in both panels.',fontsize=12.5,color='#555555')
    fig.text(.07,.075,'Pearson correlations describe linear association; the dashed line is a reference, not a fitted model.',fontsize=12.5,color='#555555')
    m.save(fig,'figure_3_wave_heights','Offshore versus nearshore significant wave heights','')
    counts=pd.read_csv(ROOT/'results/sensitivity_analysis/lag_sample_counts.csv')
    for row in counts.itertuples():
        actual=r[(r.analysis=='lag')&(r.site==row.site)&(r.cohort==row.cohort)&(r.lag_hours==row.lag_hours)]
        assert len(actual)==3 and (actual.sample_size==row.sample_size).all()
    counts[['site','cohort','lag_hours','sample_size']].to_csv(OUT/'verified_lag_sample_counts.csv',index=False)
    p[['site','measure','sample_size','bits']].to_csv(OUT/'verified_primary_values.csv',index=False)
    assert all(m.sha(resolve_artifact_path(path))==digest for path,digest in before.items())
    (OUT/'verification.json').write_text(json.dumps({'original_files_unchanged':True,'protected_sha256':before,'verified_input_hashes_match':True,'six_primary_values_verified':True,'contrasts_verified':True,'lag_counts_verified':True,'sensitivity_window_baseline_matches_primary':True,'scatter_uses_original_rows_and_saved_correlation':True,'jidt_run':False,'new_statistical_analyses':False,'render_checks':m.CHECKS},indent=2)+'\n')
    print('Verified saved inputs, six estimates, contrasts, cohort counts and baselines. Saved the three selected figures from existing data/results.')

if __name__=="__main__":main()
