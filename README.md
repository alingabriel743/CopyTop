# CopyTop

# CopyTop - Aplicație Management Tipografie

🖨️ **Aplicație web pentru gestionarea operațiunilor de tipografie dezvoltată cu Streamlit și PostgreSQL**

## 📋 **Funcționalități**

- ✅ **Gestiune Beneficiari** - Adăugare, editare, ștergere clienți
- ✅ **Gestiune Hârtie** - Sortimente, stocuri, coduri FSC separate pentru intrare/ieșire
- ✅ **Gestiune Stoc** - Intrări hârtie cu actualizare automată stocuri
- ✅ **Gestiune Comenzi** - Comenzi complete cu generare PDF automată
- ✅ **Facturare Protejată** - Secțiune cu parolă pentru facturare
- ✅ **Rapoarte PDF** - Rapoarte stoc și FSC cu export PDF/Excel
- ✅ **Compatibilitate Hârtie-Coală** - Matricea de compatibilitate din specificații

---

## 🚀 **Instalare Rapidă**

### **Cerințe Sistem**

- Windows 10/11, macOS sau Linux
- Python 3.8+ (recomandat Python 3.12)
- PostgreSQL 12+
- 4GB RAM minim

---

## 📥 **Pasul 1: Instalare Dependențe**

### **1.1 Instalare Python**

- Descarcă Python de la [python.org](https://www.python.org/downloads/)
- ✅ **IMPORTANT**: Bifează "Add Python to PATH" la instalare
- Verifică instalarea:

```bash
python --version
pip --version
```

### **1.2 Instalare PostgreSQL**

- Descarcă PostgreSQL de la [postgresql.org](https://www.postgresql.org/downloads/)
- Instalează cu setările implicite
- Reține parola pentru utilizatorul `postgres`
- Verifică instalarea:

```bash
psql --version
```

---

## 📂 **Pasul 2: Configurare Proiect**

### **2.1 Clonare/Descărcare Cod**

```bash
# Opțiunea 1: Clonare Git (dacă ai Git instalat)
git clone <URL_REPOSITORY>
cd CopyTop

# Opțiunea 2: Descarcă ZIP și extrage
# Navighează în folderul extras
cd CopyTop
```

### **2.2 Creare Virtual Environment**

```bash
# Creează mediul virtual
python -m venv venv

# Activează mediul virtual
# Pe Windows:
venv\Scripts\activate

# Pe macOS/Linux:
source venv/bin/activate

# Verifică activarea (vei vedea (venv) în prompt)
```

### **2.3 Instalare Pachete Python**

```bash
# Actualizează pip
pip install --upgrade pip

# Instalează dependențele
pip install -r requirements.txt

# Dacă apar erori cu psycopg2, încearcă:
pip install psycopg2-binary --force-reinstall
```

---

## 🗄️ **Pasul 3: Configurare Bază de Date**

### **3.1 Creare Bază de Date PostgreSQL**

```sql
-- Conectează-te la PostgreSQL ca administrator
psql -U postgres

-- Creează baza de date
CREATE DATABASE copy_top_db;

-- Creează utilizator (opțional)
CREATE USER copy_user WITH PASSWORD 'parola_sigura';
GRANT ALL PRIVILEGES ON DATABASE copy_top_db TO copy_user;

-- Ieși din psql
\q
```

### **3.2 Configurare Conexiune**

Creează fișierul `.env` în folderul principal:

```bash
# .env
DB_USER=postgres
DB_PASSWORD=parola_ta_postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=copy_top_db
SECRET_KEY=cheie_secreta_aplicatie_12345
DEBUG=True
```

### **3.3 Inițializare Structură Baza de Date**

```bash
# Navighează în folderul app
cd app

# Rulează scriptul de inițializare
python db_init.py

# Ar trebui să vezi: "Baza de date copy_top_db a fost creată cu succes!"
```

### **3.4 Migrare Baza de Date (pentru coloanele noi)**

```bash
# Rulează migrarea pentru coloanele FSC și PDF
python script_migrare.py

# Ar trebui să vezi: "🎉 Migrarea completă!"
```

---

## ⚙️ **Pasul 4: Configurare Aplicație**

### **4.1 Verificare Structură Fișiere**

Asigură-te că ai această structură:

```
CopyTop/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db_init.py
│   ├── simple_migrate.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── beneficiari.py
│   │   ├── hartie.py
│   │   ├── stoc.py
│   │   └── comenzi.py
│   ├── pages/
│   │   ├── beneficiari.py
│   │   ├── hartie.py
│   │   ├── stoc.py
│   │   ├── comenzi.py
│   │   ├── facturare.py
│   │   ├── rapoarte.py
│   │   └── rapoarte_pdf.py
│   ├── services/
│   │   └── pdf_generator.py
│   └── .streamlit/
│       └── secrets.toml
├── requirements.txt
├── .env
└── README.md
```

### **4.2 Configurare Parole**

Editează `app/.streamlit/secrets.toml`:

```toml
facturare_password = "admin"
```

**🔐 IMPORTANT**: Schimbă parola implicită pentru producție!

---

## 🚀 **Pasul 5: Pornire Aplicație**

### **5.1 Pornire Prima dată**

```bash
# Asigură-te că ești în folderul app și mediul virtual este activ
cd app
# Verifică că vezi (venv) în prompt

# Pornește aplicația
streamlit run main.py
```

### **5.2 Verificare Funcționare**

- Aplicația se va deschide automat în browser la `http://localhost:8501`
- Dacă nu se deschide automat, accesează manual linkul din terminal

### **5.3 Test Funcționalități**

1. **Adaugă un beneficiar** în pagina "Gestiune Beneficiari"
2. **Adaugă un sortiment de hârtie** în pagina "Gestiune Hârtie"
3. **Adaugă stoc** în pagina "Gestiune Stoc"
4. **Creează o comandă** în pagina "Gestiune Comenzi"
5. **Testează facturarea** cu parola configurată

---

## 🛠️ **Depanare Probleme Comune**

### **❌ Eroare PostgreSQL Connection**

```bash
# Verifică că PostgreSQL rulează
# Windows: Services -> PostgreSQL
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# Testează conexiunea
psql -U postgres -d copy_top_db
```

### **❌ Eroare "Module not found"**

```bash
# Verifică că mediul virtual este activ
# Reinstalează dependențele
pip install -r requirements.txt --force-reinstall
```

### **❌ Eroare Port 8501 ocupat**

```bash
# Folosește alt port
streamlit run main.py --server.port 8502
```

### **❌ Eroare PDF Generation**

```bash
# Verifică că ReportLab este instalat
pip install reportlab==4.0.7

# Verifică permisiuni folderul static
# Se creează automat, dar dacă ai probleme:
mkdir -p app/static/comenzi
mkdir -p app/static/rapoarte
```

### **❌ Eroare Coloane Lipsă**

```bash
# Rulează din nou migrarea
cd app
python simple_migrate.py
```

---

## 📊 **Configurări Avansate**

### **Configurare Port și Host**

```bash
# Pentru acces din rețea
streamlit run main.py --server.address 0.0.0.0 --server.port 8501
```

### **Configurare HTTPS (Producție)**

```bash
# Adaugă în .streamlit/config.toml:
[server]
enableCORS = false
enableXsrfProtection = false
```

### **Backup Bază de Date**

```bash
# Backup
pg_dump -U postgres copy_top_db > backup_copy_top.sql

# Restore
psql -U postgres copy_top_db < backup_copy_top.sql
```

---

## 🔧 **Configurări Specifice**

### **Coduri FSC**

Aplicația vine preconfigurata cu codurile FSC:

- **Intrare (materia prima)**: FSC-C008955, FSC-C009851, etc.
- **Ieșire (produs final)**: P 7.1 (Notebooks), P 8.4 (Advertising materials), etc.

### **Formate Hârtie**

Formate suportate: 70x100, 72x102, 45x64, SRA3, 50x70, A4, 64x90, 61x86, A3, 43x61

### **Matricea de Compatibilitate**

Implementată conform documentației PDF cu toate indicii de împărțire.

---

## 📱 **Utilizare Zilnică**

### **Pornire Rapidă**

```bash
# Activează mediul virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Pornește aplicația
cd app
streamlit run main.py
```

### **Oprire Aplicație**

- Apasă `Ctrl + C` în terminal
- Sau închide terminalul

---

## 🆘 **Suport și Probleme**

### **Loguri și Debug**

```bash
# Pornește cu loguri detaliate
streamlit run main.py --logger.level debug
```

### **Reset Bază de Date**

```bash
# ATENȚIE: Șterge toate datele!
DROP DATABASE copy_top_db;
CREATE DATABASE copy_top_db;
python db_init.py
python simple_migrate.py
```

### **Update Aplicație**

```bash
# Activează mediul virtual
venv\Scripts\activate

# Update pachete
pip install -r requirements.txt --upgrade

# Rulează migrări noi (dacă există)
python simple_migrate.py
```

---

## 🎯 **Checklist Instalare Completă**

- [ ] Python 3.8+ instalat cu PATH configurat
- [ ] PostgreSQL instalat și pornit
- [ ] Virtual environment creat și activat
- [ ] Dependențele instalate din requirements.txt
- [ ] Baza de date creată și configurată
- [ ] Fișierul .env configurat cu datele corecte
- [ ] Scripturile db_init.py și simple_migrate.py rulate cu succes
- [ ] Aplicația pornește la `http://localhost:8501`
- [ ] Toate paginile se încarcă fără erori
- [ ] Testele de funcționalitate trecute
