#!/usr/bin/env python3
"""
Script pentru ștergerea intrărilor de hârtie din tabelul Stoc
ATENȚIE: Acest script șterge DOAR intrările de hârtie (tabelul Stoc)
NU șterge: beneficiarii, lista de hârtii, comenzile
"""

from models import get_session
from models.stoc import Stoc
from models.hartie import Hartie

def sterge_intrari_hartie():
    """Șterge toate intrările de hârtie din tabelul Stoc"""
    session = get_session()
    
    try:
        # Numără intrările înainte de ștergere
        nr_intrari = session.query(Stoc).count()
        
        if nr_intrari == 0:
            print("ℹ️  Nu există intrări de hârtie de șters.")
            return
        
        print(f"⚠️  Găsite {nr_intrari} intrări de hârtie în baza de date.")
        print(f"⚠️  Acest script va șterge TOATE intrările din tabelul Stoc.")
        print(f"✅ NU va șterge: beneficiarii, lista de hârtii, comenzile")
        print()
        
        # Confirmare
        confirmare = input("Ești sigur că vrei să continui? (scrie 'DA' pentru confirmare): ")
        
        if confirmare.upper() != "DA":
            print("❌ Operațiune anulată.")
            return
        
        # Șterge toate intrările din Stoc
        session.query(Stoc).delete()
        
        # IMPORTANT: Resetează stocul hârtiilor la 0
        # (deoarece intrările de stoc au fost șterse)
        print("\n📊 Resetare stoc hârtii la 0...")
        hartii = session.query(Hartie).all()
        for hartie in hartii:
            hartie.stoc = 0
            hartie.greutate = 0
        
        session.commit()
        
        print(f"\n✅ {nr_intrari} intrări de hârtie au fost șterse cu succes!")
        print(f"✅ Stocul tuturor hârtiilor a fost resetat la 0")
        print(f"✅ Beneficiarii și lista de hârtii au fost păstrate")
        print(f"✅ Comenzile au fost păstrate")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Eroare la ștergerea intrărilor: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  ȘTERGERE INTRĂRI HÂRTIE (Tabelul Stoc)")
    print("=" * 60)
    print()
    sterge_intrari_hartie()
    print()
    print("=" * 60)
