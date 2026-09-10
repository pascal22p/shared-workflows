set -euo pipefail

CONTEXT_DIR="review-context"
REPOSITORY=""
HEAD_SHA=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repository)
      REPOSITORY="$2"
      shift 2
      ;;
    --head-sha)
      HEAD_SHA="$2"
      shift 2
      ;;
    --context-dir)
      CONTEXT_DIR="$2"
      shift 2
      ;;
    --github-token)
      export GH_TOKEN="$2"
      export GITHUB_TOKEN="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [ -z "$REPOSITORY" ] || [ -z "$HEAD_SHA" ]; then
  echo "Missing required arguments: --repository, --head-sha" >&2
  exit 1
fi

mkdir -p "${CONTEXT_DIR}/additional"

fetch_file() {
  local file="$1"
  local sha="$2"
  local output="$3"
  local missing_message="$4"

  local response
  local decoded

  response=$(mktemp)
  decoded=$(mktemp)

  mkdir -p "$(dirname "$output")"

  if ! gh api \
    "repos/${REPOSITORY}/contents/${file}?ref=${sha}" \
    > "$response" 2>/dev/null; then

    echo "$missing_message" > "$output"
    rm -f "$response" "$decoded"
    return
  fi

  if ! jq -e '.content' "$response" >/dev/null 2>&1; then
    echo "$missing_message" > "$output"
    rm -f "$response" "$decoded"
    return
  fi

  jq -r '.content' "$response" \
    | tr -d '\n' \
    | base64 -d \
    > "$decoded"

  # Ignore binary files.
  if file --brief --mime-encoding "$decoded" | grep -q '^binary$'; then
    echo "[BINARY FILE]" > "$output"
    rm -f "$response" "$decoded"
    return
  fi

  cp "$decoded" "$output"

  rm -f "$response" "$decoded"
}

changed_files=$(mktemp)
additional_files=$(mktemp)

jq -r '.[].filename' pr-files.json \
  | sort -u \
  > "$changed_files"

gh api "repos/${REPOSITORY}/git/trees/${HEAD_SHA}?recursive=1" \
  --jq '.tree[].path' \
  | grep -E '^(project/[^/]+|doc/[^/]+|conf/[^/]+)$' \
  | grep -v '^conf/logback\.xml$' \
  | sort -u \
  > "$additional_files" || true

while IFS= read -r file; do

  [ -z "$file" ] && continue

  if grep -Fxq "$file" "$changed_files"; then
    continue
  fi

  echo "Reading ${file}"

  fetch_file \
    "$file" \
    "$HEAD_SHA" \
    "${CONTEXT_DIR}/additional/${file}" \
    "[FILE DID NOT EXIST]"

done < "$additional_files"

rm -f "$changed_files" "$additional_files"