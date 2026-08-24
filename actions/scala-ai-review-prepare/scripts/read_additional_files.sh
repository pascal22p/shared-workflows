set -euo pipefail

mkdir -p review-context/additional

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
  | grep -E '^(build\.sbt|project/[^/]+|doc/[^/]+|conf/[^/]+)$' \
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
    "review-context/additional/${file}" \
    "[FILE DID NOT EXIST]"

done < "$additional_files"

rm -f "$changed_files" "$additional_files"