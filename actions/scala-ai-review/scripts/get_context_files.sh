          set -euo pipefail

          gh api \
            --paginate \
            "repos/${REPOSITORY}/pulls/${PR_NUMBER}/files?per_page=100" \
            > pr-files.json

          jq -r '.[].filename' pr-files.json \
            > changed-files.txt

          # Resolve the PR head SHA so we read build config as of this PR,
          # not the default branch
          HEAD_SHA=$(gh api "repos/${REPOSITORY}/pulls/${PR_NUMBER}" --jq '.head.sha')

          # Always include build.sbt,  project/* and doc/* for additional context,
          # even if untouched in this PR
          gh api "repos/${REPOSITORY}/git/trees/${HEAD_SHA}?recursive=1" \
          --jq '.tree[].path' \
          | grep -E '^(build\.sbt|project/[^/]+|doc/[^/]+)$' \
          >> changed-files.txt || true

          sort -u -o changed-files.txt changed-files.txt

          echo "Changed files:"
          cat changed-files.txt
