"""Deterministic lookup over authorized document metadata, never semantic inference."""
import re
import unicodedata

_FAMILIES = (
    ('cv', 'curriculum'),
    ('contrat', 'contract', 'contratto'),
    ('entretien', 'eae', 'eap', 'colloquio'),
)
_STOP = {'pdf','document','documento','fichier','file','final','finale','signe','signed'}


def words(value):
    plain=''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c))
    return set(re.findall(r'[a-z0-9]+',plain))


def is_original_request(question):
    tokens=words(question)
    text=' '.join(tokens)
    if re.search(r'\b(?:telecharg\w*|download\w*|scaric\w*)\b',text):
        return True
    artifact=tokens & {'pdf','original','originale','fichier','file','document','documento','cv','curriculum'}
    if not tokens & {'pdf','original','originale'} and tokens & {'resume','summary','riassunto','competences','skills','informations','informazioni','contenu'}:
        return False
    action=re.search(r'\b(?:recuper\w*|retrieve\w*|renvo\w*|rimand\w*|restitui\w*|invi\w*|envoi\w*|donne\w*|donn\w*|dammi|darmi|mostr\w*|vedere|voir|consulter|get|give|show|send|open)\b',text)
    return bool(artifact and action)


def document_selection(question, documents):
    """None = transversal; empty/ambiguous groups require clarification, not guessing.

    Recognized document kinds take priority over shared person/company name tokens.
    Every matching filename of the same kind remains a candidate (e.g. two CVs).
    """
    if not documents:
        return None,False
    query=words(question)
    families=[set(f) for f in _FAMILIES if query & set(f)]
    if not families and query & {'compare','confronta','synthese','sintesi','synthesis','ensemble'}:
        return None,False
    if families:
        groups=[[d for d in documents if words(d['filename']) & family] for family in families]
        selected={d['source_revision_id']:d for group in groups for d in group}
        return list(selected.values()), any(len(group)!=1 for group in groups)
    named=[d for d in documents if (tokens:=words(d['filename'])-{'pdf'}) and tokens<=query]
    if named:
        return named,len(named)!=1
    if not query & {'pdf','document','documento','fichier','fonte','source'}:
        return None,False
    matches=[d for d in documents if (words(d['filename'])-_STOP)&query]
    return matches,len(matches)!=1


def document_reply(question, documents):
    matches,ambiguous=document_selection(question,documents)
    if matches is None or (not matches and '.pdf' not in question.casefold()
            and not any(words(question)&set(f) for f in _FAMILIES)):
        matches=documents
        ambiguous=len(matches)!=1
    if not matches:
        return dict(text='Aucun original accessible ne correspond à cette demande. Précise le document souhaité.',documents=[])
    text='Quel original souhaites-tu récupérer ? Choisis le document.' if ambiguous else (
        'Voici les documents originaux.' if len(matches)>1 else 'Voici le document original. Utilise le téléchargement sécurisé ci-dessous.')
    return dict(text=text,documents=matches)


def scoped_revision_ids(rows, selected, documents):
    allowed={d['source_revision_id'] for d in selected}
    known={d['source_revision_id'] for d in documents}
    result=[]
    for row in rows:
        evidence={c['source_revision_id'] for c in row['content'].get('citations',[]) if c['source_revision_id'] in known}
        # A cross-document statement is indivisible: never pretend its whole text
        # belongs to just one source by stripping its other citations.
        if evidence and evidence<=allowed:
            result.append(row['revision_id'])
    return tuple(result)
