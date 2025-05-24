# app/migrate_db.py
import psycopg2
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

def migrate_database():
    """
    Script pentru migrarea bazei de date cu noile coloane FSC
    """
    try:
        # Conectare la baza de date
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        
        cursor = conn.cursor()
        print("Conectat la baza de date cu succes!")
        
        # Lista de modificări pentru tabelul hartie
        hartie_migrations = [
            # Redenumește coloanele existente
            "ALTER TABLE hartie RENAME COLUMN cod_fsc TO cod_fsc_intrare;",
            "ALTER TABLE hartie RENAME COLUMN certificare_fsc TO certificare_fsc_intrare;",
            
            # Adaugă coloanele noi pentru FSC ieșire
            "ALTER TABLE hartie ADD COLUMN IF NOT EXISTS cod_fsc_iesire VARCHAR(50);",
            "ALTER TABLE hartie ADD COLUMN IF NOT EXISTS certificare_fsc_iesire VARCHAR(50);"
        ]
        
        # Lista de modificări pentru tabelul comenzi
        comenzi_migrations = [
            # Redenumește coloanele existente
            "ALTER TABLE comenzi RENAME COLUMN cod_fsc TO cod_fsc_output;",
            "ALTER TABLE comenzi RENAME COLUMN certificare_fsc TO certificare_fsc_output;",
            
            # Adaugă coloana pentru calea PDF
            "ALTER TABLE comenzi ADD COLUMN IF NOT EXISTS pdf_path VARCHAR(255);"
        ]
        
        print("Pornesc migrarea pentru tabelul 'hartie'...")
        
        # Execută migrările pentru hartie
        for migration in hartie_migrations:
            try:
                cursor.execute(migration)
                print(f"✅ Executat: {migration}")
            except psycopg2.errors.DuplicateColumn as e:
                print(f"⚠️  Coloana există deja: {migration}")
                conn.rollback()
                continue
            except psycopg2.errors.UndefinedColumn as e:
                print(f"⚠️  Coloana nu există pentru redenumire: {migration}")
                conn.rollback()
                continue
            except Exception as e:
                print(f"❌ Eroare la: {migration}")
                print(f"   Detalii: {e}")
                conn.rollback()
                continue
        
        print("Pornesc migrarea pentru tabelul 'comenzi'...")
        
        # Execută migrările pentru comenzi
        for migration in comenzi_migrations:
            try:
                cursor.execute(migration)
                print(f"✅ Executat: {migration}")
            except psycopg2.errors.DuplicateColumn as e:
                print(f"⚠️  Coloana există deja: {migration}")
                conn.rollback()
                continue
            except psycopg2.errors.UndefinedColumn as e:
                print(f"⚠️  Coloana nu există pentru redenumire: {migration}")
                conn.rollback()
                continue
            except Exception as e:
                print(f"❌ Eroare la: {migration}")
                print(f"   Detalii: {e}")
                conn.rollback()
                continue
        
        # Commit toate modificările
        conn.commit()
        print("🎉 Migrarea a fost completată cu succes!")
        
        # Verifică structura tabelelor
        print("\n📋 Verificare structură tabel 'hartie':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'hartie' 
            ORDER BY ordinal_position;
        """)
        
        hartie_columns = cursor.fetchall()
        for col in hartie_columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        print("\n📋 Verificare structură tabel 'comenzi':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'comenzi' 
            ORDER BY ordinal_position;
        """)
        
        comenzi_columns = cursor.fetchall()
        for col in comenzi_columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
    except Exception as e:
        print(f"❌ Eroare la conectarea la baza de date: {e}")
        if 'conn' in locals():
            conn.rollback()
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("🔐 Conexiunea la baza de date a fost închisă.")

if __name__ == "__main__":
    print("🚀 Pornesc migrarea bazei de date...")
    migrate_database()