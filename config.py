#Dizionario dove sono salvate le capienze delle varie aule
capienze_aule = {
    'a0': 50,
    'a1': 30,
    'a2':30,
    'b1':30,
    'b2':20
}

# Definiamo gli stati della conversazione con lo studente
SELEZIONE,DATA ,POSTAZIONE, NOME = range(4)
# Definiamo gli stati della conversazione con il professore
CREA_NOME, CREA_AULA, CREA_DATA, CREA_ORA,SELEZIONE_LEZIONE, SELEZIONE_DATA_CANCELLAZIONE = range(6)
