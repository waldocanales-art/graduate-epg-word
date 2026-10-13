"""Clasificación conservadora de porcentajes escritos en nombres Turnitin.

Nunca acredita un resultado real: únicamente clasifica pistas textuales para
la revisión del PDF original. Evita confundir escritura IA con similitud.
"""
import re
import unicodedata

PERCENT = re.compile(r"(?<![0-9])([0-9]{1,3})\s*%")
AI_AFTER = re.compile(r"^[-_\s]*(?:IA|AI|ESCRITURA[-_\s]*(?:CON[-_\s]*)?IA)(?:[-_\s.]|$)")
AI_BEFORE = re.compile(r"(?:^|[-_\s])(?:IA|AI|ESCRITURA[-_\s]*(?:CON[-_\s]*)?IA)[-_\s]*$")
SIM_AFTER = re.compile(r"^[-_\s]*(?:SIMILITUD|SIMILARITY|COINCIDENCIA)(?:[-_\s.]|$)")
SIM_BEFORE = re.compile(r"(?:^|[-_\s])(?:SIMILITUD|SIMILARITY|COINCIDENCIA)[-_\s]*$")


def extract_scores(filename):
    """Porcentajes por nombre de archivo, no por lectura o validación del informe."""
    plain = unicodedata.normalize("NFKD", str(filename or ""))
    plain = "".join(c for c in plain if not unicodedata.combining(c)).upper()
    sim, ai, ambiguous = [], [], []
    for m in PERCENT.finditer(plain):
        value = int(m.group(1))
        before, after = plain[max(0, m.start()-45):m.start()], plain[m.end():m.end()+45]
        if value > 100:
            ambiguous.append(value)
        elif AI_AFTER.match(after) or AI_BEFORE.search(before):
            ai.append(value)
        elif SIM_AFTER.match(after) or SIM_BEFORE.search(before):
            sim.append(value)
        else:
            ambiguous.append(value)
    assumed = False
    # Compatibilidad histórica con un único porcentaje en un archivo
    # 'Turnitin', siempre marcado como inferencia no certificada.
    if len(ambiguous) == 1 and not sim and not ai and "TURNITIN" in plain:
        sim.append(ambiguous.pop())
        assumed = True
    return {
        "percentages_named": [int(v) for v in PERCENT.findall(plain)],
        "similarity_percentages_named": sim,
        "ai_percentages_named": ai,
        "unclassified_percentages_named": ambiguous,
        "similarity_inferred_from_filename": assumed,
        "content_verified": False,
    }
