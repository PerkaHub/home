"""Validate lab 2 documents using only the Python standard library."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = ['Контекст', 'Движущие факторы', 'Рассмотренные варианты', 'Решение', 'Последствия']

def adr_errors(text, name, index):
    errors = []
    for title in HEADINGS:
        if f'## {title}' not in text:
            errors.append(f'{name}: missing {title}')
    for field in ['Статус', 'Дата', 'Участники', 'Отрицательные', 'Что пересмотрит', 'Определяющий довод']:
        if field not in text:
            errors.append(f'{name}: missing {field}')
    if name not in index:
        errors.append(f'{name}: missing index entry')
    options = text.split('## Рассмотренные варианты')[-1].split('## Решение')[0]
    rows = [line for line in options.splitlines() if line.startswith('|')]
    if len(rows) < 4:
        errors.append(f'{name}: need two alternatives')
    return errors

def check():
    errors = []
    index = (ROOT/'docs/adr/README.md').read_text(encoding='utf-8')
    adrs = sorted((ROOT/'docs/adr').glob('0*.md'))
    if len(adrs) < 5:
        errors.append('Need at least five ADRs')
    for p in adrs:
        errors.extend(adr_errors(p.read_text(encoding='utf-8'), p.name, index))
    for p in [ROOT/'README.md', ROOT/'CONTRIBUTING.md', *(ROOT/'docs').rglob('*.md')]:
        text = p.read_text(encoding='utf-8')
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            if '://' in link or link.startswith('#'):
                continue
            target = link.split('#')[0]
            if target and not (p.parent/target).exists():
                errors.append(f'{p.relative_to(ROOT)}: broken link {link}')
    requirements = (ROOT/'docs/requirements.md').read_text(encoding='utf-8')
    trace = (ROOT/'docs/traceability.md').read_text(encoding='utf-8')
    for i in range(1,7):
        if f'FR-{i:02}' not in trace:
            errors.append(f'Missing trace FR-{i:02}')
        for j in range(1,5):
            if f'AC-{i:02}.{j}' not in requirements:
                errors.append(f'Missing AC-{i:02}.{j}')
    for prefix, count in [('NFR',8),('BR',2)]:
        for i in range(1,count+1):
            if f'{prefix}-{i:02}' not in trace:
                errors.append(f'Missing trace {prefix}-{i:02}')
    for filename in ['domain/context-map.mmd','architecture/c4/context.mmd','architecture/c4/container.mmd','architecture/sequence/create-payment.mmd','architecture/data/model.mmd','api/resources.md','architecture/overview.md']:
        if not (ROOT/'docs'/filename).is_file():
            errors.append(f'Missing {filename}')
    return errors

def self_test():
    p = ROOT/'docs/adr/0002-backend-language.md'
    text = p.read_text(encoding='utf-8')
    index = (ROOT/'docs/adr/README.md').read_text(encoding='utf-8')
    assert adr_errors(text.replace('## Контекст','## Removed'),p.name,index), 'Missing section was accepted'
    assert adr_errors(text,p.name,''), 'Missing index entry was accepted'
    print('PASS: negative ADR checks reject missing section and index entry (in memory, no files changed)')

if __name__ == '__main__':
    if '--self-test' in sys.argv:
        self_test()
    else:
        errors = check()
        for error in errors:
            print('ERROR:', error)
        print(f'Document validation: {len(errors)} errors')
        sys.exit(bool(errors))
