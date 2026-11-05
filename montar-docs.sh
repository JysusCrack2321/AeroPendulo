#!/usr/bin/env bash
# Monta la carpeta del proyecto del vault Obsidian como docs/ del repo.
# Ejecutar tras cada reinicio:  ~/Proyectos/AeroPendulo/montar-docs.sh
set -e
ORIGEN="/home/jysusman/My-obsidian-vault/Universidad 2026-2/Tecnicas de contro/proyecto"
DESTINO="/home/jysusman/Proyectos/AeroPendulo/docs"

if findmnt -q "$DESTINO"; then
  echo "ya montado en $DESTINO"
  exit 0
fi
sudo mount --bind "$ORIGEN" "$DESTINO"
findmnt "$DESTINO"
