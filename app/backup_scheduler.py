# app/backup_scheduler.py
"""
Scheduler pentru backup-uri automate zilnice ale bazei de date
Rulează ca proces în fundal și creează backup-uri la ora specificată
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
from services.backup_service import BackupService
import os
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()

# Configurare logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def perform_daily_backup():
    """Funcție care execută backup-ul zilnic"""
    logger.info("=" * 60)
    logger.info("Începe backup-ul zilnic automat")
    logger.info("=" * 60)
    
    try:
        backup_service = BackupService()
        
        # Creează backup cu nume descriptiv
        backup_name = f"daily_auto"
        success, message, backup_path = backup_service.create_backup(backup_name)
        
        if success:
            logger.info(f"✅ {message}")
            
            # Afișează statistici
            stats = backup_service.get_backup_stats()
            logger.info(f"📊 Statistici backup-uri:")
            logger.info(f"   - Total backup-uri: {stats['total_backups']}")
            logger.info(f"   - Spațiu total: {stats['total_size_mb']:.2f} MB")
            if stats['newest_backup']:
                logger.info(f"   - Cel mai recent: {stats['newest_backup'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.error(f"❌ {message}")
            
    except Exception as e:
        logger.error(f"❌ Eroare critică la backup: {str(e)}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("Backup zilnic finalizat")
    logger.info("=" * 60)
    logger.info("")


def run_scheduler():
    """Pornește scheduler-ul pentru backup-uri automate"""
    
    # Obține ora pentru backup din variabilele de mediu (implicit 02:00)
    backup_time = os.getenv("BACKUP_TIME", "02:00")
    
    logger.info("🚀 Backup Scheduler pornit")
    logger.info(f"⏰ Backup-uri programate zilnic la ora: {backup_time}")
    logger.info(f"📁 Director backup-uri: {Path('backups').absolute()}")
    logger.info(f"🗄️  Bază de date: {os.getenv('DB_NAME', 'copy_top_db')}")
    logger.info("")
    
    # Programează backup zilnic
    schedule.every().day.at(backup_time).do(perform_daily_backup)
    
    # Opțional: Creează un backup imediat la pornire (pentru testare)
    if os.getenv("BACKUP_ON_START", "false").lower() == "true":
        logger.info("🔄 Creează backup inițial la pornire...")
        perform_daily_backup()
    
    # Loop principal
    logger.info("⏳ Aștept următorul backup programat...")
    logger.info("")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifică la fiecare minut
    except KeyboardInterrupt:
        logger.info("⏹️  Scheduler oprit de utilizator")
    except Exception as e:
        logger.error(f"❌ Eroare în scheduler: {str(e)}", exc_info=True)


if __name__ == "__main__":
    run_scheduler()
