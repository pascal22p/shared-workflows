set -euo pipefail

gh api \
  --paginate \
  "repos/${REPOSITORY}/pulls/${PR_NUMBER}/files?per_page=100" \
  > pr-files.json

# Files actually changed in the PR
jq -r '.[].filename' pr-files.json \
  | sort -u \
  > changed-files.txt

# Resolve the PR head SHA so we read build config as of this PR,
# not the default branch
HEAD_SHA=$(gh api "repos/${REPOSITORY}/pulls/${PR_NUMBER}" --jq '.head.sha')

# Candidate additional context files
gh api "repos/${REPOSITORY}/git/trees/${HEAD_SHA}?recursive=1" \
  --jq '.tree[].path' \
  | grep -E '^(build\.sbt|project/[^/]+|doc/[^/]+)$' \
  | sort -u \
  > additional-files-candidates.txt || true

# Additional files must not already be changed files
comm -23 \
  additional-files-candidates.txt \
  changed-files.txt \
  > additional-files.txt

rm -f additional-files-candidates.txt

echo "Changed files:"
cat changed-files.txt

echo
echo "Additional files:"
cat additional-files.txt