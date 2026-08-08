from bot import wanted, gather_all_jobs

jobs = gather_all_jobs()
matching = [j for j in jobs if wanted(j)]

print(f"\nTotal jobs: {len(jobs)}")
print(f"Matching IT filter: {len(matching)}\n")

print("=== Jobs that MATCH the filter ===")
for j in matching:
    print(f"  ✓ {j['title']}  ({j['company']})")

print("\n=== A peek at ALL titles (to eyeball what's there) ===")
for j in jobs:
    mark = "✓" if wanted(j) else " "
    print(f"  [{mark}] {j['title']}")