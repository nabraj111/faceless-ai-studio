#!/usr/bin/env python3
"""Render new Gemini-generated scenes using the original Faceless Shorts engine."""
import json, os, re, pathlib, subprocess, zipfile, sys
from generate_scenes import create_scenes

root = pathlib.Path(__file__).resolve().parents[1]
event = json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text())
issue = event['issue']
if issue['user']['login'].lower() != os.environ['GITHUB_REPOSITORY_OWNER'].lower():
    raise ValueError('Only repository owner can request render')
if not issue['title'].startswith('[Faceless Render]'):
    raise ValueError('Not a Faceless Render issue')
body = issue.get('body') or ''
match = re.search(r'```json\s*(\{.*?\})\s*```', body, flags=re.S)
if not match: raise ValueError('Request must include a JSON code block')
request = json.loads(match.group(1))
style = request.get('style')
styles = ('deep-dive','night-file','inside-out','stick-story','paper-atlas','tall-tale')
if style not in styles: raise ValueError('Invalid style')
seconds = int(request.get('duration_seconds', 5))
if seconds not in (5,15,30,60): raise ValueError('Invalid duration')
if request.get('aspect_ratio') != '9:16': raise ValueError('9:16 only in first test')
prompt = str(request.get('prompt','')).strip()
if not 1 <= len(prompt) <= 280: raise ValueError('Prompt must be 1-280 characters')
package = root/'faceless-shorts-skill.zip'
if not package.is_file(): raise FileNotFoundError('Original faceless-shorts-skill.zip missing')
target = root/'work'; target.mkdir(exist_ok=True)
with zipfile.ZipFile(package) as z:
    for entry in z.infolist():
        p=(target/entry.filename).resolve()
        if not p.is_relative_to(target.resolve()): raise ValueError('Unsafe ZIP member')
    z.extractall(target)
skill = target/'faceless-shorts'
if not (skill/'SKILL.md').is_file(): raise FileNotFoundError('Original SKILL.md missing')
project = root/'work'/'generated'/f'issue-{issue["number"]}'
project.parent.mkdir(parents=True,exist_ok=True)
def run(args, cwd=None, timeout=None, env=None):
    print('RUN', ' '.join(map(str,args)),flush=True)
    subprocess.run(list(map(str,args)),cwd=cwd,check=True,timeout=timeout,env=env or {k:v for k,v in os.environ.items() if k != 'GEMINI_API_KEY'})
run(['bash', skill/'scripts/new_video.sh', style, project.name, '--dir', project.parent])
print('STEP 1: Ask Gemini to build NEW prompt-specific scenes',flush=True)
create_scenes(skill,project,style,prompt,seconds)
print('STEP 2: Estimate caption timing and validate JavaScript syntax',flush=True)
run(['python',skill/'scripts/estimate.py',project])
run(['node','--check','src/shots.js'],cwd=project)
print('STEP 3: Capture the new animation, without original example audio',flush=True)
# Limit to 10fps and 5sec for the first trial, then expand after quality validation.
# Renderer must use freshly generated src/shots.js or fail (no copying from samples).
env={k:v for k,v in os.environ.items() if k != 'GEMINI_API_KEY'}
env.update(FPS='10', SOFTWARE_GL='1')
run(['node','tools/capture.mjs','video','renders/new-scene.mp4','0',str(seconds),'--draft'],cwd=project,timeout=1200,env=env)
output=root/'output'; output.mkdir(exist_ok=True)
video=output/f'faceless-{style}-issue-{issue["number"]}.mp4'
run(['ffmpeg','-y','-i','renders/new-scene.mp4','-t',str(seconds),'-vf','scale=540:960',
     '-c:v','libx264','-preset','veryfast','-crf','25','-pix_fmt','yuv420p','-movflags','+faststart',video],cwd=project,timeout=180)
(output/'README.txt').write_text(f'Style: {style}\nPrompt: {prompt}\nDuration: {seconds} seconds\n'
  'Gemini generated NEW script.json and src/shots.js from the prompt.\n'
  'First test is captions-only (silent), 10 FPS and subject to visual QA.\n')
(output/'script.json').write_text((project/'script.json').read_text())
print('RENDERED',video,flush=True)
