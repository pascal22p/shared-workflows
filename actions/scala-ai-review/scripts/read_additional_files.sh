set -euo pipefail

rm -rf review-context

mkdir -p review-context/additional

fetch_file() {
  local file="$1"
  local sha="$2"
  local output="$3"
  local missing_message="$4"

  local response="/tmp/file.json"
  local decoded="/tmp/file.content"

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

while IFS= read -r file; do

  [ -z "$file" ] && continue

  safe_name=$(echo "$file" | sed 's#[/ ]#__#g')

  echo "Reading ${file}"

  fetch_file \
    "$file" \
    "$BASE_SHA" \
    "review-context/additional/${safe_name}" \
    "[FILE DID NOT EXIST]"

done < additional-files.txt