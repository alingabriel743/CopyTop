#!/bin/bash

# Script pentru backup complet al aplicației CopyTop
# Creat: 30/10/2025

# Culori pentru output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Backup Aplicație CopyTop${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Backup baza de date SQLite
echo -e "${GREEN}[1/4] Backup bază de date...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "copytop.db" ]; then
    cp copytop.db "$BACKUP_DIR/copytop_backup.db"
    echo "✅ Baza de date salvată în: $BACKUP_DIR/copytop_backup.db"
else
    echo -e "${RED}⚠️  Baza de date nu a fost găsită!${NC}"
fi

# 2. Backup fișiere statice (PDF-uri generate, etc.)
echo -e "${GREEN}[2/4] Backup fișiere statice...${NC}"
if [ -d "app/app/static" ]; then
    cp -r app/app/static "$BACKUP_DIR/static"
    echo "✅ Fișiere statice salvate"
else
    echo "ℹ️  Nu există fișiere statice de salvat"
fi

# 3. Commit Git (dacă există modificări)
echo -e "${GREEN}[3/4] Commit modificări în Git...${NC}"
git add .
if git diff --staged --quiet; then
    echo "ℹ️  Nu există modificări de commit"
else
    git commit -m "Backup automat - $(date +%Y-%m-%d\ %H:%M:%S)"
    echo "✅ Modificări commit-ate în Git"
fi

# 4. Push la GitHub (opțional - decomentează dacă vrei push automat)
# echo -e "${GREEN}[4/4] Push la GitHub...${NC}"
# git push origin main
# echo "✅ Modificări push-ate la GitHub"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Backup complet finalizat!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "📁 Locație backup: $BACKUP_DIR"
echo "📊 Bază de date: $BACKUP_DIR/copytop_backup.db"
echo ""
echo "💡 Pentru a restaura backup-ul:"
echo "   cp $BACKUP_DIR/copytop_backup.db copytop.db"
echo ""
