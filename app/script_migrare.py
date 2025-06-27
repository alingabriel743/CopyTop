# app/migrate_db.py
"""
Script de migrare pentru actualizarea bazei de date Copy Top
Versiunea: v2.0 - Separarea certificării FSC și adăugarea câmpurilor noi
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
import logging

# Configurare logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_connection():
    """Obține conexiunea la baza de date"""
    return psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

def check_column_exists(cursor, table_name, column_name):
    """Verifică dacă o coloană există în tabelă"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        )
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def migrate_hartie_table(cursor):
    """Migrează tabela hartie - separă certificarea FSC"""
    logger.info("🔄 Migrare tabelă 'hartie'...")
    
    # 1. Adaugă noile coloane pentru FSC materie primă
    if not check_column_exists(cursor, 'hartie', 'fsc_materie_prima'):
        cursor.execute("ALTER TABLE hartie ADD COLUMN fsc_materie_prima BOOLEAN DEFAULT FALSE NOT NULL")
        logger.info("✅ Adăugată coloana 'fsc_materie_prima'")
    
    if not check_column_exists(cursor, 'hartie', 'cod_fsc_materie_prima'):
        cursor.execute("ALTER TABLE hartie ADD COLUMN cod_fsc_materie_prima VARCHAR(50)")
        logger.info("✅ Adăugată coloana 'cod_fsc_materie_prima'")
    
    if not check_column_exists(cursor, 'hartie', 'certificare_fsc_materie_prima'):
        cursor.execute("ALTER TABLE hartie ADD COLUMN certificare_fsc_materie_prima VARCHAR(50)")
        logger.info("✅ Adăugată coloana 'certificare_fsc_materie_prima'")
    
    # 2. Migrează datele existente de la vechile coloane FSC la cele noi
    try:
        # Verifică dacă există coloanele vechi
        old_cod_exists = check_column_exists(cursor, 'hartie', 'cod_fsc')
        old_cert_exists = check_column_exists(cursor, 'hartie', 'certificare_fsc')
        
        if old_cod_exists and old_cert_exists:
            # Migrează datele din coloanele vechi în cele noi
            cursor.execute("""
                UPDATE hartie 
                SET fsc_materie_prima = CASE 
                    WHEN cod_fsc IS NOT NULL AND cod_fsc != '' THEN TRUE 
                    ELSE FALSE 
                END,
                cod_fsc_materie_prima = CASE 
                    WHEN cod_fsc IS NOT NULL AND cod_fsc != '' THEN 
                        CASE 
                            WHEN cod_fsc LIKE 'FSC-C%' THEN 'P 2.1'  -- Mapping implicit pentru codurile vechi
                            ELSE 'P 2.1'
                        END
                    ELSE NULL 
                END,
                certificare_fsc_materie_prima = certificare_fsc
                WHERE cod_fsc IS NOT NULL OR certificare_fsc IS NOT NULL
            """)
            logger.info("✅ Migrate datele FSC din coloanele vechi în cele noi")
            
            # Șterge coloanele vechi după migrare
            cursor.execute("ALTER TABLE hartie DROP COLUMN IF EXISTS cod_fsc")
            cursor.execute("ALTER TABLE hartie DROP COLUMN IF EXISTS certificare_fsc")
            logger.info("✅ Șterse coloanele FSC vechi")
        
    except Exception as e:
        logger.warning(f"⚠️ Eroare la migrarea datelor FSC pentru hârtie: {e}")

def migrate_comenzi_table(cursor):
    """Migrează tabela comenzi - restructurează câmpurile"""
    logger.info("🔄 Migrare tabelă 'comenzi'...")
    
    # 1. Redenumește 'lucrare' în 'nume_lucrare' și mărește dimensiunea
    if check_column_exists(cursor, 'comenzi', 'lucrare') and not check_column_exists(cursor, 'comenzi', 'nume_lucrare'):
        cursor.execute("ALTER TABLE comenzi ADD COLUMN nume_lucrare VARCHAR(300)")
        cursor.execute("UPDATE comenzi SET nume_lucrare = lucrare")
        cursor.execute("ALTER TABLE comenzi ALTER COLUMN nume_lucrare SET NOT NULL")
        cursor.execute("ALTER TABLE comenzi DROP COLUMN lucrare")
        logger.info("✅ Redenumită 'lucrare' în 'nume_lucrare' cu dimensiune mărită")
    
    # 2. Face 'descriere_lucrare' opțională
    if check_column_exists(cursor, 'comenzi', 'descriere_lucrare'):
        cursor.execute("ALTER TABLE comenzi ALTER COLUMN descriere_lucrare DROP NOT NULL")
        logger.info("✅ 'descriere_lucrare' nu mai e obligatoriu")
    
    # 3. Adaugă câmpurile noi pentru calculul colilor
    new_columns = [
        ('ex_pe_coala', 'INTEGER DEFAULT 1 NOT NULL'),
        ('nr_coli_tipar', 'INTEGER'),
        ('coli_prisoase', 'INTEGER DEFAULT 0 NOT NULL'),
        ('total_coli', 'INTEGER')
    ]
    
    for column_name, column_def in new_columns:
        if not check_column_exists(cursor, 'comenzi', column_name):
            cursor.execute(f"ALTER TABLE comenzi ADD COLUMN {column_name} {column_def}")
            logger.info(f"✅ Adăugată coloana '{column_name}'")
    
    # 4. Adaugă câmpurile pentru certificarea FSC produs final
    fsc_columns = [
        ('certificare_fsc_produs', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('cod_fsc_produs', 'VARCHAR(50)'),
        ('tip_certificare_fsc_produs', 'VARCHAR(100)')
    ]
    
    for column_name, column_def in fsc_columns:
        if not check_column_exists(cursor, 'comenzi', column_name):
            cursor.execute(f"ALTER TABLE comenzi ADD COLUMN {column_name} {column_def}")
            logger.info(f"✅ Adăugată coloana '{column_name}'")
    
    # 4b. Adaugă câmpurile noi pentru opțiunile de finisare
    finisare_columns = [
        ('capsat', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('colturi_rotunde', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('perfor', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('spiralare', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('stantare', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('lipire', 'BOOLEAN DEFAULT FALSE NOT NULL'),
        ('codita_wobbler', 'BOOLEAN DEFAULT FALSE NOT NULL')
    ]
    
    for column_name, column_def in finisare_columns:
        if not check_column_exists(cursor, 'comenzi', column_name):
            cursor.execute(f"ALTER TABLE comenzi ADD COLUMN {column_name} {column_def}")
            logger.info(f"✅ Adăugată coloana de finisare '{column_name}'")
    
    # 5. Migrează datele FSC existente
    try:
        if check_column_exists(cursor, 'comenzi', 'fsc'):
            # Mapează datele vechi FSC la noua structură
            cursor.execute("""
                UPDATE comenzi 
                SET certificare_fsc_produs = COALESCE(fsc, FALSE),
                    cod_fsc_produs = CASE 
                        WHEN fsc = TRUE THEN 'P 8.4'  -- Default: Advertising materials
                        ELSE NULL 
                    END,
                    tip_certificare_fsc_produs = CASE 
                        WHEN fsc = TRUE THEN 'Advertising materials'
                        ELSE NULL 
                    END
            """)
            logger.info("✅ Migrate datele FSC din coloana veche 'fsc'")
            
            # Face coloana veche fsc să accepte NULL pentru compatibilitate
            try:
                cursor.execute("ALTER TABLE comenzi ALTER COLUMN fsc DROP NOT NULL")
                logger.info("✅ Coloana 'fsc' poate fi acum NULL pentru compatibilitate")
            except Exception as e:
                logger.warning(f"⚠️ Nu s-a putut modifica constraintul NOT NULL pentru 'fsc': {e}")
        
        # Verifică și populează pentru comenzile existente fără FSC
        cursor.execute("""
            UPDATE comenzi 
            SET certificare_fsc_produs = FALSE,
                fsc = FALSE
            WHERE certificare_fsc_produs IS NULL
        """)
        logger.info("✅ Setat valori default pentru comenzile fără FSC")
    
    except Exception as e:
        logger.warning(f"⚠️ Eroare la migrarea datelor FSC pentru comenzi: {e}")
    
    # 6. Calculează nr_coli_tipar pentru comenzile existente
    try:
        cursor.execute("""
            UPDATE comenzi 
            SET nr_coli_tipar = CEIL(tiraj::FLOAT / ex_pe_coala::FLOAT),
                total_coli = CEIL(tiraj::FLOAT / ex_pe_coala::FLOAT) + coli_prisoase
            WHERE nr_coli_tipar IS NULL AND tiraj > 0 AND ex_pe_coala > 0
        """)
        logger.info("✅ Calculat nr_coli_tipar și total_coli pentru comenzile existente")
    except Exception as e:
        logger.warning(f"⚠️ Eroare la calcularea colilor pentru comenzile existente: {e}")

def migrate_compatibility_views(cursor):
    """Creează view-uri pentru compatibilitate cu codul existent"""
    logger.info("🔄 Creare view-uri pentru compatibilitate...")
    
    # View pentru compatibilitate cu coloana 'lucrare'
    try:
        cursor.execute("""
            CREATE OR REPLACE VIEW comenzi_legacy AS 
            SELECT id, numar_comanda, echipament, data, beneficiar_id,
                   nume_lucrare AS lucrare,
                   po_client, tiraj, descriere_lucrare, latime, inaltime, 
                   nr_pagini, indice_corectie,
                   certificare_fsc_produs AS fsc,
                   cod_fsc_produs AS cod_fsc,
                   tip_certificare_fsc_produs AS certificare_fsc,
                   hartie_id, coala_tipar, nr_culori, nr_coli, coli_mari, greutate,
                   plastifiere, big, nr_biguri, laminare, format_laminare, 
                   numar_laminari, taiere_cutter, detalii_finisare, 
                   detalii_livrare, pret, facturata,
                   ex_pe_coala, nr_coli_tipar, coli_prisoase, total_coli
            FROM comenzi
        """)
        logger.info("✅ Creat view 'comenzi_legacy' pentru compatibilitate")
    except Exception as e:
        logger.warning(f"⚠️ Eroare la crearea view-ului de compatibilitate: {e}")

def backup_database():
    """Creează un backup al bazei de date înainte de migrare"""
    import subprocess
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_copy_top_{timestamp}.sql"
    
    # Încearcă să găsească pg_dump în locații comune pe Windows
    possible_paths = [
        "pg_dump",  # În PATH
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\12\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\14\bin\pg_dump.exe",
    ]
    
    pg_dump_path = None
    for path in possible_paths:
        try:
            if os.path.exists(path) or path == "pg_dump":
                # Testează dacă comanda funcționează
                test_result = subprocess.run([path, "--version"], 
                                           capture_output=True, text=True, timeout=5)
                if test_result.returncode == 0:
                    pg_dump_path = path
                    logger.info(f"✅ Găsit pg_dump la: {path}")
                    break
        except:
            continue
    
    if not pg_dump_path:
        logger.warning("⚠️ pg_dump nu a fost găsit. Încercând backup manual...")
        return backup_manual()
    
    try:
        cmd = [
            pg_dump_path,
            f"--host={DB_HOST}",
            f"--port={DB_PORT}",
            f"--username={DB_USER}",
            f"--dbname={DB_NAME}",
            f"--file={backup_file}",
            "--verbose"
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = DB_PASSWORD
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info(f"✅ Backup creat cu succes: {backup_file}")
            return backup_file
        else:
            logger.error(f"❌ Eroare la crearea backup-ului: {result.stderr}")
            logger.warning("⚠️ Încercând backup manual...")
            return backup_manual()
    except Exception as e:
        logger.error(f"❌ Eroare la backup: {e}")
        logger.warning("⚠️ Încercând backup manual...")
        return backup_manual()

def backup_manual():
    """Creează un backup manual prin SQL dacă pg_dump nu funcționează"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_manual_{timestamp}.txt"
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup manual Copy Top DB - {timestamp}\n")
            f.write("-- IMPORTANT: Acesta este un backup minimal. Folosește pg_dump pentru backup complet.\n\n")
            
            # Backup structură tabele
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            f.write("-- STRUCTURĂ TABELE:\n")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                f.write(f"\n-- Tabelă: {table_name}\n")
                for col in columns:
                    f.write(f"-- {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'}) default: {col[3]}\n")
            
            # Backup date importante
            important_tables = ['beneficiari', 'hartie', 'comenzi', 'stoc']
            for table_name in important_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    f.write(f"\n-- Date {table_name}: {count} înregistrări\n")
                    
                    if count > 0 and count < 1000:  # Backup doar pentru tabele mici
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                        rows = cursor.fetchall()
                        f.write(f"-- Primele 10 înregistrări din {table_name}:\n")
                        for row in rows:
                            f.write(f"-- {row}\n")
                except:
                    f.write(f"-- Eroare la backup {table_name}\n")
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Backup manual creat: {backup_file}")
        logger.warning("⚠️ ATENȚIE: Acesta este un backup minimal! Pentru siguranță maximă, rulează manual:")
        logger.warning(f"   pg_dump -h {DB_HOST} -U {DB_USER} -d {DB_NAME} > backup_complet.sql")
        
        return backup_file
        
    except Exception as e:
        logger.error(f"❌ Eroare la backup manual: {e}")
        return None

def main(skip_backup=False):
    """Funcția principală de migrare"""
    logger.info("🚀 Începe migrarea bazei de date Copy Top v2.0")
    
    backup_file = None
    if not skip_backup:
        # 1. Creează backup
        logger.info("📦 Creare backup...")
        backup_file = backup_database()
        if not backup_file:
            logger.error("❌ Nu s-a putut crea backup-ul.")
            logger.info("💡 Poți sări peste backup cu: python migrate_db.py --skip-backup")
            logger.info("💡 SAU creează manual un backup cu: pg_dump -h localhost -U postgres copy_top_db > backup.sql")
            return False
    else:
        logger.warning("⚠️ ATENȚIE: Migrarea rulează FĂRĂ backup!")
    
    try:
        # 2. Conectare la baza de date
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Conectat la baza de date")
        
        # 3. Verifică versiunea migrării
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            cursor.execute("SELECT version FROM migration_history WHERE version = 'v2.0'")
            migration_exists = cursor.fetchone()
            
            if migration_exists:
                logger.info("✅ Migrarea v2.0 a fost deja aplicată - verificăm completitudinea...")
                # Chiar dacă migrarea există, verificăm și adăugăm coloanele lipsă
            else:
                logger.info("🆕 Prima aplicare a migrării v2.0")
        except Exception as e:
            logger.warning(f"⚠️ Eroare la verificarea istoricului migrărilor: {e}")
            migration_exists = False
        
        # 4. Aplicare migrări
        migrate_hartie_table(cursor)
        migrate_comenzi_table(cursor)
        migrate_compatibility_views(cursor)
        
        # 5. Înregistrează migrarea în istoric (doar dacă nu există)
        if not migration_exists:
            cursor.execute("""
                INSERT INTO migration_history (version, description) 
                VALUES ('v2.0', 'Separarea certificării FSC și restructurarea câmpurilor pentru comenzi')
            """)
            logger.info("📝 Migrarea v2.0 înregistrată în istoric")
        else:
            logger.info("📝 Migrarea v2.0 deja înregistrată în istoric")
        
        logger.info("🎉 Migrarea s-a finalizat cu succes!")
        logger.info(f"📦 Backup disponibil în: {backup_file}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Eroare în timpul migrării: {e}")
        logger.info(f"📦 Poți restaura din backup: {backup_file}")
        return False

def rollback_migration():
    """Rollback pentru migrarea v2.0 (în caz de probleme)"""
    logger.info("🔄 Rollback migrare v2.0...")
    
    try:
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Restaurează coloanele vechi în hartie
        cursor.execute("ALTER TABLE hartie ADD COLUMN IF NOT EXISTS cod_fsc VARCHAR(50)")
        cursor.execute("ALTER TABLE hartie ADD COLUMN IF NOT EXISTS certificare_fsc VARCHAR(50)")
        
        # Copiază datele înapoi
        cursor.execute("""
            UPDATE hartie 
            SET cod_fsc = CASE 
                    WHEN fsc_materie_prima = TRUE THEN 'FSC-C008955'  -- Cod implicit
                    ELSE NULL 
                END,
                certificare_fsc = certificare_fsc_materie_prima
            WHERE fsc_materie_prima = TRUE
        """)
        
        # Șterge coloanele noi
        cursor.execute("ALTER TABLE hartie DROP COLUMN IF EXISTS fsc_materie_prima")
        cursor.execute("ALTER TABLE hartie DROP COLUMN IF EXISTS cod_fsc_materie_prima")
        cursor.execute("ALTER TABLE hartie DROP COLUMN IF EXISTS certificare_fsc_materie_prima")
        
        # Rollback pentru comenzi
        cursor.execute("ALTER TABLE comenzi ADD COLUMN IF NOT EXISTS lucrare VARCHAR(200)")
        cursor.execute("UPDATE comenzi SET lucrare = nume_lucrare WHERE lucrare IS NULL")
        cursor.execute("ALTER TABLE comenzi DROP COLUMN IF EXISTS nume_lucrare")
        
        # Șterge intrarea din istoric
        cursor.execute("DELETE FROM migration_history WHERE version = 'v2.0'")
        
        logger.info("✅ Rollback finalizat")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Eroare la rollback: {e}")

if __name__ == "__main__":
    import sys
    
    skip_backup = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--rollback":
            rollback_migration()
            sys.exit(0)
        elif sys.argv[1] == "--skip-backup":
            skip_backup = True
            logger.warning("⚠️ Modul fără backup activat!")
    
    success = main(skip_backup=skip_backup)
    if not success:
        logger.error("❌ Migrarea a eșuat. Verifică logurile și backup-ul.")
        sys.exit(1)
    else:
        logger.info("🎉 Migrarea completă!")
        sys.exit(1)
