"""Quick dry-run: test ingest + rubric against real repos (no LLM needed)."""

import sys
sys.path.insert(0, ".")

from src.nodes.ingest_repos import ingest_repos_node
from src.nodes.evaluate_rubric import evaluate_rubric_node

state = {
    "repos_dir": r"D:\repos\devops",
    "scope": "all",
    "repo_files": {},
    "rubric_results": {},
}

print("=" * 60)
print("  DRY RUN: Ingest + Rubric (no LLM)")
print("=" * 60)

state = ingest_repos_node(state)
print(f"\nFound {len(state['repo_files'])} repos")
for repo, files in state["repo_files"].items():
    print(f"  {repo}: {len(files)} files")

print()
state = evaluate_rubric_node(state)

print("\n" + "=" * 60)
print("  RUBRIC RESULTS SUMMARY")
print("=" * 60)

for repo, results in state["rubric_results"].items():
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warned = sum(1 for r in results if r["status"] == "WARN")
    print(f"\n{'─' * 50}")
    print(f"  {repo}  ✅{passed}  ❌{failed}  ⚠️{warned}")
    print(f"{'─' * 50}")
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌" if r["status"] == "FAIL" else "⚠️"
        print(f"  {icon} [{r['id']}] {r['title']}")
        if r["status"] != "PASS":
            print(f"       └─ {r['evidence'][:120]}")
