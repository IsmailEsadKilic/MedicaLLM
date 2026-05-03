import re

# Severity pattern matching - ordered from most to least severe
_SEVERITY_CONTRAINDICATED = re.compile(
    r"contraindicated|do not use|must not|should not be used|avoid concomitant"
    r"|absolute.+prohibition|strictly prohibited|never.+together|forbidden"
    r"|not.+recommended.+under.+any|completely avoid",
    re.IGNORECASE,
)

_SEVERITY_CRITICAL = re.compile(
    r"life.?threatening|fatal|death|lethal|mortality"
    r"|cardiac arrest|respiratory arrest|anaphylaxis|anaphylactic"
    r"|severe.+organ.+failure|acute.+liver.+failure|acute.+kidney.+failure"
    r"|status epilepticus|coma|stroke|myocardial infarction"
    r"|pulmonary embolism|ventricular fibrillation",
    re.IGNORECASE,
)

_SEVERITY_MAJOR = re.compile(
    r"serotonin syndrome|neuroleptic malignant|malignant hyperthermia"
    r"|hemorrhag|severe.+bleeding|uncontrolled.+bleeding|gastrointestinal.+bleeding"
    r"|QT.?prolong|torsade|torsades de pointes|ventricular.+arrhythmi"
    r"|seizure|convulsion|severe.+hypotension|hypertensive crisis|hypertensive emergency"
    r"|severe.+hypoglycemia|diabetic.+ketoacidosis|hyperosmolar"
    r"|agranulocytosis|aplastic.+anemia|thrombocytopenia.+purpura"
    r"|stevens.?johnson|toxic.+epidermal.+necrolysis|severe.+skin.+reaction"
    r"|rhabdomyolysis|acute.+renal.+failure|hepatotoxicity|severe.+hepatic"
    r"|respiratory.+depression|severe.+respiratory|bronchospasm.+severe"
    r"|angioedema|severe.+allergic|anaphylactoid"
    r"|suicidal|severe.+psychiatric|psychosis|mania.+severe"
    r"|bone.+marrow.+suppression|pancytopenia",
    re.IGNORECASE,
)

_SEVERITY_MODERATE_HIGH = re.compile(
    r"significant.+increase|significant.+decrease|significantly.+increase|significantly.+decrease"
    r"|substantially.+increase|substantially.+decrease|markedly.+increase|markedly.+decrease"
    r"|greatly.+increase|greatly.+decrease|considerable.+increase|considerable.+decrease"
    r"|major.+increase|major.+decrease|pronounced.+effect"
    r"|serious.+adverse|serious.+side.+effect|hospitalization.+may.+be.+required"
    r"|emergency.+medical|urgent.+medical|immediate.+medical"
    r"|dose.+adjustment.+required|dose.+reduction.+required|discontinue.+if"
    r"|frequent.+monitoring|intensive.+monitoring|close.+supervision"
    r"|bleeding.+risk|increased.+bleeding|hemorrhage.+risk"
    r"|hypotension.+risk|syncope|fainting|dizziness.+severe"
    r"|confusion|delirium|altered.+mental|cognitive.+impairment"
    r"|renal.+impairment|kidney.+damage|nephrotoxic"
    r"|liver.+damage|hepatic.+impairment|elevated.+liver.+enzymes.+significant"
    r"|arrhythmia|irregular.+heart|palpitation.+severe"
    r"|hypoglycemia.+risk|blood.+sugar.+dangerously|glucose.+control.+difficult",
    re.IGNORECASE,
)

_SEVERITY_MODERATE = re.compile(
    r"increas.+risk|decreas.+effect|alter.+metabolism|may.+increase|may.+decrease"
    r"|can.+increase|can.+decrease|might.+increase|might.+decrease"
    r"|monitor.+closely|monitor.+for|monitoring.+recommended|caution.+advised"
    r"|adjust.+dose|dose.+adjustment|dosage.+modification|titrate"
    r"|enhance.+effect|potentiate|augment.+effect|additive.+effect"
    r"|reduce.+efficacy|diminish.+effect|decrease.+effectiveness|impair.+efficacy"
    r"|plasma.+concentration|serum.+level|blood.+level|auc.+increase|auc.+decrease"
    r"|clearance.+decrease|clearance.+reduce|half.?life.+prolong|elimination.+reduce"
    r"|absorption.+affect|bioavailability.+affect|metabolism.+affect"
    r"|cyp.+inhibit|cyp.+induc|enzyme.+inhibit|enzyme.+induc"
    r"|p.?glycoprotein|pgp.+inhibit|transporter.+affect"
    r"|adverse.+effect|side.+effect.+increase|toxicity.+increase"
    r"|therapeutic.+effect.+reduce|clinical.+response.+reduce"
    r"|sedation|drowsiness|somnolence|cns.+depression"
    r"|nausea|vomiting|gastrointestinal.+effect|gi.+disturbance"
    r"|headache|dizziness|vertigo|lightheaded"
    r"|electrolyte.+imbalance|hypokalemia|hyperkalemia|hyponatremia"
    r"|dehydration|fluid.+retention|edema",
    re.IGNORECASE,
)

_SEVERITY_MILD = re.compile(
    r"minor.+effect|slight.+effect|small.+effect|minimal.+effect"
    r"|unlikely.+to.+be.+clinically|not.+clinically.+significant|rarely.+significant"
    r"|generally.+well.+tolerated|usually.+not.+problematic"
    r"|observe|watch.+for|be.+aware|consider"
    r"|mild.+increase|mild.+decrease|modest.+increase|modest.+decrease"
    r"|transient|temporary|short.?term|reversible"
    r"|discomfort|inconvenience|nuisance",
    re.IGNORECASE,
)

def calculate_severity(description: str) -> float:
    """
    Calculate interaction severity from description text using comprehensive pattern matching.
    
    Uses a hierarchical approach checking from most to least severe patterns.
    Considers clinical terminology, pharmacokinetic changes, and adverse event descriptions.
    
    Args:
        description: Interaction description text
    
    Returns:
        float: Severity score from 0.0 (minimal) to 1.0 (contraindicated)
            1.0 = Contraindicated (absolute prohibition)
            0.9 = Critical (life-threatening, fatal outcomes)
            0.8 = Major (serious adverse events, organ damage)
            0.65 = Moderate-High (significant clinical impact, requires intervention)
            0.5 = Moderate (clinically relevant, monitoring needed)
            0.3 = Mild (minor clinical significance)
            0.15 = Minimal (unlikely to be clinically significant)
    """
    if not description:
        return 0.5  # Unknown severity - assume moderate for safety
    
    desc_lower = description.lower()
    
    # Check in order of severity (highest to lowest)
    if _SEVERITY_CONTRAINDICATED.search(desc_lower):
        return 1.0  # Contraindicated
    
    if _SEVERITY_CRITICAL.search(desc_lower):
        return 0.9  # Critical
    
    if _SEVERITY_MAJOR.search(desc_lower):
        return 0.8  # Major
    
    if _SEVERITY_MODERATE_HIGH.search(desc_lower):
        return 0.65  # Moderate-High
    
    if _SEVERITY_MODERATE.search(desc_lower):
        return 0.5  # Moderate
    
    if _SEVERITY_MILD.search(desc_lower):
        return 0.3  # Mild
    
    # If no patterns match, check for some basic indicators
    # Presence of "increase" or "decrease" without other context
    if re.search(r"increase|decrease|affect|alter|change", desc_lower):
        return 0.4  # Low-moderate (some interaction but unclear severity)
    
    return 0.15  # Minimal (no clear severity indicators)