"""Build the final descriptive report from saved results only; never invokes JIDT."""
from artifact_paths import resolve_artifact_path
from pathlib import Path
from decimal import Decimal
import hashlib,json,re,shutil
import pandas as pd
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables'
SITES=['figure_eight_pools','stockton']
MEASURES=['I(Ho;Hn)','I(Tp_o;Hn|Ho)','I((Dx,Dy);Hn|Ho)']

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',*['| '+' | '.join(map(str,r))+' |' for r in rows]])
def link(paragraph,label,target):
    h=OxmlElement('w:hyperlink');h.set(qn('r:id'),paragraph.part.relate_to(target,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True))
    run=OxmlElement('w:r');prop=OxmlElement('w:rPr');colour=OxmlElement('w:color');colour.set(qn('w:val'),'0563C1');prop.append(colour);run.append(prop)
    t=OxmlElement('w:t');t.text=label;run.append(t);h.append(run);paragraph._p.append(h)
def inline(paragraph,text):
    pattern=r'\*\*(.+?)\*\*|\*([^*]+)\*|\[([^\]]+)\]\(([^)]+)\)'
    pos=0
    for m in re.finditer(pattern,text):
        paragraph.add_run(text[pos:m.start()])
        if m.group(1):paragraph.add_run(m.group(1)).bold=True
        elif m.group(2):paragraph.add_run(m.group(2)).italic=True
        else:link(paragraph,m.group(3),m.group(4))
        pos=m.end()
    paragraph.add_run(text[pos:])

def word_document(text):
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=Inches(.72);sec.left_margin=sec.right_margin=Inches(.8)
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.12
    for name in ['Title','Heading 1','Heading 2']:
        doc.styles[name].font.name='Calibri';doc.styles[name].font.color.rgb=RGBColor.from_string('17365D')
    header=sec.header.paragraphs[0];header.text='MSc Information Theory · Descriptive two-deployment comparison';header.style='Caption'
    footer=sec.footer.paragraphs[0];footer.alignment=2
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                line=lines[i].strip()
                if not re.fullmatch(r'[|:\-\s]+',line):group.append([c.strip() for c in line.strip('|').split('|')])
                i+=1
            t=doc.add_table(rows=0,cols=len(group[0]));t.style='Light Shading Accent 1'
            for ri,row in enumerate(group):
                cells=t.add_row().cells
                for cell,value in zip(cells,row):
                    inline(cell.paragraphs[0],value)
                    for run in cell.paragraphs[0].runs:run.font.size=Pt(9)
                if ri==0:
                    repeat=OxmlElement('w:tblHeader');t.rows[-1]._tr.get_or_add_trPr().append(repeat)
                no_split=OxmlElement('w:cantSplit');t.rows[-1]._tr.get_or_add_trPr().append(no_split)
            doc.add_paragraph();continue
        match=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if match:
            doc.add_picture(str(OUT/match.group(2)),width=Inches(6.4));i+=1;continue
        if line.startswith('# '):doc.add_heading(line[2:],0)
        elif line.startswith('### '):doc.add_heading(line[4:],2)
        elif line.startswith('## '):doc.add_heading(line[3:],1)
        else:
            p=doc.add_paragraph(style='List Bullet' if line.startswith('- ') else 'Normal')
            inline(p,line[2:] if line.startswith('- ') else line)
            if line.startswith('**Figure '):p.paragraph_format.keep_with_next=True
        i+=1
    doc.core_properties.title='Offshore–nearshore wave dependence across contrasting NSW coastal settings'
    doc.core_properties.subject='Final descriptive report using unchanged Step 7 and Step 9 results'
    doc.core_properties.keywords='mutual information; conditional mutual information; coastal waves; descriptive comparison'
    doc.save(OUT/'final_scientific_report.docx')
    # Content consistency checks, not a visual pagination claim.
    reread=Document(OUT/'final_scientific_report.docx')
    assert len(reread.inline_shapes)==3 and len(reread.tables)==5
    for value in ['+0.868023','−0.040520','+0.134605']:
        assert value in '\n'.join(p.text for p in reread.paragraphs)

def main():
    protected=[p for area in ['data','results','research','deliverables'] for p in (ROOT/area).rglob('*') if p.is_file() and not p.is_relative_to(OUT)]
    protected += [p for p in (ROOT/'data/raw').rglob('*') if p.is_file()]+[ROOT/'docs/project_proposal.pdf']
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    primary_path=ROOT/'results/primary_information/primary_information_summary.csv'
    results_path=ROOT/'results/sensitivity_analysis/all_sensitivity_results.csv'
    contrast_path=ROOT/'results/primary_information/between_site_contrasts.csv'
    p=pd.read_csv(primary_path,dtype=str);r=pd.read_csv(results_path,float_precision='round_trip');c=pd.read_csv(contrast_path,dtype=str)
    original=json.loads((ROOT/'config/verified_sources.json').read_text())
    for path,wanted in original['sources_sha256'].items():assert digest(resolve_artifact_path(path))==wanted,path
    rows=[]
    labels=['Height MI: I(Hₒ; Hₙ)','Period CMI: I(Tₚ,ₒ; Hₙ ∣ Hₒ)','Direction CMI: I((Dₓ,Dᵧ); Hₙ ∣ Hₒ)']
    for measure,label,contrast in zip(MEASURES,labels,c.itertuples()):
        values=[]
        for site,n in zip(SITES,[6867,10522]):
            row=p[(p.site==site)&(p.measure==measure)].iloc[0]
            assert int(row.sample_size)==n
            assert abs(float(row.bits)-float(row.nats)/__import__('math').log(2))<1e-14
            values.append(Decimal(row.bits))
        assert values[0]==Decimal(contrast.FigureEight_bits) and values[1]==Decimal(contrast.Stockton_bits)
        delta=values[0]-values[1] if measure==MEASURES[0] else values[1]-values[0]
        assert abs(delta-Decimal(contrast.observed_delta_bits))<Decimal('1e-15')
        order='FEP − Stockton' if measure==MEASURES[0] else 'Stockton − FEP'
        rows.append([label,format(values[0],'.6f'),format(values[1],'.6f'),order,format(delta,'+.6f').replace('-','−')])
    assert Decimal(p[(p.site=='stockton')&(p.measure==MEASURES[1])].iloc[0].bits)<0
    replacements={'PRIMARY_TABLE':table(['Measure','FEP (bits)','Stockton (bits)','Difference definition','Difference (bits)'],rows)}
    focus=r[(r.analysis=='theiler')|((r.analysis=='lag')&(r.k==4))].copy()
    assert (focus.k==4).all() and len(focus)==66 # 48 lag +18 window rows, all original measures
    focus.to_csv(OUT/'temporal_sensitivity_reused.csv',index=False)
    for analysis,cohort,col,token in [('lag','common_source_timestamps','lag_hours','COMMON_LAG_TABLE'),('theiler','original_cleaned','theiler_hours','THEILER_TABLE'),('lag','all_available','lag_hours','AVAILABLE_LAG_TABLE')]:
        d=r[(r.analysis==analysis)&(r.cohort==cohort)]
        output=[]
        for setting in sorted(d[col].unique()):
            sel=d[d[col]==setting];values=[];counts=[]
            for site in SITES:
                group=sel[sel.site==site];assert group.sample_size.nunique()==1
                counts.append(int(group.sample_size.iloc[0]))
            for measure in ['height_mi','direction_cmi']:
                for site in SITES:
                    item=sel[(sel.site==site)&(sel.measure==measure)].iloc[0]
                    assert item.k==4
                    values.append(f'{item.bits:.6f}')
            if cohort=='common_source_timestamps':assert counts==[6316,10307]
            if analysis=='theiler':assert counts==[6867,10522]
            output.append([f'{setting:g}']+counts+values if cohort=='all_available' else [f'{setting:g}']+values)
        head=[('τ (h)' if analysis=='lag' else 'W (h)')]+(['FEP N','Stockton N'] if cohort=='all_available' else [])+['FEP height','Stockton height','FEP direction','Stockton direction']
        replacements[token]=table(head,output)
    # Verify reported orderings using only selected, non-k sensitivity rows.
    for (analysis,cohort),g in focus.groupby(['analysis','cohort']):
        col='lag_hours' if analysis=='lag' else 'theiler_hours'
        for measure,positive_site in [('height_mi',SITES[0]),('direction_cmi',SITES[1])]:
            v=g[g.measure==measure].pivot(index=col,columns='site',values='bits')
            other=SITES[1] if positive_site==SITES[0] else SITES[0]
            assert (v[positive_site]>v[other]).all()
    for src,name in [(primary_path,'primary_information_summary.csv'),(contrast_path,'between_site_contrasts.csv')]:shutil.copy2(src,OUT/name)
    figure_hashes={}
    for stem in ['figure_1_between_site_contrasts','figure_2_temporal_sensitivity','figure_3_wave_heights']:
        for ext in ['png','pdf']:
            src=OUT/f'figures/{stem}.{ext}';dest=src
            assert src.is_file();figure_hashes[str(dest.relative_to(OUT))]=digest(src)
    text=(ROOT/'docs/templates/final_report.md').read_text()
    for key,value in replacements.items():text=text.replace('{{'+key+'}}',value)
    assert '{{' not in text
    (OUT/'final_scientific_report.md').write_text(text)
    word_document(text)
    assert all(digest(ROOT/path)==wanted for path,wanted in before.items())
    sources=['results/primary_information/primary_information_summary.csv','results/sensitivity_analysis/all_sensitivity_results.csv','results/primary_information/between_site_contrasts.csv','results/preprocessing/preprocessing_audit.json','results/preprocessing/verified_dataset_description.csv','results/preprocessing/autocorrelation_decay_summary.csv','research/surrogate_validation/report.md','research/between_site_method_assessment/assessment.md','docs/project_proposal.pdf','docs/templates/final_report.md']
    (OUT/'report_manifest.json').write_text(json.dumps(dict(preserved_original_sha256=before,original_files_unchanged=True,sources_sha256={path:digest(ROOT/path) for path in sources},figure_copies_sha256=figure_hashes,checks=dict(six_primary_estimates_match=True,negative_period_estimate_preserved=True,three_contrasts_match=True,sampling_counts_and_cohorts_verified=True,non_k_temporal_orderings_verified=True,three_existing_figures_reused_unchanged=True,docx_tables_and_embedded_figures_verified=True),new_information_estimates=0,new_statistical_tests=0,new_simulations=0,wave_confidence_intervals_available=False,wave_pvalues_available=False,scientific_scope='descriptive full-deployment case comparison; not calibrated population inference',software=dict(pandas=pd.__version__,python_docx=__import__('docx').__version__)),indent=2)+'\n')
    print('Created Markdown and Word reports with 3 reused figures; verified source values, temporal cohorts and original-file preservation. No estimator or statistical test run.')

if __name__=='__main__':main()
