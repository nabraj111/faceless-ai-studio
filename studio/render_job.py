#!/usr/bin/env python3
"""Render a Faceless Shorts original style demo from a GitHub issue request.

The original style example's scripted actions are unchanged. The viewer's prompt
becomes a title overlay; this is not arbitrary text-to-scene generation.
"""
import json, os, re, pathlib, subprocess, sys, zipfile, shutil
root = pathlib.Path(__file__).resolve().parents[1]
event = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text())
issue = event['issue']
assert issue['user']['login'].lower() == os.environ['GITHUB_REPOSITORY_OWNER'].lower(), 'Only owner requests can render.'
body = issue.get('body') or ''
match = re.search(r'```json\s*(\{.*?\})\s*```', body, flags=re.S)
if not match: raise ValueError('Request must include a JSON code block')
request = json.loads(match.group(1))
styles = ('deep-dive','night-file','inside-out','stick-story','paper-atlas','tall-tale')
style = request.get('style')
if style not in styles: raise ValueError('Invalid style')
seconds = int(request.get('duration_seconds', 5))
if seconds not in (5,15,30,60): raise ValueError('Invalid duration')
if request.get('aspect_ratio') != '9:16': raise ValueError('Current engine supports 9:16 only')
prompt = str(request.get('prompt','')).strip()
if not 1 <= len(prompt) <= 280: raise ValueError('Prompt must be 1-280 characters')
package = root/'faceless-shorts-skill.zip'
if not package.is_file(): raise FileNotFoundError('Original faceless-shorts-skill.zip missing from repository root')
with zipfile.ZipFile(package) as z:
    # Reject traversal entries from the attached archive
    target = root/'work';target.mkdir(exist_ok=True)
    for entry in z.infolist():
        p=(target/entry.filename).resolve()
        if not p.is_relative_to(target.resolve()): raise ValueError('Unsafe ZIP path')
    z.extractall(target)
skill = target/'faceless-shorts'
if not (skill/'SKILL.md').is_file(): raise ValueError('Expected faceless-shorts/SKILL.md')
project = root/'work'/'generated'/f'issue-{issue["number"]}'
project.parent.mkdir(exist_ok=True)
def run(args, cwd=None):
    print('RUN', ' '.join(map(str,args)), flush=True)
    subprocess.run(list(map(str,args)),cwd=cwd,check=True)
run(['bash',skill/'scripts/new_video.sh',style,project.name,'--dir',project.parent])
run(['python3',skill/'scripts/estimate.py',project])
run(['node','tools/capture.mjs','check'],cwd=project)
run(['node','tools/capture.mjs','cues'],cwd=project)
run(['python3','tools/mix.py','.'],cwd=project)
# Existing examples vary in duration; use their measured duration for a valid segment.
lines = json.loads((project/'data/lines.json').read_text())
source_length = float(lines['duration'])
clip_seconds = max(1,min(seconds,int(source_length)-1))
run(['node','tools/capture.mjs','video','renders/scene.mp4','0',str(clip_seconds),'--draft'],cwd=project)
# Add the user's actual prompt as a title, while preserving the existing animation.
# Text is passed as a file, never interpolated into a shell command/filter.
textfile = project/'overlay.txt'
textfile.write_text(prompt[:110],encoding='utf-8')
output = root/'output';output.mkdir(exist_ok=True)
filename=f'faceless-{style}-issue-{issue["number"]}.mp4'
video = output/filename
# Scale to max 540 wide to reduce processing and artifact size, loop if necessary.
filtergraph=("scale=540:960,"
             "drawbox=x=0:y=0:w=iw:h=190:color=black@0.65:t=fill:enable='lt(t,3.5)',"
             "drawtext=textfile=overlay.txt:fontcolor=white:fontsize=25:"
             "x=(w-text_w)/2:y=65:fix_bounds=1:enable='lt(t,3.5)'")
run(['ffmpeg','-y','-stream_loop','-1','-i','renders/scene.mp4','-t',str(seconds),
    '-vf',filtergraph,'-c:v','libx264','-preset','veryfast','-crf','27',
    '-c:a','aac','-b:a','96k','-movflags','+faststart',str(video)],cwd=project)
(output/'README.txt').write_text(f'Style: {style}\nPrompt/title: {prompt}\nDuration: {seconds}s\n'
   'This is an actual moving video rendered from the Skill\'s included example animation.\n'
   'The prompt is displayed as a title; the existing example animation was not rewritten to match it.\n')
print('OUTPUT:',video)
