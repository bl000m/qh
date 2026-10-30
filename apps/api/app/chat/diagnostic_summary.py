"""Private diagnostic presentation: call counters and validation batches stay distinct."""
import json
import re


def uum_output_metrics(response):
    """Lengths/counts only. Malformed output remains the Engine's responsibility."""
    sizes = {}
    try:
        content = response['choices'][0]['message']['content']
        if not isinstance(content, str):
            return {}
        sizes = dict(output_json_chars=len(content), output_json_bytes=len(content.encode()))
        output = json.loads(content)
        items = output.get('understanding', output)['items']
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            return sizes
        sizes['atomic_items'] = len(items)
        if all(isinstance(item.get('text'), str) for item in items):
            sizes['atomic_text_chars'] = sum(len(item['text']) for item in items)
        evidence = [item.get('evidence_refs', item.get('evidence')) for item in items]
        if any(not isinstance(refs, list) for refs in evidence):
            return sizes
        return dict(**sizes, passage_references=sum(map(len, evidence)),
            evidence_json_chars=sum(len(json.dumps(refs, ensure_ascii=False, separators=(',', ':'))) for refs in evidence))
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return sizes


SOURCE_METRICS = {'source_chars','source_tokens','source_turns','source_disclosed_chars',
    'catalogue_passages','catalogue_chars','previous_machine_chars'}
ATOMIC_METRICS = {'atomic_items','atomic_text_chars','passage_references','evidence_json_chars'}


def output_phase(response):
    try:
        value=json.loads(response['choices'][0]['message']['content'])
        if 'understanding' in value and 'recap' in value:
            return 'extraction_summary'
        if 'items' in value or 'understanding' in value:
            return 'extraction'
        if 'title' in value and 'text' in value:
            return 'summary'
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    return 'unknown'


def call_metrics(metrics, response):
    result={k:v for k,v in metrics.items() if k not in ATOMIC_METRICS}
    # Summary HTTP responses do not inherit the preceding extraction's counters.
    if output_phase(response)=='summary':
        result={k:v for k,v in result.items() if k not in SOURCE_METRICS|ATOMIC_METRICS}
        result['atomic_items']=0
    result.update(uum_output_metrics(response))
    return result


def validation_rounds(checks):
    rounds=[]
    for check in checks:
        if check['rule']=='uum.envelope_format_and_item_count':
            rounds.append(set())
        match=re.fullmatch(r'uum.item.(\d+).fields',check['rule'])
        if match:
            if not rounds:rounds.append(set())
            rounds[-1].add(int(match[1]))
    return [dict(items=len(indices)) for indices in rounds]


def operation_totals(calls):
    keys=('input_tokens','output_tokens','request_message_chars','atomic_items','source_chars')
    extraction=[call for call in calls if call['phase'] in ('extraction','extraction_summary')]
    result=dict(calls=len(calls),blocks=len(extraction),summaries=sum(c['phase'] in ('summary','extraction_summary') for c in calls))
    for key in keys:
        selected=extraction if key in ('atomic_items','source_chars') else calls
        values=[call['metrics'].get(key) for call in selected]
        result[key]=sum(values) if values and all(v is not None for v in values) else None
    return result


def diagnostic_view(record):
    if record['kind']!='uum':return record
    response=record.get('raw_response')
    warnings=record.get('warnings',[])
    if output_phase(response)=='summary':
        warnings=[w for w in warnings if w=='output_tokens_over_3x_input']
    return dict(record,metrics=call_metrics(record.get('metrics',{}),response),
        warnings=warnings,call_phase=output_phase(response),validation_rounds=validation_rounds(record['checks']),
        legacy_metrics='operation' not in record)
