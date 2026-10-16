"""Offline QH-33 v2 accounting/review package. No network, provider or QH writes.

V1 files and evaluator stay sealed. The v2 naming adapter reuses the existing
human-review gates, while keeping rubric approval separate from personal review.
"""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "apps/api/tests/fixtures/qh33/benchmark-v2.json"
NAMES = {
    "coverage": "active_coverage",
    "semantic": "semantic_support",
    "attribution": "attribution",
    "negation": "negation",
    "temporality": "temporality",
    "uncertainty": "uncertainty",
    "provenance": "citation_traceability",
}
DIMENSIONS = tuple(NAMES.values())


def local_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v1 = local_module("qh33_sealed_v1", ROOT / "scripts/evaluate_qh33.py")
citations = local_module(
    "qh33_existing_citations", ROOT / "apps/api/app/understanding/citations.py"
)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_benchmark(path=BENCHMARK):
    b = v1.read_json(path)
    if (
        b["version"] != 2
        or b["reference_status"] != "D1-D5_approved_personal_review_pending"
    ):
        raise ValueError("Explicit v2 rubric-only approval required")
    for prefix in ("parent", "reassessment", "evaluator_v1"):
        pinned = (ROOT / b["lineage"][prefix + "_path"]).resolve()
        if (
            not pinned.is_relative_to(ROOT)
            or file_hash(pinned) != b["lineage"][prefix + "_file_sha256"]
        ):
            raise ValueError("V2 lineage mismatch")
    parent, cases = v1.load_benchmark(ROOT / b["lineage"]["parent_path"])
    rubric = v1.asset(b["rubric"], ROOT)
    proposal = v1.read_json(ROOT / b["lineage"]["reassessment_path"])
    proposed = {u["id"]: u for u in proposal["units"]}
    decision = b["owner_decisions"]
    if (
        decision["approved"] != ["D1", "D2", "D3", "D4", "D5"]
        or decision["personal_review_attestations"] != "not_provided"
        or decision["merge_or_jira_done_authorized"] is not False
        or decision["paid_inference_authorized"] is not False
        or rubric["version"] != 2
        or set(rubric["dimensions"]) != set(DIMENSIONS)
        or b["cases"] != parent["cases"]
    ):
        raise ValueError(
            "Rubric approval cannot replace unit review or change captures"
        )
    originals = {u["id"]: u for u in parent["units"]}
    if len(b["units"]) != len(originals) or {u["id"] for u in b["units"]} != set(
        originals
    ):
        raise ValueError("Retain each of the 74 original IDs exactly once")
    historical = set(rubric["active_coverage_exclusions"])
    if historical != {
        "multilingual.initial_tax_uncertainty",
        "multilingual.initial_fit_hypothesis",
    }:
        raise ValueError("Only approved historical exclusions allowed")
    for u in b["units"]:
        old, fresh = originals[u["id"]], proposed[u["id"]]
        for key in ("id", "case", "kind", "source_evidence", "anchors"):
            if u[key] != old[key]:
                raise ValueError(
                    "Original unit identity/evidence must remain unchanged"
                )
        expected = {NAMES[k]: v["rating"] for k, v in fresh["judgments"].items()}
        reasons = {NAMES[k]: v["reason_it"] for k, v in fresh["judgments"].items()}
        if (
            u["draft_ratings"] != expected
            or u["dimension_rationales_it"] != reasons
            or u["meaning"] != fresh["proposed_reading_it"]
            or u["rationale"] != fresh["rationale_it"]
            or u["issues"] != fresh["issues"]
            or u["decisions_applied"] != fresh["owner_decisions"]
            or u["owner_unit_review"] != "pending"
            or set(u["draft_ratings"]) != set(DIMENSIONS)
            or any(v not in v1.RATINGS for v in u["draft_ratings"].values())
        ):
            raise ValueError("Unapproved annotation drift or false personal review")
        scope = (
            "historical_reconstructible"
            if u["id"] in historical
            else ("active" if u["kind"] == "source_proposition" else u["kind"])
        )
        if u["coverage_scope"] != scope or (
            u["id"] in historical
            and any(v != "n/a" for v in u["draft_ratings"].values())
        ):
            raise ValueError("Historical exclusion is not a pass or source deletion")
        if (
            u["draft_ratings"]["active_coverage"] in {"pass", "partial"}
            and not u["anchors"]
        ):
            raise ValueError("Evidence-only text cannot count as extracted coverage")
    return b, cases, rubric


def legacy_units(b):
    """Naming only: preserve the sealed v1 per-unit review gates and applicability."""
    return {
        "version": 2,
        "units": [
            {
                "id": u["id"],
                "kind": u["kind"],
                "draft_ratings": {
                    old: u["draft_ratings"][new] for old, new in NAMES.items()
                },
            }
            for u in b["units"]
        ],
    }


def renamed_metrics(groups):
    for group in groups.values():
        group["dimensions"] = {
            NAMES[k]: value for k, value in group["dimensions"].items()
        }
    return groups


def review_template(b):
    result = v1.review_template(legacy_units(b))
    result.update(
        benchmark_version=2,
        benchmark_sha256=v1.digest(b),
        rubric_sha256=b["rubric"]["sha256"],
    )
    for row in result["units"]:
        row["ratings"] = {NAMES[k]: value for k, value in row["ratings"].items()}
    return result


def human_review(b, review):
    if (
        review.get("benchmark_version") != 2
        or review.get("benchmark_sha256") != v1.digest(b)
        or review.get("rubric_sha256") != b["rubric"]["sha256"]
    ):
        raise ValueError("Review must identify this exact v2 benchmark and rubric")
    mapped = deepcopy(review)
    legacy = legacy_units(b)
    mapped["benchmark_sha256"] = v1.digest(legacy)
    for row in mapped["units"]:
        if set(row["ratings"]) != set(DIMENSIONS):
            raise ValueError("V2 dimension names required")
        row["ratings"] = {old: row["ratings"][new] for old, new in NAMES.items()}
    result = v1.human_review(legacy, mapped)
    if result["metrics"] is not None:
        result["metrics"] = renamed_metrics(result["metrics"])
    return result


def locator_diagnostics(cases):
    """Reuse QH-32 resolver for diagnostics only; no publication/partial acceptance."""
    result = {}
    for name, case in cases.items():
        candidates = []
        for item in case["output"]["items"]:
            try:
                _, audit = citations.resolve_output_citations(
                    {"items": [item]}, source=case["source"]
                )
                candidates.append(
                    {
                        "local_id": item["local_id"],
                        "traceable": True,
                        "corrected_spans": sum(
                            x["changed"] for x in audit["citations"]
                        ),
                    }
                )
            except citations.CitationResolutionError as exc:
                candidates.append(
                    {
                        "local_id": item["local_id"],
                        "traceable": False,
                        "issues": list(exc.issues),
                    }
                )
        try:
            citations.resolve_output_citations(case["output"], source=case["source"])
            batch = "citation_derivation_accepted_not_semantic_approval"
        except citations.CitationResolutionError:
            batch = "rejected_whole_batch"
        result[name] = {
            "batch": batch,
            "candidate_diagnostics_not_publication": candidates,
        }
    return result


def evaluate(b, cases, review=None):
    legacy = legacy_units(b)
    proposed = v1.summarize(
        legacy["units"], {u["id"]: u["draft_ratings"] for u in legacy["units"]}
    )
    return {
        "benchmark_version": 2,
        "benchmark_sha256": v1.digest(b),
        "rubric_sha256": b["rubric"]["sha256"],
        "status": "D1-D5 approved; proposed unit judgments pending personal verification",
        "inventory": {
            "review_units": len(b["units"]),
            "original_source_propositions": 46,
            "active_source_propositions": sum(
                u["coverage_scope"] == "active" for u in b["units"]
            ),
            "historical_reconstructible": [
                u["id"]
                for u in b["units"]
                if u["coverage_scope"] == "historical_reconstructible"
            ],
        },
        "provisional_assistant_metrics": renamed_metrics(proposed),
        "human_review": human_review(
            b, review if review is not None else review_template(b)
        ),
        "original_locator_metrics_unchanged": v1.locators(cases),
        "citation_resolution_diagnostics": locator_diagnostics(cases),
        "new_inference_requests": 0,
        "comparison_limit": "V1/v2 rubric, applicability and annotations changed; outputs unchanged. No model-quality gain, composite score or independent semantic accuracy inferred.",
    }


def slug(value):
    return value.replace(".", "-").replace("_", "-")


def md_json(value):
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def render(b, cases, rubric):
    source_ids, sources, payloads = {}, [], []
    source_keys = {}
    for name, case in cases.items():
        key = v1.digest(case["source"])
        if key not in source_keys:
            source_keys[key] = "source-" + slug(name)
            source_asset = (
                "../qh8-mistral-20261016/" + name + "/source.json"
                if case["kind"] == "frozen_mistral"
                else "../../../apps/api/tests/fixtures/qh33/benchmark-v2.json"
            )
            sources += [
                '<a id="' + source_keys[key] + '"></a>',
                "## Fonte " + name,
                "",
                "[Identità, turni e metadati originali]("
                + source_asset
                + ") · source revision `"
                + case["source"]["id"]
                + "`. Il tempo di acquisizione non sostituisce quello del fatto.",
                "",
                "```text\n" + case["source"]["content"].rstrip() + "\n```",
                "",
            ]
        source_ids[name] = source_keys[key]
        payloads += [
            '<a id="output-' + slug(name) + '"></a>',
            "## Output " + name,
            "",
            "Mistral originale congelato."
            if case["kind"] == "frozen_mistral"
            else "Controllo scritto per il benchmark: non generato da Mistral.",
            "",
            md_json(case["output"]),
            "",
        ]
    cases_md = "\n".join(
        [
            "# V2 — fonti originali e payload completi",
            "",
            "14 fonti distinte, 4 output Mistral originali e 20 controlli scritti. Nessuna correzione ai payload. Fonte condivisa fra good/mutated leggibile una sola volta.",
            "",
            *sources,
            *payloads,
        ]
    )
    matrix = [
        "# QH-33 v2 — matrice per la verifica personale",
        "",
        "**D1–D5 approvate; verifica personale delle 74 unità NON attestata.** Tutti i giudizi sotto sono proposti dall’assistente. Accettare un NO conferma il difetto, non la correttezza del candidato.",
        "",
        "★ = attenzione particolare: difetto/parzialità, storia esclusa dal coverage attivo o riferimento precisato. Anche le righe senza ★ richiedono la tua verifica. Ogni ID apre la motivazione; fonte e output sono collegamenti ai testi/payload completi.",
        "",
        "AC copertura attiva · SS sostegno semantico · A attori · N negazioni · T temporalità · U incertezza · CT tracciabilità della citazione. OK / PARZ / NO / — = soddisfatto / parziale / non soddisfatto / non applicabile. CT può essere OK con SS NO; CT non certifica il significato.",
        "",
        "Leggi prima le fonti condivise e i payload completi, poi verifica le 74 righe. Il template personale è vuoto: nessuna approvazione viene dedotta dai giudizi qui mostrati.",
        "",
        "74 ID conservati; 46 proposizioni originali, 44 nel coverage attivo. Due dubbi storici restano verificabili nelle fonti, non sono diventati pass. Nessun indice aggregato.",
        "",
        "[Rubrica](rubric.it.md) · [Metriche provvisorie](metrics.json) · [Template personale vuoto](review-template.json) · [Tutti i dettagli](unit-details.it.md)",
        "",
        "| ID | AC | SS | A | N | T | U | CT | Fonte | Output | Criticità / ambito |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    details = [
        "# V2 — motivazioni delle 74 unità",
        "",
        "Proposte dell’assistente. Nessuna firma, attestazione o decisione personale precompilata.",
        "",
    ]
    short = {"pass": "OK", "partial": "PARZ", "fail": "NO", "n/a": "—"}
    for u in b["units"]:
        attention = bool(
            u["decisions_applied"]
            or any(v in {"partial", "fail"} for v in u["draft_ratings"].values())
        )
        issue = (
            ", ".join(x.replace("_", " ") for x in u["issues"])
            or "Nessuna criticità proposta"
        )
        if u["coverage_scope"] == "historical_reconstructible":
            issue = "Storica, ricostruibile; fuori coverage attivo"
        matrix.append(
            "| "
            + ("★ " if attention else "")
            + "["
            + u["id"]
            + "](unit-details.it.md#unit-"
            + slug(u["id"])
            + ") | "
            + " | ".join(short[u["draft_ratings"][d]] for d in DIMENSIONS)
            + " | ["
            + u["source_evidence"]["turn_id"]
            + "](case-payloads.it.md#"
            + source_ids[u["case"]]
            + ") | [payload](case-payloads.it.md#output-"
            + slug(u["case"])
            + ") | "
            + issue.replace("|", "\\|")
            + " |"
        )
        evidence = u["source_evidence"]
        claims = [
            {
                "pointer": a["pointer"],
                "value": v1.pointer(cases[u["case"]]["output"], a["pointer"]),
            }
            for a in u["anchors"]
        ]
        details += [
            '<a id="unit-' + slug(u["id"]) + '"></a>',
            "## " + u["id"],
            "",
            "[Matrice](review-matrix.it.md) · [Fonte completa](case-payloads.it.md#"
            + source_ids[u["case"]]
            + ") · [Output completo](case-payloads.it.md#output-"
            + slug(u["case"])
            + ")",
            "",
            "**Lettura proposta:** " + u["meaning"],
            "",
            "**Ambito:** " + u["coverage_scope"] + ". Verifica personale: pending.",
            "",
            "**Evidenza originale:** source revision `"
            + cases[u["case"]]["source"]["id"]
            + "`, turno `"
            + evidence["turn_id"]
            + "`, Unicode `["
            + str(evidence["start"])
            + ","
            + str(evidence["end"])
            + ")`.",
            "",
            "> " + evidence["quote"],
            "",
            "**Campi originali indicati** (non sostituiscono il payload completo):",
            "",
            md_json(claims)
            if claims
            else "Nessun claim estratto: verificare l’assenza nel payload completo.",
            "",
            "| Dimensione | Proposta | Motivazione |",
            "| --- | --- | --- |",
        ]
        details += [
            "| "
            + rubric["dimensions"][d]["label_it"]
            + " | "
            + short[u["draft_ratings"][d]]
            + " | "
            + u["dimension_rationales_it"][d].replace("|", "\\|")
            + " |"
            for d in DIMENSIONS
        ]
        details += ["", "**Criticità:** " + issue + ".", ""]
    rub = [
        "# Rubrica v2 — decisioni approvate, unità da verificare",
        "",
        "D1–D5 approvate dal proprietario. Nessuna attestazione di indipendenza, completezza o verifica personale è contenuta nell’approvazione. Le annotazioni restano proposte dell’assistente.",
        "",
    ]
    for d in DIMENSIONS:
        rub += [
            "## " + rubric["dimensions"][d]["label_it"] + " (`" + d + "`)",
            "",
            rubric["dimensions"][d]["definition_it"],
            "",
        ]
    rub += [
        "## Verifica personale e limiti",
        "",
        "Tutti i 74 ID, incluse le due unità storiche, devono essere verificati. Il template lascia reviewer/reviewed_at/independence null, completezza e payload false, decisioni pending e rating null. Nessun copia/incolla automatico dei rating proposti.",
        "",
        "Per ottenere metriche personali occorrono accettazione di ogni giudizio applicabile, identificatore e data con fuso del revisore, attestazioni esplicite di indipendenza, completezza del riferimento e verifica dei payload. Un’accettazione può convalidare un NO. L’importatore non autentica un essere umano; registra solo attestazioni effettivamente fornite. Modifiche di applicabilità richiedono una nuova versione.",
        "",
        "V1 rimane integra. Il cambio di coverage e rubrica non misura miglioramento delle estrazioni o del LLM. Niente merge, Jira DONE o inferenza autorizzati. Il successivo protocollo Mistral resta preparato e non eseguito.",
    ]
    return {
        "review-matrix.it.md": "\n".join(matrix),
        "unit-details.it.md": "\n".join(details),
        "case-payloads.it.md": cases_md,
        "rubric.it.md": "\n".join(rub),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    b, cases, rubric = load_benchmark()
    metrics = evaluate(
        b, cases, v1.read_json(args.review) if args.review is not None else None
    )
    material = render(b, cases, rubric)
    args.out.mkdir(parents=True, exist_ok=False)
    for name, value in material.items():
        (args.out / name).write_text(value.rstrip() + "\n")
    for name, value in {
        "metrics.json": metrics,
        "review-template.json": review_template(b),
    }.items():
        (args.out / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        )
    print(
        json.dumps(
            {
                "version": 2,
                "units": len(b["units"]),
                "personal_review": metrics["human_review"]["status"],
                "provider_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
