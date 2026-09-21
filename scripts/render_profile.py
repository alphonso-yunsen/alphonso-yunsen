"""Render a small GitHub dashboard with one palette and no third-party renderer.

Uses public REST endpoints and aggregate contribution counts only. In Actions,
GITHUB_TOKEN is scoped to this public profile repository, not other repositories.
No commit messages, emails, private repository metadata or raw API payloads saved.
"""
import argparse
from datetime import datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
THEME = json.loads((ROOT / 'profile-theme.json').read_text(encoding='utf-8'))
OUT = ROOT / 'generated'
FONT = 'Segoe UI,Arial,sans-serif'

def api(path, body=None):
    token = os.environ.get('GITHUB_TOKEN')
    headers = {'User-Agent': 'alphonso-starfield-profile', 'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request('https://api.github.com/' + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)
    if isinstance(result, dict) and result.get('errors'):
        raise RuntimeError('GitHub query failed; previous published cards remain intact')
    return result

def text(x, y, value, size=14, color='text', extra=''):
    return f'<text x="{x}" y="{y}" fill="{THEME.get(color, color)}" font-family="{FONT}" font-size="{size}" {extra}>{escape(str(value))}</text>'

def card(width, height, title, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
            f'<title>{escape(title)}</title><defs><linearGradient id="bg" x2="1" y2="1">'
            f'<stop stop-color="{THEME["background"]}"/><stop offset="1" stop-color="{THEME["panel"]}"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="20" fill="url(#bg)" stroke="{THEME["border"]}"/>'
            + content + '</svg>')

def save(name, svg):
    ET.fromstring(svg)
    (OUT / name).write_text(svg + '\n', encoding='utf-8')

def render_terminal():
    # Native SVG animation inspired by readme-typing-svg; no runtime service.
    content = '<style>@keyframes type{0%,8%{width:0}55%,88%{width:350px}100%{width:0}}@keyframes travel{0%,8%{transform:translateX(-350px)}55%,88%{transform:translateX(0)}100%{transform:translateX(-350px)}}@keyframes blink{50%{opacity:0}}.reveal{animation:type 12s steps(21,end) infinite}.cursor{animation:blink 1s step-end infinite,travel 12s steps(21,end) infinite}@media(prefers-reduced-motion:reduce){.reveal{animation:none;width:350px}.cursor{animation:none}}</style>'
    content += '<defs><clipPath id="typing"><rect class="reveal" x="58" y="61" width="640" height="45"/></clipPath></defs>'
    for x, color in [(28,'lavender'),(45,'cyan'),(62,'muted')]:
        content += f'<circle cx="{x}" cy="25" r="4" fill="{THEME[color]}"/>'
    content += text(88,30,'alphonso / midnight workspace',12,'muted')
    content += text(28,91,'>',22,'cyan')
    content += '<g clip-path="url(#typing)">' + text(58,91,'Create. Learn. Repeat.',27,'lavender', 'textLength="350" lengthAdjust="spacingAndGlyphs"') + '</g>'
    content += text(408,91,'_',26,'cyan','class="cursor"')
    content += text(28,126,'Somewhere between data and daydreams.',15,'muted')
    svg = card(760,152,'Create. Learn. Repeat. — animated terminal',content)
    ET.fromstring(svg)
    (ROOT/'assets/terminal.svg').write_text(svg+'\n',encoding='utf-8')

def frame_snake():
    raw = ET.parse(OUT/'snake-raw.svg').getroot()
    view = [float(v) for v in raw.attrib['viewBox'].split()]
    width, height = view[2] + 48, view[3] + 100
    raw.set('x','24'); raw.set('y','63')
    raw.set('width',str(view[2])); raw.set('height',str(view[3]))
    # Retain the original nested SVG/viewBox so upstream animation coordinates stay valid.
    content = text(28,31,'STAR TRAIL / 365 DAYS',15,'lavender','letter-spacing="2"')
    content += text(28,53,'A little comet, collecting a year of contributions.',12,'muted')
    content += ET.tostring(raw,encoding='unicode')
    save('snake.svg',card(width,height,'Contribution snake in a lavender starfield',content))

def render():
    user = THEME['user']
    profile = api('users/' + user)
    repos = []
    page = 1
    while True:
        batch = api(f'users/{user}/repos?type=owner&per_page=100&page={page}')
        # Explicitly discard private records even if an API response changes.
        repos.extend(r for r in batch if r.get('private') is False)
        if len(batch) < 100:
            break
        page += 1
    today = datetime.now(timezone.utc).date()
    first = today - timedelta(days=30)
    query = '''query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}'''
    data = api('graphql', {'query':query, 'variables':{'login':user,'from':first.isoformat()+'T00:00:00Z','to':datetime.now(timezone.utc).isoformat()}})
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    values = {d['date']:d['contributionCount'] for w in weeks for d in w['contributionDays']}
    days = [(first+timedelta(days=i)).isoformat() for i in range(31)]
    if any(d not in values for d in days):
        raise RuntimeError('Incomplete contribution calendar; not publishing a fabricated zero')
    counts = [values[d] for d in days]
    snapshot = {'user':user, 'as_of_utc':today.isoformat(), 'public_repos':len(repos),
                'public_stars':sum(r['stargazers_count'] for r in repos if not r['fork']),
                'followers':profile['followers'], 'contributions_31d':sum(counts),
                'calendar':[{'date':d,'count':n} for d,n in zip(days,counts)]}
    content = text(24,34,'OBSERVATORY',14,'lavender','letter-spacing="2"')
    content += text(24,57,'Small steps, visible progress.',13,'muted')
    entries = [('Public repos',snapshot['public_repos']),('Stars received',snapshot['public_stars']),('Followers',snapshot['followers']),('Contributions / 31d',sum(counts))]
    for i,(label,value) in enumerate(entries):
        x,y = 24+(i%2)*212, 112+(i//2)*85
        content += text(x,y,value,32,'cyan', 'font-weight="600"') + text(x,y+24,label,13,'muted')
    content += text(24,244,'UTC / '+today.isoformat(),10,'muted')
    save('overview.svg',card(440,264,'Public repositories, stars, followers and recent contributions',content))
    content = text(24,34,'NIGHT SIGNAL',14,'lavender','letter-spacing="2"')
    content += text(24,57,'GitHub contributions / last 31 days',13,'muted')
    max_n = max(1,max(counts))
    points = [(40+i*12,198-n/max_n*107) for i,n in enumerate(counts)]
    for ratio in [0,0.5,1]:
        y=198-ratio*107
        content += f'<path d="M40 {y}H400" stroke="{THEME["border"]}" opacity=".35"/>'
    path=' '.join(f'{x:.1f},{y:.1f}' for x,y in points)
    content += f'<polygon points="40,198 {path} 400,198" fill="{THEME["lavender"]}" opacity=".12"/>'
    content += f'<polyline points="{path}" fill="none" stroke="{THEME["lavender"]}" stroke-width="2.4" stroke-linejoin="round"/>'
    for x,y in points:
        content += f'<circle cx="{x}" cy="{y:.1f}" r="2.4" fill="{THEME["cyan"]}"/>'
    content += text(8,96,max_n,11,'muted') + text(15,202,0,11,'muted')
    content += text(40,222,first.strftime('%b %d'),11,'muted') + text(354,222,today.strftime('%b %d'),11,'muted')
    content += text(24,244,f'{sum(n>0 for n in counts)} active days · refreshed daily · UTC',10,'muted')
    save('activity.svg',card(440,264,'Daily GitHub contributions for the last 31 days',content))
    (OUT/'profile.json').write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
    render_terminal()
    print('Rendered overview, activity and terminal; aggregate fields only')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--frame-snake',action='store_true')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.frame_snake:
        frame_snake()
    else:
        render()
