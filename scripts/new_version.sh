#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <version>  (e.g. $0 0.8.0)"
  exit 1
fi

VERSION=$1
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."

sed -i "s/^version = \".*\"/version = \"$VERSION\"/" "$ROOT/pyproject.toml"

git -C "$ROOT" add pyproject.toml
git -C "$ROOT" commit -m "version $VERSION"
git -C "$ROOT" push

git -C "$ROOT" tag "v$VERSION"
git -C "$ROOT" push origin "v$VERSION"
