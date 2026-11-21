#!/usr/bin/env python3
"""Generate original Faceless Shorts animation code with Gemini, not sample reuse."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def create_scenes(skill: Path, project: Path, style: str, prompt: str, seconds: int):
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY missing from GitHub Actions secrets')
    model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    if not model.startswith('gemini-') or '/' in model:
        raise ValueError('Invalid Gemini model name')
    rules = (skill / 'SKILL.md').read_text(encoding='utf-8')[:18000]
    style_rules = (skill / 'styles' / style / 'STYLE.md').read_text(encoding='utf-8')[:18000]
    reference = (project / 'src/shots.js').read_text(encoding='utf-8')
    starter_script = (project / 'script.json').read_text(encoding='utf-8')[:4500]
    # Use the complete reference when possible, but cap requests to avoid enormous prompts.
    reference = reference[:44000]
    instruction = f'''You are an expert JavaScript animator following an existing Faceless Shorts engine.
Create ACTUAL NEW ANIMATION CODE for this story. Do not reuse the example's story, cast, or script.
USER PROMPT: {prompt}
STYLE: {style}
TARGET DURATION: {seconds} seconds.

MASTER SKILL REQUIREMENTS:\n{rules}\n
STYLE-SPECIFIC ENGINE MANUAL:\n{style_rules}\n
EXAMPLE script.json (format only):\n{starter_script}\n
EXAMPLE src/shots.js (API and coding reference; your new file must REPLACE this):\n{reference}\n
Respond with exactly one JSON object containing two STRING properties:
"script_json": complete JSON text of the new script.json (with title, lines, lead, outro, speed, gap),
"shots_js": complete runnable JavaScript source text for src/shots.js.

IMPORTANT:
- Use ONLY imports/APIs demonstrated in the example or engine manual; no npm installs, external URLs or fetching.
- Export buildShots(E) compatible with the original engine; follow shot array structure exactly.
- Create new characters and visible motion matching the prompt, not merely text overlays.
- Make all animations fit within {seconds} seconds and show meaningful movement immediately.
- Keep dialogue VERY brief for this first {seconds}-second silent captions-only test.
- Prefer 1-3 shots for 5 seconds; other durations can use proportionally more shots.
- Work with the original browser/Three.js files already in the example project.
- No markdown fences or explanations, just valid JSON.
'''
    data = {'contents': [{'parts': [{'text': instruction}]}],
            'generationConfig': {'responseMimeType': 'application/json', 'maxOutputTokens': 12000, 'temperature': 0.35}}
    endpoint = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    req = Request(endpoint, data=json.dumps(data).encode('utf-8'), headers={
        'Content-Type': 'application/json', 'x-goog-api-key': key}, method='POST')
    try:
        with urlopen(req, timeout=150) as response:
            payload = json.load(response)
    except HTTPError as err:
        detail = err.read().decode('utf-8', errors='replace')[:1200]
        raise RuntimeError(f'Gemini API HTTP {err.code}: {detail}') from None
    except URLError as err:
        raise RuntimeError(f'Gemini connection failed: {err.reason}') from None
    try:
        parts = payload['candidates'][0]['content']['parts']
        result = json.loads(''.join(p.get('text','') for p in parts))
        script_text = result['script_json']
        shot_text = result['shots_js']
        script = json.loads(script_text)
        assert script.get('lines') and all(isinstance(l.get('text'), str) for l in script['lines'])
        assert 'export function buildShots' in shot_text
        assert len(shot_text) > 350
    except (KeyError, ValueError, TypeError, AssertionError) as err:
        raise RuntimeError(f'Gemini returned invalid animation files: {err}') from None
    # Generated source is executed only in a temporary GitHub-hosted runner.
    # Never interpolate these generated files into a shell command.
    (project / 'script.json').write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding='utf-8')
    (project / 'src/shots.js').write_text(shot_text, encoding='utf-8')
    (project / 'generated_from_prompt.txt').write_text(prompt + '\n', encoding='utf-8')
    print('Gemini created NEW script.json and src/shots.js. No example fallback.', flush=True)
