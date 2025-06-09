#!/bin/bash
WORKDIR=$(dirname "$0")
LOGFILE="${WORKDIR}/logs/cron.log"
MAX_LOG_SIZE=$((1 * 1024 * 1024)) 

if [ -f "$LOGFILE" ]; then
    filesize=$(stat -c%s "$LOGFILE")
    if [ "$filesize" -gt "$MAX_LOG_SIZE" ]; then
        > "$LOGFILE"  # Sobrescreve o arquivo, mantendo o mesmo inode
    fi
fi

echo "Executando script em $(date)" >> "$LOGFILE"
cd "$WORKDIR" || { echo "Erro ao entrar no diretório" >> "$LOGFILE"; exit 1; }

# Ativa o ambiente virtual
source "$WORKDIR/.venv/bin/activate"
python -m uv run --env-file "$WORKDIR/.env" main.py

echo "Finalizado em $(date)" >> "$LOGFILE"