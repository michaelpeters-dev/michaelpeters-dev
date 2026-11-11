#!/bin/sh
# Typeset card.tex twice, once per color scheme, and convert each PDF to an SVG
# of glyph outlines so it renders the same everywhere.
# Needs pdflatex (TinyTeX is enough) and pdftocairo (brew install poppler).
set -eu
cd "$(dirname "$0")"
PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

build() {   # build <name> <text color as RRGGBB>
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$tmp" \
    -jobname "$1" "\def\fg{$2}\input{card.tex}" >/dev/null
  pdftocairo -svg "$tmp/$1.pdf" "assets/$1.svg"
}

mkdir -p assets
build dark E6EDF3
build light 1F2328
