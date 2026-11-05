#!/usr/bin/env bash
# Deja permanente el montaje de docs/ (bind mount al vault) y lo verifica.
# Uso:  sudo ~/Proyectos/AeroPendulo/fstab-docs.sh
set -euo pipefail

ORIGEN="/home/jysusman/My-obsidian-vault/Universidad 2026-2/Tecnicas de contro/proyecto"
DESTINO="/home/jysusman/Proyectos/AeroPendulo/docs"
FSTAB="/etc/fstab"

# fstab(5): los espacios van escapados como \040, nunca como "\ "
ORIGEN_ESC="${ORIGEN// /\\040}"

if grep -qF "$DESTINO" "$FSTAB"; then
  echo "ya existe una entrada para $DESTINO en $FSTAB; no se toca"
  grep -F "$DESTINO" "$FSTAB"
  exit 0
fi

cp -a "$FSTAB" "${FSTAB}.bak.$(date +%Y%m%d%H%M%S)"
printf '%s\t%s\tnone\tbind,nofail,x-systemd.requires-mounts-for=/home\t0\t0\n' \
  "$ORIGEN_ESC" "$DESTINO" >> "$FSTAB"

echo "--- linea agregada ---"
tail -1 "$FSTAB"

systemctl daemon-reload
mountpoint -q "$DESTINO" || mount --bind "$ORIGEN" "$DESTINO"

echo "--- verificacion ---"
findmnt "$DESTINO"
ls "$DESTINO"
