import telegram
import datetime
from telegram.ext import ConversationHandler, CallbackContext
from firebase_admin import db
from config import (capienze_aule,CREA_NOME, CREA_AULA, CREA_DATA, CREA_ORA,SELEZIONE_LEZIONE, SELEZIONE_DATA_CANCELLAZIONE)

# Funzione che cancella l'azione corrente eseguita dall'utente, cancellando tutti i dati della conversazione
def cancel(update: telegram.Update, context: CallbackContext):
    query=update.callback_query
    if query:
        query.message.delete()
        ##print("DEBUG:cancello query")
    else:
        update.message.delete()
        #print("DEBUG:Cancello messaggio")
    context.user_data.clear()
    context.bot.send_message(chat_id=update.effective_chat.id, text="Operazione annullata.")
    #print("DEBUG:e adesso chiudo la conversaione")    
    return ConversationHandler.END

#Funzione che avvia il processo guidato di creazione di una lezione
def crea_lezione(update, context):
    # Verifica se l'utente è un professore
    user = update.effective_user
    if user.username != 'SamuIosa':
        context.bot.send_message(chat_id=update.message.chat_id, text="Accesso negato. Solo i professori possono creare lezioni.")
        return
    update.message.reply_text("Inserisci il nome della lezione:")
    return CREA_NOME
#Inizio gestione dei parametri richiesti per creare una lezione: Nome, Aula, Data,Ora
def get_nome_lezione(update, context):
    nome_lezione = update.message.text
    context.user_data['nome_lezione'] = nome_lezione
    update.message.reply_text("Inserisci l'aula:")
    return CREA_AULA

def get_aula(update, context):
    aula_lezione = update.message.text
    # Verifica se l'aula è presente nel dizionario delle capienze
    if aula_lezione not in capienze_aule:
        update.message.reply_text(f"L'aula '{aula_lezione}' non è un'aula valida.")
        return
    context.user_data['aula_lezione'] = aula_lezione
    update.message.reply_text("Inserisci la data (formato: GG-MM-AAAA):")
    return CREA_DATA

def get_data_lezione(update, context):
    data_lezione = update.message.text
    try:
        # Verifica se la data inserita è nel formato corretto (GG-MM-AAAA), non è weekend e se l'anno è valido
        date_obj = datetime.datetime.strptime(data_lezione, "%d-%m-%Y")
        if date_obj.weekday() >= 5:
            update.message.reply_text("Non è possibile creare lezioni di sabato o domenica.")
            return
        current_year = datetime.datetime.now().year
        if date_obj.year < current_year:
            update.message.reply_text("L'anno inserito non può essere inferiore all'anno corrente.")
            return
    except ValueError:
        update.message.reply_text("Formato data non valido. Inserisci la data nel formato GG-MM-AAAA.")
        return
    context.user_data['data_lezione'] = data_lezione
    update.message.reply_text("Inserisci l'ora (formato: HH:MM):")
    return CREA_ORA

def get_ora_lezione(update, context):
    ora_lezione = update.message.text
    try:
        # Verifica se l'ora inserita è nel formato corretto (HH:MM) ed è nell'orario di apertura dell'università
        time_obj = datetime.datetime.strptime(ora_lezione, "%H:%M")
        start_time = datetime.datetime.strptime("9:00", "%H:%M").time()
        end_time = datetime.datetime.strptime("18:00", "%H:%M").time()
        if not start_time <= time_obj.time() <= end_time:
            update.message.reply_text("L'orario inserito non è valido. Gli orari disponibili sono dalle 9:00 alle 18:00.")
            return
    except ValueError:
        update.message.reply_text("Formato ora non valido. Inserisci l'ora nel formato HH:MM.")
        return
    
    # Verifica se esiste già una lezione programmata nello stesso giorno e alla stessa ora nella stessa aula
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    aula_lezione = context.user_data['aula_lezione']
    data_lezione = context.user_data['data_lezione']
    if lezioni is not None:
        for key, value in lezioni.items():
            if value.get('data') == data_lezione and value.get('ora') == ora_lezione and value.get('aula') == aula_lezione:
                update.message.reply_text(f"È già programmata una lezione nello stesso giorno e alla stessa ora nell'aula '{aula_lezione}'.")
                return
    context.user_data['ora_lezione'] = ora_lezione

    #Calcola la capienza dell'aula tramite il dizionario
    capienza = capienze_aule[aula_lezione]
    id_professore=str(update.effective_chat.id)
    ref.push().set(
        {
            "nome" : context.user_data['nome_lezione'],
            "capienza" : capienza,
            "aula": aula_lezione,
            "data": data_lezione,
            "ora": ora_lezione,
            "professore": id_professore
        }
    )
    update.message.reply_text("Nuova lezione creata!")
    return ConversationHandler.END

#Funzione che permette a un professore di cancellare una sua lezione
def cancella_lezione(update, context):
    ref = db.reference("/Lezione")
    #Controlla che chi ha chiamato il comando sia un professore tramite nome telegram
    if update.effective_user.username != 'SamuIosa':
        context.bot.send_message(chat_id=update.message.chat_id, text="Accesso negato. Solo i professori possono cancellare lezioni.")
        return
    user_id = str(update.effective_chat.id)
    lezioni = ref.get()
    button_list = []
    added_lezioni = set()
    # Mostra soltanto le lezioni create dal professore che esegue il comando, controllando il chat id
    for key, value in lezioni.items():
        if 'nome' in value:
            nome_lezione = value['nome']
            if nome_lezione not in added_lezioni and user_id==value['professore']:
                button_list.append([telegram.InlineKeyboardButton(nome_lezione, callback_data=f"lezione_{key}")])
                added_lezioni.add(nome_lezione)           
    button_list.append([telegram.InlineKeyboardButton(text="Annulla ❌", callback_data="annulla")])

    reply_markup = telegram.InlineKeyboardMarkup(button_list)
    # Invio dei bottoni
    update.message.reply_text("Seleziona una lezione da cancellare:", reply_markup=reply_markup)
    return SELEZIONE_LEZIONE      

def seleziona_lezione_cancellazione(update, context):
    query = update.callback_query
    if query.data == "annulla":
        return cancel(update,context)   
    selected_lezione_id = query.data.split('_')[1]
    # Ottieni la lezione selezionata utilizzando l'ID
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    selected_lezione = ref.child(selected_lezione_id).get()
    if selected_lezione:
        # Salva la lezione selezionata nel contesto
        context.user_data['selected_lezione'] = selected_lezione
        query.message.delete()
        # Recupera le date associate alla lezione selezionata e le visualizza
        dates = []
        for key, value in lezioni.items():
            if 'data' in value and value['nome'] == selected_lezione['nome']:
                data=value['data']
                ora=value['ora']
                dates.append((data,ora))
        if not dates:
            query.message.reply_text("Nessuna data disponibile per la lezione selezionata.")
            return cancel(update, context)
        button_list = []
        for data,ora in dates:
            button_list.append([telegram.InlineKeyboardButton(data, callback_data=f"data_{data}_{ora}")])
        button_list.append([telegram.InlineKeyboardButton(text="Annulla ❌", callback_data="annulla")])
        reply_markup = telegram.InlineKeyboardMarkup(button_list)

        # Invia i bottoni all'utente per selezionare una data
        query.message.reply_text("Seleziona una data da cancellare:", reply_markup=reply_markup)
        return SELEZIONE_DATA_CANCELLAZIONE
    else:
        query.message.reply_text("Lezione non trovata.")
    return 

#Una volta scelta una determinata lezione controlla che sia tutto corretto e la cancella
def seleziona_data_cancellazione(update, context):
    query = update.callback_query
    if query.data == "annulla":
        return cancel(update,context)   
    selected_date = query.data.split('_')[1]
    selected_lezione = context.user_data.get('selected_lezione')
    if selected_lezione:
        lezione = selected_lezione['nome']
        data = selected_date
        ref = db.reference('/Lezione')
        user_id = str(update.effective_chat.id)
        lezioni = ref.get()

        if lezioni is not None:
            for key, value in lezioni.items():
                if value.get('nome') == lezione and value.get('data') == data:
                    #print("DEBUG: utente id:", user_id, "sta cancellando la lezione", lezione, "del giorno", data)
                    ref.child(key).delete()
                    context.bot.send_message(chat_id=update.effective_chat.id, text="Lezione cancellata")
                    return ConversationHandler.END

        #print("DEBUG: lezione non trovata")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Lezione non trovata!")
    else:
        #print("DEBUG: lezione non trovata")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Lezione non trovata!")
    return

#Funzione ausiliaria chiamata per ottenere una lista delle date in cui c'è un determinato corso
def get_dates_for_lezione(lezione_id):
    ref = db.reference('/Lezione')
    lezioni = ref.get()
    dates = set()

    if lezioni is not None:
        for key,value in lezioni.items():
            if key == lezione_id:
                dates.add(value.get('data'))
    return list(dates)