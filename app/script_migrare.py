# app/migrate_v3.py
"""
Script de migrare pentru actualizarea bazei de date Copy Top - Versiunea 3
Modificări conform cerințelor din Aplicatie Copy Top_2.docx
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

def migrate_comenzi_table_v3(cursor):
    """Adaugă câmpul nr_pagini_pe_coala în tabela comenzi"""
    logger.info("🔄 Migrare tabelă 'comenzi' - V3...")
    
    # Adaugă coloana nr_pagini_pe_coala
    if not check_column_exists(cursor, 'comenzi', 'nr_pagini_pe_coala'):
        cursor.execute("ALTER TABLE comenzi ADD COLUMN nr_pagini_pe_coala INTEGER DEFAULT 2 NOT NULL")
        logger.info("✅ Adăugată coloana 'nr_pagini_pe_coala'")
        
        # Migrează datele existente: ex_pe_coala devine nr_pagini_pe_coala
        if check_column_exists(cursor, 'comenzi', 'ex_pe_coala'):
            cursor.execute("""
                UPDATE comenzi 
                SET nr_pagini_pe_coala = CASE 
                    WHEN ex_pe_coala > 0 THEN ex_pe_coala * 2
                    ELSE 2
                END
            """)
            logger.info("✅ Migrate valorile din ex_pe_coala în nr_pagini_pe_coala")

def migrate_stoc_table_v3(cursor):
    """Adaugă câmpul furnizor în tabela stoc"""
    logger.info("🔄 Migrare tabelă 'stoc' - V3...")
    
    # Adaugă coloana furnizor
    if not check_column_exists(cursor, 'stoc', 'furnizor'):
        cursor.execute("ALTER TABLE stoc ADD COLUMN furnizor VARCHAR(100)")
        logger.info("✅ Adăugată coloana 'furnizor'")
        
        # Setează o valoare implicită pentru înregistrările existente
        cursor.execute("UPDATE stoc SET furnizor = 'Furnizor necunoscut' WHERE furnizor IS NULL")
        
        # Face câmpul obligatoriu după ce am completat valorile
        cursor.execute("ALTER TABLE stoc ALTER COLUMN furnizor SET NOT NULL")
        logger.info("✅ Câmpul 'furnizor' setat ca obligatoriu")

def main():
    """Funcția principală de migrare V3"""
    logger.info("🚀 Începe migrarea bazei de date Copy Top v3.0")
    
    try:
        # Conectare la baza de date
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Conectat la baza de date")
        
        # Verifică istoricul migrărilor
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # Verifică dacă migrarea v3 a fost deja aplicată
            cursor.execute("SELECT version FROM migration_history WHERE version = 'v3.0'")
            if cursor.fetchone():
                logger.info("✅ Migrarea v3.0 a fost deja aplicată")
                cursor.close()
                conn.close()
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Eroare la verificarea istoricului: {e}")
        
        # Aplicare migrări
        migrate_comenzi_table_v3(cursor)
        migrate_stoc_table_v3(cursor)
        
        # Înregistrează migrarea
        cursor.execute("""
            INSERT INTO migration_history (version, description) 
            VALUES ('v3.0', 'Adăugare nr_pagini_pe_coala și furnizor conform cerințe noi')
        """)
        logger.info("📝 Migrarea v3.0 înregistrată în istoric")
        
        logger.info("🎉 Migrarea v3.0 s-a finalizat cu succes!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Eroare în timpul migrării: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    success = main()
    if not success:
        logger.error("❌ Migrarea a eșuat!")
        sys.exit(1)
    else:
        logger.info("🎉 Migrarea completă!")
        sys.exit(0)