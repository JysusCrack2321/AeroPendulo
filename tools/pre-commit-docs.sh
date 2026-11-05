#!/usr/bin/env bash
# Hook pre-commit: evita commitear la desaparicion de docs/ cuando el bind mount
# al vault no esta activo (esa fue la causa de que se borraran las notas).
set -e
DESTINO="$(git rev-parse --show-toplevel)/docs"

if ! mountpoint -q "$DESTINO"; then
  # solo bloquea si el commit tocaria archivos de docs
  if git diff --cached --name-only | grep -q '^docs/'; then
    echo "pre-commit: docs/ NO esta montado y hay cambios en docs/." >&2
    echo "  Corre: ~/Proyectos/AeroPendulo/montar-docs.sh" >&2
    echo "  Si de verdad quieres commitear eso: git commit --no-verify" >&2
    exit 1
  fi
fi
exit 0
