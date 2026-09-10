set -euo pipefail

CONTEXT_DIR="review-context"
REPOSITORY=""
BASE_SHA=""
HEAD_SHA=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repository)
      REPOSITORY="$2"
      shift 2
      ;;
    --base-sha)
      BASE_SHA="$2"
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

if [ -z "$REPOSITORY" ] || [ -z "$BASE_SHA" ] || [ -z "$HEAD_SHA" ]; then
  echo "Missing required arguments: --repository, --base-sha, --head-sha" >&2
  exit 1
fi

mkdir -p "${CONTEXT_DIR}/before"
mkdir -p "${CONTEXT_DIR}/after"

fetch_file() {
  local file="$1"
  local sha="$2"
  local output="$3"
  local missing_message="$4"

  local response="/tmp/file.json"
  local decoded="/tmp/file.content"

  mkdir -p "$(dirname "$output")"

  if ! gh api \
    "repos/${REPOSITORY}/contents/${file}?ref=${sha}" \
    > "$response" 2>/dev/null; then

    echo "$missing_message" > "$output"
    return
  fi

  if ! jq -e '.content' "$response" >/dev/null 2>&1; then
    echo "$missing_message" > "$output"
    return
  fi

  jq -r '.content' "$response" \
    | tr -d '\n' \
    | base64 -d \
    > "$decoded"

  # Ignore binary files.
  if file --brief --mime-encoding "$decoded" | grep -q '^binary$'; then
    echo "[BINARY FILE]" > "$output"
    return
  fi

  cp "$decoded" "$output"
}

jq -r '.[].filename' pr-files.json \
  | sort -u \
  > /tmp/changed-files.txt

while IFS= read -r file; do

  [ -z "$file" ] && continue

  echo "Reading ${file}"

  fetch_file \
    "$file" \
    "$BASE_SHA" \
    "${CONTEXT_DIR}/before/${file}" \
    "[FILE DID NOT EXIST AT BASE]"

  fetch_file \
    "$file" \
    "$HEAD_SHA" \
    "${CONTEXT_DIR}/after/${file}" \
    "[FILE DELETED BY PR]"

done < /tmp/changed-files.txt

rm -f /tmp/changed-files.txt