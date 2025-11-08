# app/services/backup_service.py
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import logging
from typing import Optional, List, Tuple
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupService:
    """Serviciu pentru gestionarea backup-urilor bazei de date PostgreSQL"""
    
    def __init__(self):
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "parola")
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "copy_top_db")
        
        # Director pentru backup-uri
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Număr maxim de backup-uri de păstrat
        self.max_backups = int(os.getenv("MAX_BACKUPS", "30"))
        
        # Autodetectează pg_dump și psql (funcționează pe Windows, macOS, Linux)
        self.pg_dump_path = self._find_postgres_tool("pg_dump")
        self.psql_path = self._find_postgres_tool("psql")
        
        logger.info(f"Folosesc pg_dump: {self.pg_dump_path}")
        logger.info(f"Folosesc psql: {self.psql_path}")
    
    def _find_postgres_tool(self, tool_name: str) -> str:
        """
        Găsește automat calea către utilitarul PostgreSQL
        Funcționează pe Windows, macOS și Linux
        
        Args:
            tool_name: Numele utilitarului (pg_dump sau psql)
        
        Returns:
            str: Calea către utilitar
        """
        import platform
        
        # 1. Verifică dacă este setat manual în .env
        env_var = f"{tool_name.upper().replace('-', '_')}_PATH"
        if os.getenv(env_var):
            path = os.getenv(env_var)
            if Path(path).exists():
                return path
        
        # 2. Caută în locații comune bazate pe sistem de operare
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Postgres.app
            if os.path.exists("/Applications/Postgres.app"):
                for version in ["latest", "18", "17", "16", "15", "14"]:
                    path = f"/Applications/Postgres.app/Contents/Versions/{version}/bin/{tool_name}"
                    if Path(path).exists():
                        return path
        
        elif system == "Windows":
            # Locații comune PostgreSQL pe Windows
            program_files = [
                os.environ.get("ProgramFiles", "C:\\Program Files"),
                os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            ]
            
            for pf in program_files:
                # Caută în toate versiunile PostgreSQL instalate
                postgres_base = Path(pf) / "PostgreSQL"
                if postgres_base.exists():
                    for version_dir in sorted(postgres_base.glob("*"), reverse=True):
                        tool_path = version_dir / "bin" / f"{tool_name}.exe"
                        if tool_path.exists():
                            return str(tool_path)
        
        # 3. Încearcă să găsească în PATH folosind 'which' (Unix) sau 'where' (Windows)
        try:
            if system == "Windows":
                result = subprocess.run(
                    ['where', tool_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ['which', tool_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]  # Prima linie
        except:
            pass
        
        # 4. Fallback - returnează numele simplu
        return tool_name
    
    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str, Optional[Path]]:
        """
        Creează un backup al bazei de date PostgreSQL
        
        Args:
            backup_name: Nume personalizat pentru backup (opțional)
        
        Returns:
            Tuple[bool, str, Optional[Path]]: (success, message, backup_path)
        """
        try:
            # Generează nume backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                filename = f"{backup_name}_{timestamp}.sql"
            else:
                filename = f"backup_{timestamp}.sql"
            
            backup_path = self.backup_dir / filename
            
            # Setează variabila de mediu pentru parolă
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Comandă pg_dump pentru backup (folosește calea detectată automat)
            cmd = [
                self.pg_dump_path,
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-F', 'p',  # Plain text format
                '-f', str(backup_path),
                '--no-owner',
                '--no-acl',
                '--no-privileges'
            ]
            
            # Adaugă flag pentru a ignora diferențele de versiune (dacă este disponibil)
            # Acest lucru permite backup-uri chiar dacă versiunile nu se potrivesc exact
            env['PGOPTIONS'] = '-c client_min_messages=warning'
            
            # Execută backup
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Comprimă backup-ul
                compressed_path = self.compress_backup(backup_path)
                
                # Șterge fișierul necomprimat
                if compressed_path and backup_path.exists():
                    backup_path.unlink()
                    final_path = compressed_path
                else:
                    final_path = backup_path
                
                # Curăță backup-uri vechi
                self.cleanup_old_backups()
                
                size_mb = final_path.stat().st_size / (1024 * 1024)
                logger.info(f"Backup creat cu succes: {final_path} ({size_mb:.2f} MB)")
                return True, f"Backup creat cu succes: {final_path.name} ({size_mb:.2f} MB)", final_path
            else:
                error_msg = f"Eroare la crearea backup-ului: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg, None
                
        except subprocess.TimeoutExpired:
            error_msg = "Timeout: Backup-ul a durat prea mult timp"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Eroare neașteptată: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def compress_backup(self, backup_path: Path) -> Optional[Path]:
        """
        Comprimă fișierul de backup folosind gzip
        
        Args:
            backup_path: Calea către fișierul de backup
        
        Returns:
            Optional[Path]: Calea către fișierul comprimat sau None dacă a eșuat
        """
        try:
            import gzip
            
            compressed_path = backup_path.with_suffix('.sql.gz')
            
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Backup comprimat: {compressed_path}")
            return compressed_path
        except Exception as e:
            logger.error(f"Eroare la comprimarea backup-ului: {e}")
            return None
    
    def restore_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Restaurează baza de date dintr-un backup
        
        Args:
            backup_path: Calea către fișierul de backup
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Verifică dacă fișierul există
            if not backup_path.exists():
                return False, f"Fișierul de backup nu există: {backup_path}"
            
            # Decomprimă dacă este necesar
            if backup_path.suffix == '.gz':
                import gzip
                temp_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = temp_path
                cleanup_temp = True
            else:
                sql_file = backup_path
                cleanup_temp = False
            
            # Setează variabila de mediu pentru parolă
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Comandă psql pentru restore (folosește calea detectată automat)
            cmd = [
                self.psql_path,
                '-h', self.db_host,
                '-p', self.db_port,
                '-U', self.db_user,
                '-d', self.db_name,
                '-f', str(sql_file)
            ]
            
            # Execută restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Curăță fișierul temporar
            if cleanup_temp and sql_file.exists():
                sql_file.unlink()
            
            if result.returncode == 0:
                logger.info(f"Backup restaurat cu succes din: {backup_path}")
                return True, f"Backup restaurat cu succes din: {backup_path.name}"
            else:
                error_msg = f"Eroare la restaurarea backup-ului: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Eroare neașteptată: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_backups(self) -> List[dict]:
        """
        Listează toate backup-urile disponibile
        
        Returns:
            List[dict]: Lista cu informații despre backup-uri
        """
        backups = []
        
        for file in sorted(self.backup_dir.glob("*.sql*"), reverse=True):
            try:
                stat = file.stat()
                backups.append({
                    'name': file.name,
                    'path': file,
                    'size': stat.st_size,
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                })
            except Exception as e:
                logger.error(f"Eroare la citirea informațiilor pentru {file}: {e}")
        
        return backups
    
    def cleanup_old_backups(self) -> int:
        """
        Șterge backup-urile mai vechi decât limita setată
        
        Returns:
            int: Numărul de backup-uri șterse
        """
        backups = self.list_backups()
        deleted_count = 0
        
        if len(backups) > self.max_backups:
            # Păstrează doar cele mai recente max_backups backup-uri
            for backup in backups[self.max_backups:]:
                try:
                    backup['path'].unlink()
                    deleted_count += 1
                    logger.info(f"Backup vechi șters: {backup['name']}")
                except Exception as e:
                    logger.error(f"Eroare la ștergerea backup-ului {backup['name']}: {e}")
        
        return deleted_count
    
    def delete_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Șterge un backup specific
        
        Args:
            backup_path: Calea către backup-ul de șters
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Backup șters: {backup_path}")
                return True, f"Backup șters cu succes: {backup_path.name}"
            else:
                return False, "Backup-ul nu există"
        except Exception as e:
            error_msg = f"Eroare la ștergerea backup-ului: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_backup_stats(self) -> dict:
        """
        Obține statistici despre backup-uri
        
        Returns:
            dict: Statistici despre backup-uri
        """
        backups = self.list_backups()
        
        if not backups:
            return {
                'total_backups': 0,
                'total_size_mb': 0,
                'oldest_backup': None,
                'newest_backup': None
            }
        
        total_size = sum(b['size'] for b in backups)
        
        return {
            'total_backups': len(backups),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_backup': backups[-1]['created'] if backups else None,
            'newest_backup': backups[0]['created'] if backups else None
        }
