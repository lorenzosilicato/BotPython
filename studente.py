import telegram
from telegram.ext import ConversationHandler, CallbackContext
from firebase_admin import db
from professore import cancel
from config import (capienze_aule,SELEZIONE,DATA,POSTAZIONE,NOME)

# Funzione che permette di vedere tutti i corsi disponibili
def cerca_lezione(update, context):
    ref = db.reference("/Lezione")
    lezioni=ref.get()   
    if lezioni is None:
        update.message.reply_text("Nessuna lezione disponibile.")
        return      
    button_list = []
    added_lezioni = set()
    for key, value in lezioni.items():
        if 'nome' in value:
            nome_lezione = value['nome']
            if nome_lezione not in added_lezioni:
                button_list.append([telegram.InlineKeyboardButton(nome_lezione, callback_data=f"searchLezione_{key}")])
                added_lezioni.add(nome_lezione)
    # Aggiungi il pulsante "Annulla"
    button_list.append([telegram.InlineKeyboardButton("Annulla ❌", callback_data="annulla")])    
    # Invio dei bottoni all'utente
    context.bot.send_message(chat_id=update.effective_chat.id, text="Seleziona una lezione:", reply_markup=telegram.InlineKeyboardMarkup(button_list))

#Funzione che mostra all'utente varie informazioni sul corso selezionato, come l'aula e le varie date prenotabili
def ispeziona_lezione(update: telegram.Update, context: CallbackContext):
    query = update.callback_query
    selected_lezione_id = query.data.split('_')[1]
    if selected_lezione_id == "annulla":
        return cancel(update,context)  
    # Recupera le informazioni della lezione dal database
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    selected_lezione = lezioni[selected_lezione_id]
    query.message.delete()
    
    if lezioni is not None:
        for key, value in lezioni.items():
            if value.get('nome') == selected_lezione['nome']:
                 # Recupera tutte le date e gli orari disponibili per la lezione
                date_ore = []
                for k, v in lezioni.items():
                    if 'data' in v and 'ora' in v and v['nome'] == selected_lezione['nome']:
                        date_ore.append(f"Aula: {v['aula']} - Data: {v['data']} - Ora: {v['ora']}")

                # Costruisci il messaggio con le informazioni della lezione seguito da tutte le date e gli orari disponibili
                message = f"Informazioni sulla lezione '{selected_lezione['nome']}':\n"
                #message += f"Aula: {selected_lezione['aula']}\n"
                message += f"Date e orari disponibili:\n"
                message += '\n'.join(date_ore)
                # Aggiungi il pulsante "Indietro"
                back_button = telegram.InlineKeyboardButton("Indietro 🔙", callback_data="goBack")
                keyboard = [[back_button]]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                # Invia il messaggio all'utente
                context.bot.send_message(chat_id=query.message.chat_id, text=message,reply_markup=reply_markup)
                return
    
    # Se la lezione non ha informazioni nel database, invia un messaggio di errore
    error_message = f"Le informazioni sulla lezione '{selected_lezione['nome']}' non sono disponibili."
    context.bot.send_message(chat_id=query.message.chat_id, text=error_message)

#gestisce l'azione da eseguire quando premo "indietro"
def indietro(update, context):
    cerca_lezione(update, context)

# funzione che permette la prenotazione di un posto per una lezione
def prenota_lezione(update: telegram.Update, context: CallbackContext):
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    #print("DEBUG: ho chiamato prenota")
    button_list = []
    added_lezioni = set()
    #Crea una lista di bottoni per la selezione della lezione desiderata
    for key, value in lezioni.items():
        if 'nome' in value:
            nome_lezione = value['nome']
            if nome_lezione not in added_lezioni:
                button_list.append([telegram.InlineKeyboardButton(nome_lezione, callback_data=f"lezione_{key}")])
                added_lezioni.add(nome_lezione)
    button_list.append([telegram.InlineKeyboardButton(text="Annulla ❌", callback_data="annulla")])
    reply_markup = telegram.InlineKeyboardMarkup(button_list)
    update.message.reply_text("Seleziona una lezione:", reply_markup=reply_markup)
    return SELEZIONE

#gestisce la selezione di una lezione dalla lista e chiede all'utente di selezionare una data disponibile per la lezione
def seleziona_lezione(update: telegram.Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "annulla":
        return cancel(update,context)
    
    selected_lezione_id = query.data.split('_')[1]
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    selected_lezione = lezioni[selected_lezione_id]
    context.user_data['selected_lezione'] = selected_lezione
    query.message.delete()

    # Ottiene le date disponibili per la lezione selezionata
    dates = []
    for key, value in lezioni.items():
        if 'data' in value and value['nome'] == selected_lezione['nome']:
            data=value['data']
            ora=value['ora']
            dates.append((data,ora))
    if not dates:
        query.message.reply_text("Nessuna data disponibile per la lezione selezionata.")
        return cancel(update, context)
        
    # Costruisce i pulsanti per le date disponibili
    button_list = []
    for data,ora in dates:
        button_list.append([telegram.InlineKeyboardButton(data, callback_data=f"data_{data}_{ora}")])
    button_list.append([telegram.InlineKeyboardButton(text="Annulla ❌", callback_data="annulla")])
    reply_markup = telegram.InlineKeyboardMarkup(button_list)
    # Chiede all'utente di selezionare una data
    query.message.reply_text("Seleziona una data:", reply_markup=reply_markup)
    return DATA

#Mostra all'utente una lista di bottoni per la selezione della data
def select_data_lezione(update: telegram.Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "annulla":
        return cancel(update,context) 
    selected_date = query.data.split('_')[1]
    selected_time = query.data.split('_')[2]
    user_id = str(update.effective_chat.id)    
    #print("DEBUG: data", selected_date,"ora:",selected_time)
    try:
        selected_lezione = context.user_data['selected_lezione']
        selected_lezione['data'] = selected_date
        selected_lezione['ora'] = selected_time
        context.user_data['selected_lezione'] = selected_lezione
    except:
        #print("DEBUG: utente",user_id,"ha effettuato un'operazione non prevista.")
        context.bot.send_message(chat_id=user_id, text=f"Operazione non valida.\nPer prenotare fai /prenota_lezione")
        return
    #controllo che l'utente non abbia già prenotato per quella lezione tramite il suo id univoco
    ref = db.reference("/Prenotazioni")
    prenotazioni = ref.get()
    if prenotazioni is not None:
        for key, value in prenotazioni.items():
            if value.get('lezione') == selected_lezione['nome'] and value.get('data')==selected_lezione['data'] and value.get('id') == user_id:
                context.bot.send_message(chat_id=user_id, text=f"Hai già prenotato la lezione '{selected_lezione['nome']}' per il giorno {selected_lezione['data']}.")
                return cancel(update,context)
    query.message.delete()
    # Chiede all'utente di inserire la postazione
    query.message.reply_text("Inserisci il numero della postazione:")
    return POSTAZIONE

#recupera l'aula associata a una lezione e a una data specifiche dal database
def get_aula_lezione(nome_lezione,data_lezione):
    ref = db.reference("/Lezione")
    lezioni = ref.get()
    if lezioni is not None:
        for key, value in lezioni.items():
            if value.get('nome') == nome_lezione and value.get('data') == data_lezione:
                aula_lezione = value.get('aula')
                if aula_lezione in capienze_aule:
                    return aula_lezione
                else:
                    ##print("DEBUG: Aula non valida")
                    return None
    return None

#Controlla se la postazione è valida e disponibile per quella lezione
def select_postazione(update, context):
    try:
        selected_lezione = context.user_data['selected_lezione']
    except:
        update.message.reply_text("Non hai inserito un comando valido")
        return
    nome_lezione = selected_lezione['nome']
    data_lezione = selected_lezione['data']
    aula_lezione = get_aula_lezione(nome_lezione,data_lezione)
    if aula_lezione not in capienze_aule:
        update.message.reply_text("L'aula della lezione non è valida.\nContatta il professore.")
        return
    capienza_aula = capienze_aule[aula_lezione]
    try:
        #Controlla la validità dell'input dell'utente
        postazione = int(update.message.text)
        if postazione <= 0:
            update.message.reply_text("Il numero della postazione deve essere un numero positivo.")
            return
        if postazione > capienza_aula:
            update.message.reply_text("Il numero della postazione inserito non è valido per l'aula della lezione.")
            return
        #controllo che la postazione non sia occupata
        ref = db.reference("/Prenotazioni")
        prenotazioni = ref.get()
        if prenotazioni is not None:
            for key, value in prenotazioni.items():
                if value.get('lezione') == selected_lezione['nome'] and value.get('data')==data_lezione and value.get('postazione') == postazione:
                    context.bot.send_message(chat_id=update.message.chat_id, text="La postazione selezionata è già stata prenotata da un altro studente.\n\nInseriscine un'altra")
                    return
        # se è tutto ok vado avanti        
        context.user_data['postazione'] = postazione
        # Chiedo all'utente di inserire il nome
        update.message.reply_text("Inserisci il tuo nome:")
        return NOME

    except ValueError:
        update.message.reply_text("Il numero della postazione deve essere un numero intero.")
        return
        
#Verifica se il formato in cui l'utente inserisce il nome è valido e poi salva le informazioni nel database
def get_nome(update, context):
    studente = update.message.text
    if not studente.isalpha():
        update.message.reply_text("Il nome deve essere composto solo da lettere.")
        return
    if len(studente)<2 or len(studente)>15:
        update.message.reply_text("Il nome deve essere composto da un numero di caratteri compreso tra 2 e 15.")
        return
    user_id = str(update.effective_chat.id)
    try:
        selected_lezione = context.user_data['selected_lezione']
    except:
        update.message.reply_text("Non hai inserito un comando valido")
        return
    try:
        postazione = context.user_data['postazione']
    except KeyError:
        update.message.reply_text("Il numero della postazione deve essere un numero intero.")
        return

    ref = db.reference("/Prenotazioni")
    prenotazioni = ref.get()
    # Esegui le operazioni di prenotazione nel database
    ref.push().set(
        {
            "lezione": selected_lezione['nome'],
            "data":selected_lezione['data'],
            "ora": selected_lezione['ora'],
            "id": user_id,
            "aula":selected_lezione['aula'],
            "postazione": postazione,
            "studente": studente
        }
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text="Prenotazione completata con successo!")
    # Pulizia del contesto
    context.user_data.pop('selected_lezione', None)
    context.user_data.pop('studente',None)
    context.user_data.pop('postazione', None)  
    # Rimuovi i messaggi in sospeso
    if 'messages' in context.user_data:
        for message_id in context.user_data['messages']:
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
            except telegram.error.BadRequest:
                pass

    # Cancella tutti i messaggi in sospeso
    context.user_data['messages'] = []    
    return ConversationHandler.END

#Recupera le prenotazioni dell'utente e mostra le informazioni di ognuna, permettendogli anche di annullare una prenotazione
def mostra_prenotazioni(update, context):
    user_id = str(update.effective_chat.id)
    ref = db.reference("/Prenotazioni")
    prenotazioni = ref.get()
    has_prenotazioni=False
    if prenotazioni is not None:
        prenotazioni_utente = [prenotazione for prenotazione in prenotazioni.values() if prenotazione.get('id') == user_id]
        if prenotazioni_utente:
            message = "Le tue prenotazioni:\n\n"
            message += "---------------------------\n\n"
            for prenotazione in prenotazioni_utente:
                lezione = prenotazione.get('lezione')
                aula = prenotazione.get('aula')
                data = prenotazione.get('data')
                ora= prenotazione.get('ora')
                postazione = prenotazione.get('postazione')
                # Creazione del pulsante "Annulla prenotazione"
                cancella_button = telegram.InlineKeyboardButton("Annulla prenotazione", callback_data=f"annulla_{lezione}_{data}")

                keyboard = [[cancella_button]]
                reply_markup = telegram.InlineKeyboardMarkup(keyboard)
                message += f"Lezione: {lezione}\nAula: {aula}\nData: {data}\nOra: {ora}\nPostazione: {postazione}\n"
                message += "\nPremi 'Annulla prenotazione' per cancellare questa prenotazione.\n\n"
                has_prenotazioni=True

                # Invio del messaggio con la tastiera inline
                context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup)
                #ripulisce message per avere un feed più leggibile
                message=""
        else:
            if not has_prenotazioni:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Non hai effettuato alcuna prenotazione.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Non ci sono prenotazioni.")

#funzione che annulla una prenotazione
def annulla_prenotazione(update, context):
    query = update.callback_query
    lezione = query.data.split('_')[1]
    data=query.data.split('_')[2]
    print(lezione)
    ref = db.reference('/Prenotazioni')
    user_id = str(update.effective_chat.id)
    prenotazioni=ref.get()
    if prenotazioni is not None:
        for key, value in prenotazioni.items():
            if value.get('lezione') == lezione and value.get('data')==data and value.get('id') == user_id:
                #print("DEBUG: utente id:",user_id, "sta cancellando la sua prenotazione",lezione, "del giorno",data)
                ref.child(key).delete()
                context.bot.send_message(chat_id=update.effective_chat.id, text="Prenotazione cancellata")
                #Una volta cancellata una prenotazione, faccio vedere all'utente la lista aggiornata delle prenotazioni
                return mostra_prenotazioni(update, context) 
        else:
            #print("DEBUG: non trovo la lezione",lezione)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Prenotazione non trovata!")
            return