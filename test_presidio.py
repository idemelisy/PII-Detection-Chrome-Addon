# -*- coding: utf-8 -*-
"""
Test script to run Presidio on a sample Turkish text
"""

from presidio_analyzer import AnalyzerEngine
import json


def normalize_entity(entity_type: str) -> str:
    """Normalize Presidio entity types to match extension's expected format."""
    entity_mapping = {
        'PERSON': 'PERSON',
        'EMAIL_ADDRESS': 'EMAIL',
        'PHONE_NUMBER': 'PHONE',
        'LOCATION': 'LOCATION',
        'ORGANIZATION': 'ORGANIZATION',
        'CREDIT_CARD': 'CREDIT_CARD',
        'SSN': 'SSN',
        'IP_ADDRESS': 'IP_ADDRESS',
        'DATE_TIME': 'DATE_TIME',
        'URL': 'URL',
        'US_DRIVER_LICENSE': 'ID',
        'US_PASSPORT': 'ID',
        'US_BANK_NUMBER': 'BANK_ACCOUNT',
        'IBAN_CODE': 'BANK_ACCOUNT',
        'US_SSN': 'SSN',
        'MEDICAL_LICENSE': 'ID',
        'NPI': 'ID',
    }
    return entity_mapping.get(entity_type, entity_type)


def remove_overlapping_entities(entities: list) -> list:
    """
    Remove overlapping entities, keeping the larger or more specific one.
    
    Priority rules:
    1. If entities overlap, keep the larger one (more characters)
    2. If same size, prefer more specific types (EMAIL > URL, PERSON > LOCATION, etc.)
    3. If same size and type priority, prefer higher confidence
    """
    if not entities:
        return []
    
    # Entity type priority (higher number = more priority)
    type_priority = {
        'EMAIL': 10,
        'PHONE': 9,
        'CREDIT_CARD': 8,
        'SSN': 8,
        'BANK_ACCOUNT': 8,
        'ID': 7,
        'PERSON': 6,
        'ORGANIZATION': 5,
        'LOCATION': 4,
        'IP_ADDRESS': 3,
        'URL': 2,
        'DATE_TIME': 1,
    }
    
    # Sort entities by start position, then by end position (descending)
    sorted_entities = sorted(entities, key=lambda e: (e['start'], -e['end']))
    
    non_overlapping = []
    
    for current in sorted_entities:
        current_size = current['end'] - current['start']
        current_priority = type_priority.get(current['type'], 0)
        
        # Check if current entity overlaps with any already added entity
        overlaps = False
        for existing in non_overlapping:
            # Check if they overlap (one contains the other or they intersect)
            if not (current['end'] <= existing['start'] or current['start'] >= existing['end']):
                # They overlap - decide which to keep
                existing_size = existing['end'] - existing['start']
                existing_priority = type_priority.get(existing['type'], 0)
                
                # If current is larger, replace existing
                if current_size > existing_size:
                    non_overlapping.remove(existing)
                    break
                # If same size, prefer higher priority type
                elif current_size == existing_size:
                    if current_priority > existing_priority:
                        non_overlapping.remove(existing)
                        break
                    elif current_priority == existing_priority:
                        # Same priority, prefer higher confidence
                        if current.get('confidence', 0) > existing.get('confidence', 0):
                            non_overlapping.remove(existing)
                            break
                # Current is smaller or same priority, skip it
                overlaps = True
                break
        
        if not overlaps:
            non_overlapping.append(current)
    
    return non_overlapping

# Sample text to test
sample_text = "I am Ayşe , living in Tuzla with my friend Berrin Yılmaz. I will present this to my professors Dr. Demir and Dr. Ceyda Kaya. They live in İstanbul / Türkiye. The phone number is 545 333 66 78. You can reach us from Orta Mah. Üniversite Cad. No:1 Sabancı Üniversitesi. Or you can use these : ceyda.kaya@sabanciuniv.edu, ayse.yildiz@gmail.com .Can you turn these into a formal introductory paragraph?"

print("Testing Presidio on sample text...")
print("\n" + "="*80)
print("SAMPLE TEXT:")
print("="*80)
print(sample_text)
print("\n" + "="*80)

# Initialize Presidio Analyzer
print("\nInitializing Presidio Analyzer...")
try:
    analyzer = AnalyzerEngine()
    print("Presidio Analyzer initialized successfully\n")
except Exception as e:
    print(f"Error initializing Presidio Analyzer: {e}")
    exit(1)

# Analyze the text
print("Analyzing text for PII...")
print("-"*80)

# Try with English first (default)
results_en = analyzer.analyze(text=sample_text, language="en")

# Try with Turkish if available
try:
    results_tr = analyzer.analyze(text=sample_text, language="tr")
except Exception as e:
    print(f"Turkish language not available: {e}")
    results_tr = []

print(f"\nResults with English language model:")
print(f"   Found {len(results_en)} entities\n")

if results_en:
    print("DETECTED ENTITIES:")
    print("-"*80)
    for i, result in enumerate(results_en, 1):
        entity_value = sample_text[result.start:result.end]
        print(f"\n{i}. {result.entity_type}")
        print(f"   Value: '{entity_value}'")
        print(f"   Position: {result.start}-{result.end}")
        print(f"   Confidence: {result.score:.4f}")
else:
    print("No entities detected with English model.")

if results_tr:
    print(f"\n\nResults with Turkish language model:")
    print(f"   Found {len(results_tr)} entities\n")
    print("DETECTED ENTITIES:")
    print("-"*80)
    for i, result in enumerate(results_tr, 1):
        entity_value = sample_text[result.start:result.end]
        print(f"\n{i}. {result.entity_type}")
        print(f"   Value: '{entity_value}'")
        print(f"   Position: {result.start}-{result.end}")
        print(f"   Confidence: {result.score:.4f}")

# Convert to extension format and remove overlaps
print("\n\n" + "="*80)
print("BEFORE REMOVING OVERLAPS:")
print("="*80)
entities_list_before = []
for r in results_en:
    entities_list_before.append({
        "type": normalize_entity(r.entity_type),
        "start": r.start,
        "end": r.end,
        "value": sample_text[r.start:r.end],
        "confidence": round(r.score, 4)
    })
print(f"Found {len(entities_list_before)} entities before overlap removal")

# Remove overlapping entities
entities_list = remove_overlapping_entities(entities_list_before)

print("\n" + "="*80)
print("AFTER REMOVING OVERLAPS:")
print("="*80)
print(f"Found {len(entities_list)} entities after overlap removal")
print("\nDETECTED ENTITIES (after overlap removal):")
print("-"*80)
for i, entity in enumerate(entities_list, 1):
    print(f"\n{i}. {entity['type']}")
    print(f"   Value: '{entity['value']}'")
    print(f"   Position: {entity['start']}-{entity['end']}")
    print(f"   Confidence: {entity['confidence']:.4f}")

# Format results in JSON-like structure
print("\n\n" + "="*80)
print("JSON FORMAT OUTPUT:")
print("="*80)

output = {
    "has_pii": len(entities_list) > 0,
    "detected_entities": entities_list,
    "total_entities": len(entities_list),
    "model_used": "presidio",
    "language": "en"
}

print(json.dumps(output, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("Test complete!")
print("="*80)
