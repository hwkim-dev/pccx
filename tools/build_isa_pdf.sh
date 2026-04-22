#!/usr/bin/env bash
# Build the pccx v002 ISA Guidebook (main.tex) and drop the final PDF
# where the Furo site can serve it.
#
# Usage:
#   bash tools/build_isa_pdf.sh           # full build, place at _static/downloads/
#   bash tools/build_isa_pdf.sh --no-move # build only, leave main.pdf at repo root
#
# Idempotent; safe to re-run.  Two xelatex passes are required so the TOC
# picks up the final page numbers.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUT_DIR="_static/downloads"
OUT_NAME="pccx-isa-v002.pdf"
MOVE=1
for arg in "$@"; do
    case "$arg" in
        --no-move) MOVE=0 ;;
        *) echo "[build] unknown arg: $arg" >&2; exit 2 ;;
    esac
done

command -v xelatex >/dev/null || {
    echo "[build] xelatex not found.  Install TeX Live (e.g. sudo apt-get install texlive-xetex texlive-fonts-recommended)." >&2
    exit 1
}

run_pass() {
    local label="$1"
    echo "[build] $label — xelatex main.tex"
    if ! xelatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/xelatex.out 2>&1; then
        echo "[build] xelatex FAILED — dumping stdout + main.log" >&2
        cat /tmp/xelatex.out >&2 || true
        echo "--- main.log tail ---" >&2
        tail -80 main.log >&2 || true
        exit 1
    fi
}

run_pass "Pass 1/2"
run_pass "Pass 2/2 (TOC resolution)"

# Sanity check: no unresolved references or overfull hboxes that count as
# real errors. Warnings are tolerated.
if [[ ! -s main.pdf ]]; then
    echo "[build] main.pdf was not produced — see main.log" >&2
    exit 1
fi

if [[ "$MOVE" == "1" ]]; then
    mkdir -p "$OUT_DIR"
    mv main.pdf "$OUT_DIR/$OUT_NAME"
    echo "[build] Published: $OUT_DIR/$OUT_NAME"
else
    echo "[build] Output: main.pdf (left at repo root)"
fi

# Clean up the debris so the working tree stays tidy.  .gitignore already
# covers these but removing them immediately keeps `git status` readable.
rm -f main.aux main.log main.out main.toc main.lof main.lot \
      main.fls main.fdb_latexmk main.synctex.gz main.synctex \
      main.bcf main.run.xml main.blg main.bbl main.nav main.snm \
      main.vrb main.idx main.ilg main.ind main.xdv main.dvi

echo "[build] Done."
