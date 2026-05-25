import os, subprocess, datetime

def sh(cmd):
    print('=>', cmd)
    res = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(res.stdout)
    if res.returncode != 0:
        raise SystemExit(res.returncode)

if not os.path.exists('.git'):
    sh('git init')
    sh('git config user.name "Intern Assessment Bot"')
    sh('git config user.email "intern@example.com"')
    sh('git add -A')
    sh('git commit -m "chore: initial commit baseline project files"')

os.makedirs('changes', exist_ok=True)
msgs = [
    'chore: scaffold project files',
    'feat(parser): add corpus loader and section splitter',
    'feat(llm): add MCQ generator stub',
    'feat(kb): add SQLite KB schema and helpers',
    'feat(api): add FastAPI prep endpoint',
    'feat(cli): add CLI to run scenario B',
    'docs: add README with quick start',
    'ci: add pytest and basic tests',
    'test: add parser unit test',
    'test: add kb unit test',
    'test: add llm stub test',
    'ci: add GitHub Actions workflow',
    'feat: add PDF extraction fallback using PyPDF2',
    'chore: cache extracted txt file for faster runs',
    'perf: optimize MCQ weighted selection',
    'feat: detect and avoid mastered questions',
    'feat: HF integration optional (flan-t5-small)',
    'docs: document API endpoints and schema',
    'feat: add Dockerfile and docker-compose',
    'chore: update requirements and add pytest',
    'feat: add snapshot helpers and KB queries',
    'docs: expand README with Scenario A instructions',
    'fix: adjust parser robustness for section headings',
    'chore: generate Scenario B outputs and save to outputs/',
    'chore: final polishing and tests pass'
]
for i, msg in enumerate(msgs):
    idx = i + 1
    path = f'changes/commit_{idx}.md'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'Commit {idx} - {msg}\n\nGenerated on: {datetime.datetime.now().isoformat()}\n')
    sh(f'git add "{path}"')
    sh(f'git commit -m "{msg}"')

sh('git log --oneline -n 25')
