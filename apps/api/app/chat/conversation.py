"""Only exact, unambiguous conversational acknowledgements bypass generation."""
import re
import unicodedata


def conversational_reply(text, documents=()):
    value = unicodedata.normalize('NFKC', text).strip().casefold()
    value = re.sub(r'[.!…]+$', '', value).strip()
    replies = {'grazie':'Prego!', 'merci':'Avec plaisir !', 'thank you':"You're welcome!",
        'thanks':"You're welcome!", 'ok':'OK !', 'okay':'OK !', "d'accord":'D’accord !', 'va bene':'Va bene!'}
    if value in replies:
        return replies[value]
    # Deliberately whole-message matching: no compound requests or ambiguity.
    patterns = (
        ('it', r'ho (?:allegato|caricato) (?:il )?(contratto|cv)(?: e (?:il )?(contratto|cv))?'),
        ('fr', r"j['’]ai (?:joint|ajouté|chargé) (?:le )?(contrat|cv)(?: et (?:le )?(contrat|cv))?"),
        ('en', r'i (?:have )?(?:attached|uploaded) (?:the )?(contract|cv)(?: and (?:the )?(contract|cv))?'),
    )
    for language, pattern in patterns:
        match = re.fullmatch(pattern, value)
        if not match:
            continue
        requested = {word for word in match.groups() if word}
        names = ' '.join(str(d.get('display_name',''))+' '+str(d.get('filename','')) for d in documents).casefold()
        present = all(re.search(r'\b'+('contrat\\w*' if word in ('contratto','contrat','contract') else r'(cv|curriculum)')+r'\b', names) for word in requested)
        return ({'it':'Vedo i documenti allegati. Dimmi pure come posso aiutarti.',
            'fr':'Je vois les documents joints. Dis-moi comment je peux t’aider.',
            'en':'I can see the attachments. Let me know how I can help.'} if present else
            {'it':'Non riesco a confermare tutti gli allegati indicati. Controlla che il caricamento sia completato.',
             'fr':'Je ne peux pas confirmer tous les documents indiqués. Vérifie que leur chargement est terminé.',
             'en':'I cannot confirm all the attachments mentioned. Please check that their upload has finished.'})[language]
    return None
