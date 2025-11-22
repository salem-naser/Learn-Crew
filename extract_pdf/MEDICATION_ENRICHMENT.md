# Medication Data Enrichment with FDA Integration

## Overview

This system automatically enriches incomplete medication data extracted from PDFs by integrating with the FDA openFDA API. When medication information is missing critical details like dosage, strength, form, or route, the system queries the FDA database to fill in the gaps.

## How It Works

### Workflow

```
PDF → Extract Medications → Map to Schema → FDA Enrichment → Validation → API POST
```

1. **PDF Extraction**: Extract medication names and available details from PDF
2. **Initial Mapping**: Map extracted data to the medication_history schema
3. **FDA Enrichment**: Query FDA API for missing medication details
4. **Data Completion**: Fill in missing fields with FDA data
5. **Validation**: Ensure complete data matches schema
6. **API Submission**: POST enriched data to your API

### Medication Fields

The system handles the following medication fields:

#### Required Fields (from PDF)
- `medication_id`: Unique identifier
- `name`: Medication name (brand or generic)
- `start_date`: When medication was started

#### Auto-Enriched Fields (from FDA if missing)
- `generic_name`: Scientific/generic name
- `strength`: Dosage strength (e.g., "500 mg")
- `form`: Dosage form (Tablet, Capsule, Liquid, etc.)
- `route`: Route of administration (Oral, Topical, etc.)
- `dosage`: Amount per administration
- `frequency_standard`: Standardized code (QD, BID, TID, QID)

#### FDA Additional Data
- `fda_data.ndc`: National Drug Code
- `fda_data.manufacturer`: Manufacturer name
- `fda_data.drug_class`: Pharmacological class
- `fda_data.warnings`: FDA warnings and precautions
- `fda_data.interactions`: Known drug interactions

## Medication Record Example

### Incomplete Record (from PDF)
```json
{
  "medication_id": "med_001",
  "name": "Amoxicillin",
  "frequency_raw": "Three times daily",
  "start_date": "2025-02-22",
  "prescriber": "Dr. Ahmed",
  "instructions": "Take after meals"
}
```

### Enriched Record (after FDA lookup)
```json
{
  "medication_id": "med_001",
  "name": "Amoxicillin",
  "generic_name": "Amoxicillin",
  "strength": "500 mg",
  "form": "Capsule",
  "route": "Oral",
  "frequency_raw": "Three times daily",
  "frequency_standard": "TID",
  "timing": ["Morning", "Afternoon", "Night"],
  "duration": "7 days",
  "indication": "Bacterial infection",
  "start_date": "2025-02-22",
  "prescriber": "Dr. Ahmed",
  "instructions": "Take after meals",
  "fda_data": {
    "ndc": "0781-1234-56",
    "manufacturer": "Sandoz Inc",
    "drug_class": "Penicillin Antibacterial",
    "warnings": [
      "Hypersensitivity reactions",
      "Clostridium difficile associated diarrhea"
    ],
    "interactions": [
      "May reduce effectiveness of oral contraceptives",
      "Increased risk of rash with allopurinol"
    ]
  },
  "status": "active"
}
```

## Frequency Code Standardization

The system standardizes medication frequency to medical abbreviations:

| Raw Text | Standard Code | Meaning |
|----------|--------------|---------|
| Once daily | QD | Once a day |
| Twice daily | BID | Twice a day |
| Three times daily | TID | Three times a day |
| Four times daily | QID | Four times a day |
| At bedtime | QHS | Before sleep |
| As needed | PRN | When necessary |
| Every 4 hours | Q4H | Every 4 hours |
| Every 6 hours | Q6H | Every 6 hours |
| Every 8 hours | Q8H | Every 8 hours |
| Every 12 hours | Q12H | Every 12 hours |

## FDA API Integration

### API Endpoint
The system uses the FDA openFDA Drug Label API:
```
https://api.fda.gov/drug/label.json
```

### Query Process
1. Search by medication name (brand or generic)
2. Retrieve first matching result
3. Extract relevant fields:
   - Generic name
   - Brand name
   - Manufacturer
   - Route of administration
   - Dosage form
   - Strength information
   - Drug class
   - Warnings
   - Indications
   - Drug interactions

### No API Key Required
The openFDA API is free and does not require authentication for basic usage (up to 1000 requests per minute).

## Configuration

### API Schema

The medication_history schema is defined in `config/api_schema.json`:

```json
{
  "medication_history": {
    "type": "array",
    "items": {
      "type": "object",
      "required": ["medication_id", "name", "start_date"],
      "properties": {
        "medication_id": {"type": "string"},
        "name": {"type": "string"},
        "generic_name": {"type": ["string", "null"]},
        "strength": {"type": ["string", "null"]},
        "form": {"type": ["string", "null"]},
        "route": {"type": ["string", "null"]},
        // ... additional fields
      }
    }
  }
}
```

### Agent Configuration

The medication enrichment agent is defined in `config/agents.yaml`:

```yaml
medication_enrichment_agent:
  role: Medical Data Enrichment and FDA Integration Specialist
  goal: Validate medication data and enrich missing information using FDA database
  backstory: >
    Pharmaceutical data specialist with FDA knowledge who fills missing
    medication details using the FDA Lookup Tool.
```

### Task Configuration

The enrichment task is defined in `config/tasks.yaml`:

```yaml
enrich_medication_data_task:
  description: >
    Review medication_history and identify medications with missing data.
    Use FDA Medication Lookup tool to fill in missing fields.
  expected_output: >
    Updated JSON with enriched medication_history from FDA database.
  agent: medication_enrichment_agent
```

## Usage Examples

### Example 1: Basic Medication Extraction

**PDF Content:**
```
Patient: John Doe
Medications:
- Lisinopril, started 2025-01-15
- Metformin 1000mg twice daily
```

**System Output:**
```json
{
  "medication_history": [
    {
      "medication_id": "med_001",
      "name": "Lisinopril",
      "generic_name": "Lisinopril",
      "strength": "10 mg",
      "form": "Tablet",
      "route": "Oral",
      "start_date": "2025-01-15",
      "fda_data": {
        "manufacturer": "Accord Healthcare",
        "drug_class": "ACE Inhibitor",
        "warnings": ["Angioedema", "Hypotension"]
      }
    },
    {
      "medication_id": "med_002",
      "name": "Metformin",
      "generic_name": "Metformin Hydrochloride",
      "strength": "1000 mg",
      "form": "Tablet",
      "route": "Oral",
      "frequency_standard": "BID",
      "start_date": "2025-01-15",
      "fda_data": {
        "manufacturer": "Teva Pharmaceuticals",
        "drug_class": "Biguanide Antidiabetic"
      }
    }
  ]
}
```

### Example 2: Complex Prescription

**PDF Content:**
```
Rx: Amoxicillin-Clavulanate 875-125mg
Sig: 1 tab PO BID x 10 days
Indication: Sinusitis
Prescriber: Dr. Sarah Johnson, NPI: 1234567890
```

**System Output:**
```json
{
  "medication_id": "med_003",
  "name": "Amoxicillin-Clavulanate",
  "generic_name": "Amoxicillin and Clavulanate Potassium",
  "strength": "875-125 mg",
  "form": "Tablet",
  "route": "Oral",
  "frequency_raw": "1 tab PO BID x 10 days",
  "frequency_standard": "BID",
  "dosage": "1 tablet",
  "duration": "10 days",
  "indication": "Sinusitis",
  "prescriber": "Dr. Sarah Johnson",
  "prescriber_npi": "1234567890",
  "fda_data": {
    "ndc": "0093-2275-01",
    "manufacturer": "Teva Pharmaceuticals",
    "drug_class": "Penicillin Antibacterial",
    "warnings": [
      "Hepatic dysfunction",
      "Hypersensitivity reactions"
    ]
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Medication Not Found in FDA Database

**Problem**: FDA API returns no results for medication name

**Solutions**:
- Try alternative spellings or brand names
- Check for generic name vs brand name
- Verify medication name spelling in PDF
- Some medications may not be in FDA database (supplements, compounded medications)

#### 2. Incomplete FDA Data

**Problem**: FDA returns partial information

**Solution**: The system preserves any data from PDF and only adds available FDA fields. Missing FDA fields will be `null`.

#### 3. Multiple FDA Matches

**Problem**: Multiple medications match the search

**Solution**: System uses first match. For better accuracy, extract brand name from PDF when available.

#### 4. API Rate Limiting

**Problem**: Too many FDA API requests

**Solution**: FDA allows 240 requests per minute without key, 1000 with key. System handles standard workflows without issues.

### Validation Errors

#### Missing Required Fields

**Error**: `medication_id, name, or start_date missing`

**Fix**: Ensure PDF contains at least medication name and start date. System generates medication_id if not in PDF.

#### Invalid Date Format

**Error**: `start_date must be YYYY-MM-DD`

**Fix**: Check date extraction from PDF. System should convert various date formats.

#### Invalid Strength Pattern

**Error**: `strength must match pattern: number + unit`

**Fix**: Ensure strength includes both number and unit (e.g., "500 mg" not "500")

## Best Practices

### 1. PDF Format
- Ensure medication sections are clearly labeled
- Include dates in recognizable format
- Provide prescriber information
- List strength and frequency when available

### 2. Data Quality
- Review extracted medications before enrichment
- Verify critical fields (name, dosage, dates)
- Check for duplicate medications
- Validate against patient records

### 3. FDA Integration
- Use brand names when available for better matches
- Review FDA warnings for clinical relevance
- Cross-reference drug interactions
- Keep enriched data for audit trails

### 4. Error Handling
- Log medications that couldn't be enriched
- Flag incomplete records for manual review
- Maintain original PDF data
- Document data sources (PDF vs FDA)

## Output Files

The system generates these files:

1. **formatted_data.json** - Initial extracted and mapped data
2. **enriched_data.json** - Data after FDA enrichment
3. **api_response.json** - Response from final API submission

## API Schema Update

The complete medication_history schema includes:

- **Identification**: medication_id, name, generic_name
- **Dosage**: strength, form, route, dosage
- **Frequency**: frequency_raw, frequency_standard, timing
- **Duration**: duration, start_date, end_date
- **Clinical**: indication, prescriber, prescriber_npi, instructions
- **Status**: status, side_effects
- **FDA Data**: ndc, manufacturer, drug_class, warnings, interactions
- **Metadata**: Additional custom fields

## Integration with Your API

When POSTing to your API, the complete payload includes:

```json
{
  "user_information": { ... },
  "user_history": [ ... ],
  "medication_history": [
    {
      // Fully enriched medication records with FDA data
    }
  ]
}
```

## FDA Data Attribution

Data from the FDA openFDA API should be attributed:

> Medication data enhanced using the openFDA API, provided by the U.S. Food and Drug Administration. The FDA does not warrant or assume any liability for the accuracy or completeness of the data.

## Further Resources

- [openFDA API Documentation](https://open.fda.gov/apis/)
- [FDA Drug Labels](https://open.fda.gov/apis/drug/label/)
- [National Drug Code Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory)
- [Medication Terminology Standards](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3064864/)

---

**Ready to enrich your medication data!** 💊
