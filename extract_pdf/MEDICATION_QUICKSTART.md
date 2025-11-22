# Quick Start: Medication Data Extraction

## What You Get

Automatically extract medication information from PDFs and enrich missing data using FDA API.

## Example Input (PDF)

```
Patient Medication List:
- Amoxicillin 500mg three times daily
- Lisinopril started 2025-01-15
- Metformin twice daily for diabetes
```

## Example Output (JSON)

```json
{
  "medication_history": [
    {
      "medication_id": "med_001",
      "name": "Amoxicillin",
      "generic_name": "Amoxicillin",
      "strength": "500 mg",
      "form": "Capsule",
      "route": "Oral",
      "frequency_raw": "three times daily",
      "frequency_standard": "TID",
      "timing": ["Morning", "Afternoon", "Night"],
      "fda_data": {
        "manufacturer": "Sandoz Inc",
        "drug_class": "Penicillin Antibacterial",
        "warnings": ["Hypersensitivity reactions"],
        "ndc": "0781-1234-56"
      }
    },
    {
      "medication_id": "med_002",
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
      "medication_id": "med_003",
      "name": "Metformin",
      "generic_name": "Metformin Hydrochloride",
      "strength": "1000 mg",
      "form": "Tablet",
      "route": "Oral",
      "frequency_standard": "BID",
      "indication": "diabetes",
      "fda_data": {
        "manufacturer": "Teva Pharmaceuticals",
        "drug_class": "Biguanide Antidiabetic"
      }
    }
  ]
}
```

## What Gets Auto-Filled from FDA

When your PDF is missing medication details, the system automatically fills:

✅ **Generic Name** - Scientific name of the drug  
✅ **Strength** - Dosage strength (e.g., 500 mg, 10 ml)  
✅ **Form** - Tablet, Capsule, Liquid, Injection, etc.  
✅ **Route** - Oral, Topical, IV, etc.  
✅ **Manufacturer** - Drug manufacturer name  
✅ **Drug Class** - Pharmacological classification  
✅ **Warnings** - FDA safety warnings  
✅ **Interactions** - Known drug interactions  
✅ **NDC** - National Drug Code  

## Frequency Codes

The system understands and standardizes medication frequency:

| PDF Says | System Uses |
|----------|-------------|
| "once daily" | QD |
| "twice daily" | BID |
| "three times daily" | TID |
| "four times daily" | QID |
| "every 6 hours" | Q6H |
| "at bedtime" | QHS |
| "as needed" | PRN |

## Required vs Optional Fields

### ✅ Required (must be in PDF)
- Medication name
- Start date

### 🔄 Auto-enriched (FDA fills if missing)
- Generic name
- Strength
- Form
- Route
- Manufacturer
- Warnings

### 📝 Optional (from PDF if available)
- Dosage
- Frequency
- Duration
- Prescriber
- Instructions
- Indication
- End date

## Running the System

```powershell
# Simple command
crewai run path/to/medical_record.pdf

# Output files created:
# - formatted_data.json (initial extraction)
# - enriched_data.json (after FDA lookup)
# - api_response.json (API submission result)
```

## Workflow

```
1. PDF → Extract medications
2. Map to JSON schema
3. Identify missing data
4. Query FDA API
5. Fill missing fields
6. Validate complete data
7. POST to your API
```

## FDA API - No Setup Required

The system uses the free FDA openFDA API:
- ✅ No API key needed
- ✅ No registration required
- ✅ 1000 requests/minute limit
- ✅ Public government data

## Example Scenarios

### Scenario 1: Incomplete Prescription
**PDF**: "Patient taking Lipitor"

**System Adds**:
- Generic: Atorvastatin Calcium
- Strength: 10 mg (common strength)
- Form: Tablet
- Route: Oral
- Class: HMG-CoA Reductase Inhibitor
- Warnings: Liver enzyme monitoring required

### Scenario 2: Handwritten Notes
**PDF**: "Start Amox 500 TID x 7d"

**System Interprets**:
- Name: Amoxicillin
- Strength: 500 mg
- Frequency: TID (three times daily)
- Duration: 7 days
- **FDA Adds**: Form, Route, Manufacturer, Warnings

### Scenario 3: Multiple Medications
**PDF**: Lists 10 medications with varying detail levels

**System**:
- Extracts all 10
- Identifies which need enrichment
- Queries FDA for each incomplete record
- Creates complete dataset

## Validation

Before submitting to your API, the system ensures:

✅ All required fields present  
✅ Dates in correct format (YYYY-MM-DD)  
✅ Strength has units (mg, g, ml)  
✅ Form is valid enum value  
✅ Frequency codes standardized  
✅ JSON matches your schema  

## Troubleshooting

**Q: Medication not found in FDA database?**  
A: System keeps original PDF data, marks FDA data as null

**Q: Wrong medication matched?**  
A: Provide more specific name or brand name in PDF

**Q: Missing dosage information?**  
A: FDA provides available strengths; manual review may be needed

**Q: Generic vs Brand names?**  
A: System handles both; FDA returns both names

## Next Steps

1. Review [MEDICATION_ENRICHMENT.md](MEDICATION_ENRICHMENT.md) for detailed documentation
2. Customize [api_schema.json](src/extract_pdf/config/api_schema.json) for your needs
3. Test with sample medical PDFs
4. Configure your API endpoint in `.env`

---

**Start extracting and enriching medication data now!** 💊✨
