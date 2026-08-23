set -euo pipefail

mkdir -p review-context/before
mkdir -p review-context/after

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
    "review-context/before/${file}" \
    "[FILE DID NOT EXIST AT BASE]"

  fetch_file \
    "$file" \
    "$HEAD_SHA" \
    "review-context/after/${file}" \
    "[FILE DELETED BY PR]"

done < /tmp/changed-files.txt

rm -f /tmp/changed-files.txt