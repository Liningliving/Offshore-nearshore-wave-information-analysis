"""Build the pinned, unmodified official CPU JIDT source using the local JDK."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tools/jidt/source'
BUILD=ROOT/'tools/jidt/build'
COMMIT='1ca832235e64ae5b3a482dc0ead6f9b2ff2a0456'
JAR=BUILD/'infodynamics.jar'


def build():
    revision=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    if revision!=COMMIT: raise RuntimeError('Source commit does not match the reviewed revision')
    if subprocess.check_output(['git','-C',str(SOURCE),'status','--porcelain'],text=True).strip():
        raise RuntimeError('Official source has local modifications; refusing unverified build')
    BUILD.mkdir(parents=True,exist_ok=True)
    classes=BUILD/'classes'; classes.mkdir(exist_ok=True)
    sources=sorted((SOURCE/'java/source').rglob('*.java'))
    args=BUILD/'sources.args';args.write_text('\n'.join('"'+str(p)+'"' for p in sources)+'\n')
    command=['javac','--release','8','-encoding','UTF-8','-d',str(classes),'@'+str(args)]
    result=subprocess.run(command,capture_output=True,text=True)
    (BUILD/'build.log').write_text(result.stdout+result.stderr);result.check_returncode()
    subprocess.run(['jar','--create','--file',str(JAR),'--main-class','infodynamics.demos.autoanalysis.AutoAnalyserLauncher','-C',str(classes),'.'],check=True)
    manifest={'repository':'https://github.com/jlizier/jidt','commit':COMMIT,
              'commit_url':f'https://github.com/jlizier/jidt/commit/{COMMIT}',
              'commit_date':subprocess.check_output(['git','-C',str(SOURCE),'show','-s','--format=%cI'],text=True).strip(),
              'build_xml_version':'1.6.1 (source snapshot; distinguish by commit, not release label)',
              'source_unmodified':True,'java_source_files':len(sources),'compile_command':command,
              'javac_version':subprocess.run(['javac','-version'],capture_output=True,text=True).stdout.strip(),
              'jar':str(JAR.relative_to(ROOT)),'jar_sha256':hashlib.sha256(JAR.read_bytes()).hexdigest(),
              'cpu_only':True,'fallback_jar':'/Users/attie/Desktop/Information theory/jidt-1.6.1/infodynamics.jar'}
    (BUILD/'build_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
    return manifest


if __name__=='__main__': build()
