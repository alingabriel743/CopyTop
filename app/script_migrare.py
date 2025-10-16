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

def migrate_hartie_table_v4(cursor):
    """Adaugă câmpul cod_certificare în tabela hartie"""
    logger.info("🔄 Migrare tabelă 'hartie' - V4...")
    
    # Adaugă coloana cod_certificare
    if not check_column_exists(cursor, 'hartie', 'cod_certificare'):
        cursor.execute("ALTER TABLE hartie ADD COLUMN cod_certificare VARCHAR(100)")
        logger.info("✅ Adăugată coloana 'cod_certificare'")

def migrate_comenzi_table_v4(cursor):
    """Adaugă câmpurile nr_factura și data_facturare în tabela comenzi"""
    logger.info("🔄 Migrare tabelă 'comenzi' - V4...")
    
    # Adaugă coloana nr_factura
    if not check_column_exists(cursor, 'comenzi', 'nr_factura'):
        cursor.execute("ALTER TABLE comenzi ADD COLUMN nr_factura VARCHAR(50)")
        logger.info("✅ Adăugată coloana 'nr_factura'")
    
    # Adaugă coloana data_facturare
    if not check_column_exists(cursor, 'comenzi', 'data_facturare'):
        cursor.execute("ALTER TABLE comenzi ADD COLUMN data_facturare DATE")
        logger.info("✅ Adăugată coloana 'data_facturare'")

def migrate_comenzi_table_v5(cursor):
    """Adaugă câmpul stare în tabela comenzi pentru gestionarea stărilor comenzilor"""
    logger.info("🔄 Migrare tabelă 'comenzi' - V5...")
    
    # Adaugă coloana stare
    if not check_column_exists(cursor, 'comenzi', 'stare'):
        cursor.execute("ALTER TABLE comenzi ADD COLUMN stare VARCHAR(20) DEFAULT 'In lucru' NOT NULL")
        logger.info("✅ Adăugată coloana 'stare'")
        
        # Actualizează starea comenzilor existente bazat pe câmpul facturata
        cursor.execute("""
            UPDATE comenzi 
            SET stare = CASE 
                WHEN facturata = TRUE THEN 'Facturată'
                ELSE 'In lucru'
            END
        """)
        logger.info("✅ Actualizate stările comenzilor existente bazat pe status facturare")

def migrate_stoc_table_v6(cursor):
    """Adaugă câmpul cod_certificare în tabela stoc pentru intrările de hârtie"""
    logger.info("🔄 Migrare tabelă 'stoc' - V6...")
    
    # Adaugă coloana cod_certificare
    if not check_column_exists(cursor, 'stoc', 'cod_certificare'):
        cursor.execute("ALTER TABLE stoc ADD COLUMN cod_certificare VARCHAR(100)")
        logger.info("✅ Adăugată coloana 'cod_certificare' în tabela stoc")

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
            v3_applied = cursor.fetchone() is not None
            if v3_applied:
                logger.info("✅ Migrarea v3.0 a fost deja aplicată")
                
        except Exception as e:
            logger.warning(f"⚠️ Eroare la verificarea istoricului: {e}")
        
        # Aplicare migrări v3 (doar dacă nu a fost aplicată)
        if not v3_applied:
            migrate_comenzi_table_v3(cursor)
            migrate_stoc_table_v3(cursor)
            
            # Înregistrează migrarea v3
            cursor.execute("""
                INSERT INTO migration_history (version, description) 
                VALUES ('v3.0', 'Adăugare nr_pagini_pe_coala și furnizor conform cerințe noi')
            """)
            logger.info("📝 Migrarea v3.0 înregistrată în istoric")
        
        # Verifică dacă migrarea v4 a fost deja aplicată
        cursor.execute("SELECT version FROM migration_history WHERE version = 'v4.0'")
        if not cursor.fetchone():
            logger.info("🔄 Aplicare migrare v4.0...")
            
            # Aplicare migrări v4
            migrate_hartie_table_v4(cursor)
            migrate_comenzi_table_v4(cursor)
            
            # Înregistrează migrarea v4
            cursor.execute("""
                INSERT INTO migration_history (version, description) 
                VALUES ('v4.0', 'Adăugare cod_certificare la hartie și nr_factura/data_facturare la comenzi')
            """)
            logger.info("📝 Migrarea v4.0 înregistrată în istoric")
            logger.info("🎉 Migrarea v4.0 s-a finalizat cu succes!")
        else:
            logger.info("✅ Migrarea v4.0 a fost deja aplicată")
        
        # Verifică dacă migrarea v5 a fost deja aplicată
        cursor.execute("SELECT version FROM migration_history WHERE version = 'v5.0'")
        if not cursor.fetchone():
            logger.info("🔄 Aplicare migrare v5.0...")
            
            # Aplicare migrări v5
            migrate_comenzi_table_v5(cursor)
            
            # Înregistrează migrarea v5
            cursor.execute("""
                INSERT INTO migration_history (version, description) 
                VALUES ('v5.0', 'Adăugare câmp stare pentru gestionarea stărilor comenzilor (In lucru, Finalizată, Facturată)')
            """)
            logger.info("📝 Migrarea v5.0 înregistrată în istoric")
            logger.info("🎉 Migrarea v5.0 s-a finalizat cu succes!")
        else:
            logger.info("✅ Migrarea v5.0 a fost deja aplicată")
        
        # Verifică dacă migrarea v6 a fost deja aplicată
        cursor.execute("SELECT version FROM migration_history WHERE version = 'v6.0'")
        if not cursor.fetchone():
            logger.info("🔄 Aplicare migrare v6.0...")
            
            # Aplicare migrări v6
            migrate_stoc_table_v6(cursor)
            
            # Înregistrează migrarea v6
            cursor.execute("""
                INSERT INTO migration_history (version, description) 
                VALUES ('v6.0', 'Adăugare câmp cod_certificare în tabela stoc pentru intrările lunare de hârtie')
            """)
            logger.info("📝 Migrarea v6.0 înregistrată în istoric")
            logger.info("🎉 Migrarea v6.0 s-a finalizat cu succes!")
        else:
            logger.info("✅ Migrarea v6.0 a fost deja aplicată")
        
        logger.info("🎉 Toate migrările s-au finalizat cu succes!")
        
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
