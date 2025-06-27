# app/constants.py

# Coduri FSC pentru materia primă (Input Product Type)
CODURI_FSC_MATERIE_PRIMA = {
    "P 2.1": "Copying, printing, communication paper",
    "P 2.4.9": "Embossed paper and perforated paper", 
    "P 3.1": "Uncoated paperboard",
    "P 3.2": "Coated paperboard",
    "P 3.3": "Pressboard",
    "P 7.8": "Adhesive labels"
}

# Certificări FSC pentru materia primă
CERTIFICARI_FSC_MATERIE_PRIMA = [
    "FSC Mix Credit",
    "FSC Recycled", 
    "FSC Recycled Credit",
    "FSC Reciclat 100%",
    "FSC Mix Credit 90%",
    "FSC Reciclat 50%"
]

# Coduri FSC pentru produsul final (Output Product Type)
CODURI_FSC_PRODUS_FINAL = {
    "P 7.1": "Notebooks",
    "P 7.5": "Post and greeting cards", 
    "P 7.6": "Envelopes",
    "P 7.7": "Gummed paper",
    "P 7.8": "Adhesive labels",
    "P 8.4": "Advertising materials",
    "P 8.5": "Business card",
    "P 8.6": "Calendars, diaries and organisers"
}

# Tipuri de certificare FSC pentru produsul final
TIPURI_CERTIFICARE_FSC_PRODUS = [
    "Notebooks",
    "Post and greeting cards",
    "Envelopes", 
    "Gummed paper",
    "Adhesive labels",
    "Advertising materials",
    "Business card",
    "Calendars, diaries and organisers"
]

# Formate de laminare
FORMATE_LAMINARE = [
    "54 x 86mm",
    "60 x 90mm", 
    "60 x 95mm",
    "65 x 95mm",
    "75 x 105mm",
    "80 x 111mm",
    "80 x 120mm",
    "A6 111 x 154mm",
    "A5 154 x 216mm",
    "A4 216 x 303mm",
    "A3 303 x 426mm"
]

# Opțiuni plastifiere
OPTIUNI_PLASTIFIERE = [
    "Mat o fata",
    "Mat Fata/Verso", 
    "Lucios o Fata",
    "Lucios fata/verso",
    "Soft-Touch o Fata",
    "Soft-Touch Fata/Verso"
]

# Opțiuni culori
OPTIUNI_CULORI = [
    "4 + 4",
    "4 + 0", 
    "4 + K",
    "K + K",
    "K + 0",
    "0 + 0"
]