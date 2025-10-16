"""
Script pentru resetarea bazei de date - șterge toate comenzile și hârtiile
ATENȚIE: Acest script va șterge TOATE datele din tabele!
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

def reset_database():
    """Șterge toate datele din tabele"""
    logger.info("🚀 Începe resetarea bazei de date...")
    
    try:
        conn = get_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("✅ Conectat la baza de date")
        
        # Confirmă acțiunea
        print("\n⚠️  ATENȚIE! Acest script va șterge TOATE datele din următoarele tabele:")
        print("   - comenzi")
        print("   - stoc")
        print("   - hartie")
        print("\nBeneficiarii NU vor fi șterși.\n")
        
        confirm = input("Ești sigur că vrei să continui? Scrie 'DA' pentru confirmare: ")
        
        if confirm != "DA":
            logger.info("❌ Operațiune anulată de utilizator")
            return False
        
        # Șterge comenzile (trebuie prima dată din cauza foreign key)
        logger.info("🗑️  Ștergere comenzi...")
        cursor.execute("DELETE FROM comenzi")
        comenzi_count = cursor.rowcount
        logger.info(f"✅ {comenzi_count} comenzi șterse")
        
        # Șterge intrările de stoc
        logger.info("🗑️  Ștergere intrări stoc...")
        cursor.execute("DELETE FROM stoc")
        stoc_count = cursor.rowcount
        logger.info(f"✅ {stoc_count} intrări stoc șterse")
        
        # Șterge hârtiile
        logger.info("🗑️  Ștergere hârtii...")
        cursor.execute("DELETE FROM hartie")
        hartie_count = cursor.rowcount
        logger.info(f"✅ {hartie_count} hârtii șterse")
        
        # Resetează secvențele (pentru ID-uri)
        logger.info("🔄 Resetare secvențe...")
        cursor.execute("ALTER SEQUENCE comenzi_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE stoc_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE hartie_id_seq RESTART WITH 1")
        logger.info("✅ Secvențe resetate")
        
        logger.info("🎉 Baza de date a fost resetată cu succes!")
        logger.info(f"📊 Rezumat: {comenzi_count} comenzi, {stoc_count} intrări stoc, {hartie_count} hârtii șterse")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Eroare în timpul resetării: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    success = reset_database()
    if not success:
        logger.error("❌ Resetarea a eșuat!")
        sys.exit(1)
    else:
        logger.info("🎉 Resetare completă!")
        sys.exit(0)
