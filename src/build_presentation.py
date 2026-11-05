"""Build presentation and narration from existing project results; no estimation."""
from pathlib import Path
import csv
import textwrap
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from docx import Document
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/presentation'
FIG = ROOT / 'deliverables/figures'
# Display values are the saved primary results, rounded only for presentation.
SLIDES = [
('Offshore–nearshore wave dependence', 'An information-theoretic comparison of two NSW coastal settings', [
'Figure Eight Pools and Stockton', 'MSc Information Theory project', 'Descriptive deployment comparisons • MI and CMI'], None,
'''How closely do offshore waves describe conditions near the coast, and does that relationship differ between coastal settings? This project compares Figure Eight Pools and Stockton using mutual information and conditional mutual information. The aim is to quantify dependence, including additional information associated with offshore period and direction. Throughout this presentation, the differences are descriptive findings from two deployment records. They are not statistically confirmed population differences or evidence that coastal geometry caused the patterns.'''),
('Why compare these settings?', 'Physical motivation and predictions', [
'Kinsela et al. (2024): greater height scatter at embayed Stockton',
'Height MI predicted to be greater at exposed Figure Eight Pools',
'Period and direction CMI predicted to be greater at Stockton',
'Question: what differences do the observed deployment records show?'], None,
'''The motivation comes from Kinsela and colleagues, who compared the same buoy pairings and reported greater offshore–nearshore height scatter at Stockton. An exposed coastline may retain a more consistent connection with the regional offshore wave field, while an embayment may respond differently to changing approach direction. This motivates three predictions: higher height MI at Figure Eight Pools, and higher period and direction CMI at Stockton. These are predictions about information relationships, not direct measurements of attenuation. My height variables are time-domain significant heights, whereas Kinsela used spectral significant height, so this is a related investigation rather than an exact replication.'''),
('Two buoy pairings, different deployments', 'Sampling intervals and complete concurrent observations', [
'Port Kembla / Wollongong → Figure Eight Pools: N = 6,867',
'Sydney → Stockton: N = 10,522',
'Offshore: hourly parameters • Nearshore: half-hourly parameters',
'Matched: effectively hourly, with missing-data gaps',
'FEP: Dec 2016–Dec 2017 • Stockton: Dec 2019–Apr 2021'], None,
'''Figure Eight Pools is paired with the Port Kembla, or Wollongong, offshore station. Stockton is paired with Sydney. The original offshore parameter records are hourly and the nearshore records half-hourly. Exact concurrent matching produces effectively hourly observations with gaps: 6,867 complete observations at Figure Eight Pools and 10,522 at Stockton. These counts refer to the joint complete dataset used for all three primary measures. The deployments occur in different years and cover different durations, so this is not a simultaneous comparison under identical weather or seasonal conditions.'''),
('From buoy records to aligned observations', 'Quality control without filling missing hours', [
'Ho = offshore WHTH; Hn = nearshore Hsig: time-domain significant height',
'Tp,o = offshore WPPE; direction = offshore WPDI relative to true north',
'Apply supplied quality flags; align exact UTC timestamps',
'Retain valid extreme waves; no interpolation',
'Direction is one joint predictor: (cos θ, sin θ)'], None,
'''Preprocessing checked the supplied metadata and selected matching time-domain significant wave heights: offshore WHTH and nearshore Hsig. Peak period comes from WPPE and peak wave direction from WPDI. Nearshore fixed-AEST timestamps were converted to UTC before exact matching with offshore records. Quality flags and complete required variables determine the retained observations. Heights can be nonnegative and periods must be positive. Valid large waves are retained, and gaps are not interpolated. Direction is represented by cosine and sine together, preserving the circular connection between directions near zero and 360 degrees.'''),
('What do MI and CMI measure?', 'Dependence beyond a linear correlation', [
'Height MI: I(Ho; Hn)',
'Period CMI: I(Tp,o; Hn | Ho)',
'Direction CMI: I((Dx, Dy); Hn | Ho)',
'CMI asks what remains associated with Hn after Ho is known',
'Bits are not variance explained, attenuation or a causal effect'], None,
'''Height MI measures dependence between offshore and nearshore height without restricting the relationship to a straight line. Period CMI asks how much additional dependence period has with nearshore height after conditioning on offshore height. Directional CMI asks the corresponding question for joint direction. Neither conditional measure controls for the other predictor, so their values cannot be added as separate, non-overlapping contributions. Values are in bits, converted from JIDT’s nats by dividing by the natural logarithm of two. They do not express a percentage of explained variance, wave energy loss, or a causal influence.'''),
('A consistent estimator across both sites', 'Verified handling of temporal gaps', [
'JIDT continuous Kraskov algorithm 1 • k = 4',
'Normalization • max norm • GPU disabled',
'45-hour Theiler exclusion using actual elapsed time',
'Across-gap Java neighbour checks: 44 / 45 h excluded; 46 h eligible',
'Tie noise: 1e−8 after normalization • fixed seed 20261031'], None,
'''Both sites use the same continuous Kraskov algorithm one estimators with four nearest neighbours, normalization and the maximum norm. The existing autocorrelation analysis selected a common 45-hour Theiler window. This excludes temporally nearby observations as candidate neighbours. A key implementation check was to preserve actual elapsed-hour indices across missing observations, rather than counting retained rows. Java checks confirmed that observations 44 and 45 hours apart are excluded, while those 46 hours apart remain eligible across gaps. Small reproducible noise handles rounded measurement ties. These checks establish correct implementation; they do not prove unbiased estimation or independent observations.'''),
('Main results: direct site comparisons', 'Original zero-lag estimates • bits • descriptive only', [],
'figure_1_between_site_contrasts.png',
'''The main comparison shows a height MI of about 1.548 bits at Figure Eight Pools and 0.680 bits at Stockton. The Figure-Eight-minus-Stockton difference is positive 0.868023 bits, consistent with the height prediction. Directional CMI is about 0.097 bits at Figure Eight Pools and 0.232 at Stockton, giving a Stockton-minus-Figure-Eight difference of positive 0.134605 bits. Period CMI is small: approximately 0.031 and negative 0.010 bits, giving a difference of negative 0.040520 bits. Its ordering is opposite the period prediction. Negative estimated CMI reflects finite-sample estimation, not negative physical information. No significance markers or uncertainty intervals are shown.'''),
('Height relationships in the observations', 'All complete concurrent samples • matching axes', [],
'figure_3_wave_heights.png',
'''The scatterplots provide physical context for the information estimates. Offshore height is on the horizontal axis and nearshore height on the vertical axis, with matching scales for both sites. The dashed line marks equal wave height, rather than a fitted regression. The saved Pearson correlations are approximately 0.940 at Figure Eight Pools and 0.798 at Stockton. This descriptive pattern agrees with the height-MI ordering. However, MI is not attenuation: an invertible rescaling of wave height can change attenuation without changing population MI. Greater dependence should therefore not be interpreted directly as weaker energy loss.'''),
('Do the site orderings persist?', 'Propagation lag and Theiler-window sensitivity • k = 4', [],
'figure_2_temporal_sensitivity.png',
'''Temporal sensitivity changes one setting at a time. Positive lag compares offshore conditions at time t with nearshore height at t plus the lag. The main lag plots use common source timestamps within each site: 6,316 at Figure Eight Pools and 10,307 at Stockton. These differ from the primary samples. Across zero, half, one and two hours, the height contrast ranges from about 0.820 to 0.923 bits, while the directional contrast decreases from about 0.141 to 0.084 bits. Both site orderings persist. Theiler windows of 30, 45 and 60 hours also retain both orderings, with smaller magnitude changes. These are robustness checks, not confidence intervals or significance tests.'''),
('Physical interpretation: partial support', 'Consistent patterns, without a causal claim', [
'Height prediction: consistent with the observed estimates',
'Direction prediction: consistent; contrast magnitude depends on lag',
'Period prediction: not supported by the observed ordering',
'Exposure, sheltering and refraction are plausible explanations',
'Period may overlap with height information; mechanisms were not tested'], None,
'''The findings partially support the original predictions at the descriptive level. More consistent offshore–nearshore height dependence at Figure Eight Pools is compatible with its exposure. Greater directional CMI at Stockton is compatible with direction-dependent sheltering or transformation. These are plausible physical interpretations alongside Kinsela’s findings, not mechanisms demonstrated by this analysis. Period CMI may be small because offshore height already carries related information, or because one peak period incompletely describes mixed sea and swell. Rounding and finite-sample effects may also matter. None of these possibilities was separately tested, and small CMI does not establish that period is physically unimportant.'''),
('What the comparison can—and cannot—show', 'Statistical and environmental limitations', [
'One candidate between-site interval method failed initial calibration',
'No validated wave-data confidence intervals or p-values',
'Autocorrelation, unequal N, gaps and different seasonal coverage',
'Different depths and offshore stations; one site per setting',
'Sensitivity supports descriptive ordering, not population significance'], None,
'''A between-site statistical test was investigated because the central question compares two records. One time-block interval method was piloted on synthetic data but did not achieve adequate initial calibration. It was not used to report wave-data confidence intervals or p-values. That supplementary investigation does not mean all possible methods fail. The scientific conclusion remains descriptive. Different years, seasonal coverage, depths, local conditions and sample sizes complicate attribution, while one site per setting prevents generalising a geomorphic effect. The Theiler window does not remove every form of temporal dependence. A stable ordering across sensitivity settings is useful, but it cannot substitute for validated statistical inference.'''),
('Conclusion', 'Two deployment records show contrasting information relationships', [
'Height MI: greater at Figure Eight Pools by 0.868023 bits',
'Direction CMI: greater at Stockton by 0.134605 bits',
'Period CMI: small; Stockton − FEP = −0.040520 bits',
'Height and direction orderings persist under temporal checks',
'Descriptive contrasts—not significant population or causal effects'], None,
'''The main contribution is a reproducible information-theoretic comparison of two coastal deployment records. Figure Eight Pools shows stronger offshore–nearshore height dependence. Stockton shows greater additional dependence associated with offshore peak direction after offshore height is known. Period contributes little estimated conditional information and does not follow the predicted ordering. The height and direction orderings persist under the tested temporal choices, although their magnitudes are not equally stable. Together, the results extend the physical comparison with information measures while keeping the conclusions within the evidence: descriptive deployment differences, without established population significance or geomorphic causation.'''),
('References and reproducibility', 'Supporting slide—not part of the timed narration', [
'Kinsela et al. (2024), Scientific Data 11, 190',
'doi:10.1038/s41597-023-02865-x',
'Kraskov et al. (2004), Physical Review E 69, 066138',
'Lizier (2014), Frontiers in Robotics and AI 1, 11',
'Sources: final report, primary-information CSV and saved sensitivity results'], None,
'''Use this slide for reference or questions. The repository contains the original data, preprocessing audits, Java integration evidence, saved estimates and sensitivity results. The final scientific report provides full references and methodological limitations.'''),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Verify the six primary values before building; never run an estimator.
    with (ROOT/'results/primary_information/primary_information_summary.csv').open() as f:
        rows=list(csv.DictReader(f))
    expected=[1.5479403960385965,.0305376029311198,.0970024970185273,.6799175383439814,-.0099823133028735,.2316075347120687]
    assert len(rows)==6 and all(abs(float(r['bits'])-v)<1e-12 for r,v in zip(rows,expected))
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    navy='#142B43'; teal='#007F86'; ink='#263445'
    script=['# Presentation speaker script','', 'Target: approximately 10 minutes at a measured pace. Slides 1–12 are narrated; slide 13 is a reference slide. Adjust to the actual assessment time limit.','']
    doc=Document(); doc.add_heading('Offshore–nearshore wave dependence',0); doc.add_paragraph(script[2])
    with PdfPages(OUT/'presentation_preview.pdf') as pdf:
        for i,(title,subtitle,bullets,picture,notes) in enumerate(SLIDES,1):
            slide=prs.slides.add_slide(prs.slide_layouts[6])
            def box(x,y,w,h,text,size,color=ink,bold=False):
                tf=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame
                tf.word_wrap=True
                for j,line in enumerate(text.split('\n')):
                    par=tf.paragraphs[0] if j==0 else tf.add_paragraph()
                    par.text=line; par.font.name='Aptos'; par.font.size=Pt(size); par.font.bold=bold
                    par.font.color.rgb=RGBColor.from_string(color.lstrip('#'))
                    par.space_after=Pt(18)
            box(.55,.3,12.2,.65,title,30,navy,True)
            box(.58,1.05,12,.55,subtitle,17,teal)
            fig=plt.figure(figsize=(13.333,7.5)); fig.patch.set_facecolor('white')
            fig.text(.044,.925,title,fontsize=23,color=navy,weight='bold')
            fig.text(.044,.847,subtitle,fontsize=13,color=teal)
            if picture:
                path=FIG/picture
                with Image.open(path) as im: iw,ih=im.size
                w=min(12.1,5.15*iw/ih); h=w*ih/iw; x=(13.333-w)/2; y=1.72+(5.15-h)/2
                slide.shapes.add_picture(str(path), Inches(x), Inches(y),width=Inches(w),height=Inches(h))
                ax=fig.add_axes([x/13.333,1-(y+h)/7.5,w/13.333,h/7.5]); ax.imshow(Image.open(path)); ax.axis('off')
            else:
                for j,line in enumerate(bullets):
                    box(.7,1.95+j*.87,11.9,.82,'• '+line,23)
                    fig.text(.06,.69-j*.116,textwrap.fill('• '+line,88),fontsize=17,color=ink,va='top')
            footer=f'NSW wave information analysis  |  Descriptive estimates  |  {i:02d}'
            box(.6,7.08,12,.3,footer,10)
            fig.text(.045,.035,footer,fontsize=8,color=ink)
            slide.notes_slide.notes_text_frame.text=notes
            fig.savefig(OUT/f'slide_{i:02d}.png', dpi=100)
            pdf.savefig(fig); plt.close(fig)
            script.extend([f'## Slide {i} — {title}','',notes,''])
            doc.add_heading(f'Slide {i} — {title}',1); doc.add_paragraph(notes)
    prs.save(OUT/'offshore_nearshore_information.pptx')
    (OUT/'speaker_script.md').write_text('\n'.join(script))
    doc.save(OUT/'speaker_script.docx')
    words=sum(len(s[4].split()) for s in SLIDES[:12])
    (OUT/'README.md').write_text(f'''# Presentation materials\n\n- [Editable PowerPoint](offshore_nearshore_information.pptx): 13 slides in 16:9 format, including a reference slide; narration is also embedded in speaker notes.\n- [PDF preview](presentation_preview.pdf): independently rendered visual preview of the same content, not a PowerPoint export. Font wrapping may differ slightly in PowerPoint.\n- [Speaker script](speaker_script.md) and [Word script](speaker_script.docx): approximately {words} spoken words for slides 1–12 (around 9–11 minutes, depending on pace).\n\nUses the existing final report, original primary estimates and three existing scientific figures. No JIDT calculations, new statistical analyses or significance claims. Positive lag is offshore(t) → nearshore(t+τ). Main slides omit k sensitivity.\n\nRebuild from the repository root:\n\n```sh\n.venv/bin/python -m pip install -r config/requirements-presentation.txt\n.venv/bin/python src/build_presentation.py\n```\n\nCheck the editable deck in PowerPoint or Keynote before recording, especially figure labels and line wrapping. Confirm the actual assessment time limit; 10 minutes is a working assumption, not a verified course requirement.\n''')
    print(f'Built {len(SLIDES)} slides and script ({words} narrated words) in {OUT}')

if __name__=='__main__':
    main()
