from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import firebase_admin
from firebase_admin import db
from studente import (cerca_lezione,ispeziona_lezione,indietro,prenota_lezione,seleziona_lezione,select_data_lezione,select_postazione,get_nome,mostra_prenotazioni,annulla_prenotazione)
from professore import(cancel,crea_lezione,get_nome_lezione,get_aula,get_data_lezione,get_ora_lezione,cancella_lezione,seleziona_lezione_cancellazione,seleziona_data_cancellazione)
from config import (SELEZIONE,DATA,POSTAZIONE,NOME,CREA_NOME, CREA_AULA, CREA_DATA, CREA_ORA,SELEZIONE_LEZIONE, SELEZIONE_DATA_CANCELLAZIONE)
cred_obj = firebase_admin.credentials.Certificate('C:/Users/lollo/Documents/Roba/Università/UniPg/ProgettoIngS/BOT/bot-prenotazione-aule-firebase-adminsdk-omktn-88e1a48c45.json')
default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL':'https://bot-prenotazione-aule-default-rtdb.europe-west1.firebasedatabase.app/'
	})

# Definiamo le costanti del bot
TOKEN = TOKEN
PORT = 5000


# Funzione che gestisce il comando /start
def start(update, context):
    update.message.reply_text('Benvenuto al Bot PrenotaLezioni!\n\nPuoi cercare lezioni disponibili con il comando /cerca_lezione.\n\nPuoi prenotare un posto per una lezione con il comando /prenota_lezione seguito dal nome della lezione e dal numero del posto desiderato (es. /prenota_lezione Matematica 3).\n\nPer vedere le prenotazioni effettuate puoi usare il comando /prenotazioni.')


def main():
    # definiamo l'updater del bot
    updater = Updater(TOKEN)
    # Definizione degli handler più semplici
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cerca_lezione', cerca_lezione))
    dispatcher.add_handler(CommandHandler('prenotazioni', mostra_prenotazioni))
    dispatcher.add_handler(CallbackQueryHandler(ispeziona_lezione, pattern="^searchLezione_"))
    dispatcher.add_handler(CallbackQueryHandler(annulla_prenotazione, pattern="^annulla_"))
    dispatcher.add_handler(CallbackQueryHandler(indietro,pattern='goBack'))

    # Creazione dell'handler che gestisce la prenotazione
    prenotazione_handler = ConversationHandler(
        entry_points=[CommandHandler('prenota_lezione', prenota_lezione)],
        states={
            SELEZIONE: [CallbackQueryHandler(seleziona_lezione),
                        CallbackQueryHandler(cancel, pattern="^annulla$")],
            DATA: [CallbackQueryHandler(select_data_lezione),
                   CallbackQueryHandler(cancel, pattern="^annulla$")],
            POSTAZIONE: [MessageHandler(Filters.text & ~Filters.command, select_postazione)],
            NOME: [MessageHandler(Filters.text & ~Filters.command, get_nome)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(prenotazione_handler)

   # Creazione dell'handler che gestisce la creazione di lezioni
    professor_handler = ConversationHandler(
    entry_points=[CommandHandler('crea_lezione', crea_lezione)],
    states={
        CREA_NOME: [MessageHandler(Filters.text, get_nome_lezione)],
        CREA_AULA: [MessageHandler(Filters.text, get_aula)],
        CREA_DATA: [MessageHandler(Filters.text, get_data_lezione)],
        CREA_ORA: [MessageHandler(Filters.text, get_ora_lezione)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(professor_handler)
    
    # Creazione dell'handler che gestisce la cancellazione delle lezioni
    cancel_lezione_handler = ConversationHandler(
    entry_points=[CommandHandler('cancella_lezione', cancella_lezione)],
    states={
        SELEZIONE_LEZIONE: [CallbackQueryHandler(seleziona_lezione_cancellazione),
                            CallbackQueryHandler(cancel, pattern="^annulla$")],
        SELEZIONE_DATA_CANCELLAZIONE: [CallbackQueryHandler(seleziona_data_cancellazione),
                                       CallbackQueryHandler(cancel, pattern="^annulla$")]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
    dispatcher.add_handler(cancel_lezione_handler)
    dispatcher.add_handler(CallbackQueryHandler(cancel, pattern="^annulla$"))
    # avviamo il bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
