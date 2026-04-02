"""
Guardrails validation specifications for User and Medication schemas.
Provides automatic validation, correction, and reask capabilities.
"""
from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, field_validator, EmailStr
import re


# =======================
# User Schema Guards
# =======================

class AddressGuard(BaseModel):
    """Address validation with auto-correction."""
    street: Optional[str] = Field(default=None, description="Street address")
    city: Optional[str] = Field(default=None, description="City name")
    state: Optional[str] = Field(default=None, description="State or province")
    zip_code: Optional[str] = Field(default=None, description="Postal or ZIP code")
    country: Optional[str] = Field(default=None, description="Country name")
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v):
        if v and not re.match(r'^[A-Za-z0-9\s\-]+$', v):
            # Clean invalid characters
            return re.sub(r'[^A-Za-z0-9\s\-]', '', v)
        return v
    
    @field_validator('state')
    @classmethod
    def normalize_state(cls, v):
        if v:
            # Common state abbreviation normalizations
            state_map = {
                'california': 'CA', 'cal': 'CA',
                'new york': 'NY', 'newyork': 'NY',
                'texas': 'TX', 'tex': 'TX',
                'florida': 'FL', 'fla': 'FL',
            }
            return state_map.get(v.lower(), v.upper() if len(v) <= 2 else v.title())
        return v


class UserInformationGuard(BaseModel):
    """User information validation with guardrails."""
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    full_name: str = Field(..., min_length=1, description="User's full name")
    email: str = Field(..., description="User's email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    address: Optional[AddressGuard] = Field(default=None, description="User address")
    date_of_birth: Optional[str] = Field(default=None, description="Birth date YYYY-MM-DD")
    registration_date: Optional[str] = Field(default=None, description="Registration timestamp")
    account_status: Optional[str] = Field(default=None, description="Account status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format - must contain @')
        # Basic email cleanup
        return v.lower().strip()
    
    @field_validator('phone')
    @classmethod
    def normalize_phone(cls, v):
        if v:
            # Remove common non-numeric chars except + at start
            cleaned = re.sub(r'[^\d+]', '', v)
            if not cleaned.startswith('+') and len(cleaned) == 10:
                cleaned = '+1' + cleaned  # Assume US
            return cleaned
        return v
    
    @field_validator('full_name')
    @classmethod
    def normalize_name(cls, v):
        if v:
            # Title case and clean extra spaces
            return ' '.join(v.split()).title()
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v):
        if v:
            # Try to parse and normalize date formats
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    from datetime import datetime
                    dt = datetime.strptime(v, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return v
    
    @field_validator('account_status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['active', 'inactive', 'suspended', 'pending']
        if v and v.lower() not in valid_statuses:
            return 'pending'  # Default to pending if invalid
        return v.lower() if v else v


class UserHistoryRecordGuard(BaseModel):
    """User history record validation."""
    record_id: str = Field(..., min_length=1, description="Record ID")
    date: str = Field(..., description="Record timestamp")
    type: str = Field(..., description="Record type")
    description: Optional[str] = Field(default=None, description="Record description")
    amount: Optional[float] = Field(default=None, ge=0, description="Transaction amount")
    status: Optional[str] = Field(default=None, description="Record status")
    reference: Optional[str] = Field(default=None, description="Reference number")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['transaction', 'activity', 'update', 'purchase', 'login', 'payment', 'order']
        if v and v.lower() not in valid_types:
            return 'activity'  # Default
        return v.lower()
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['completed', 'pending', 'failed', 'cancelled', 'processing']
        if v and v.lower() not in valid_statuses:
            return 'pending'
        return v.lower() if v else v


class UserDataGuard(BaseModel):
    """Complete user data validation guard."""
    user_information: UserInformationGuard = Field(..., description="User info")
    user_history: List[UserHistoryRecordGuard] = Field(default=[], description="User history")


# =======================
# Medication Schema Guards
# =======================

class FDADataGuard(BaseModel):
    """FDA data validation."""
    ndc: Optional[str] = Field(default=None, description="National Drug Code")
    manufacturer: Optional[str] = Field(default=None, description="Manufacturer")
    drug_class: Optional[str] = Field(default=None, description="Drug class")
    warnings: Optional[List[str]] = Field(default=None, description="FDA warnings")
    interactions: Optional[List[str]] = Field(default=None, description="Drug interactions")


class MedicationRecordGuard(BaseModel):
    """Individual medication record validation with auto-correction."""
    medication_id: str = Field(..., min_length=1, description="Medication record ID")
    name: str = Field(..., min_length=1, description="Medication name")
    generic_name: Optional[str] = Field(default=None, description="Generic name")
    strength: Optional[str] = Field(default=None, description="Medication strength")
    form: Optional[str] = Field(default=None, description="Medication form")
    route: Optional[str] = Field(default=None, description="Administration route")
    frequency_raw: Optional[str] = Field(default=None, description="Raw frequency text")
    frequency_standard: Optional[str] = Field(default=None, description="Standard frequency")
    timing: Optional[List[str]] = Field(default=None, description="Timing instructions")
    dosage: Optional[str] = Field(default=None, description="Dosage amount")
    duration: Optional[str] = Field(default=None, description="Treatment duration")
    indication: Optional[str] = Field(default=None, description="Prescription reason")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date YYYY-MM-DD")
    prescriber: Optional[str] = Field(default=None, description="Prescriber name")
    prescriber_npi: Optional[str] = Field(default=None, description="Prescriber NPI")
    instructions: Optional[str] = Field(default=None, description="Special instructions")
    side_effects: Optional[List[str]] = Field(default=None, description="Side effects")
    fda_data: Optional[FDADataGuard] = Field(default=None, description="FDA data")
    status: Optional[str] = Field(default=None, description="Medication status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    
    @field_validator('strength')
    @classmethod
    def normalize_strength(cls, v):
        if v:
            # Normalize strength format (e.g., "500mg" -> "500 mg")
            match = re.match(r'^(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|IU|%)$', v.replace(' ', ''), re.I)
            if match:
                return f"{match.group(1)} {match.group(2).lower()}"
            # Try to extract number and unit
            num_match = re.search(r'(\d+(?:\.\d+)?)', v)
            unit_match = re.search(r'(mg|g|ml|mcg|IU|%)', v, re.I)
            if num_match and unit_match:
                return f"{num_match.group(1)} {unit_match.group(1).lower()}"
        return v
    
    @field_validator('form')
    @classmethod
    def normalize_form(cls, v):
        valid_forms = ['Tablet', 'Capsule', 'Liquid', 'Injection', 'Cream', 
                       'Ointment', 'Patch', 'Inhaler', 'Drop', 'Suppository', 'Other']
        if v:
            v_lower = v.lower().strip()
            form_map = {
                'tab': 'Tablet', 'tabs': 'Tablet', 'tablet': 'Tablet',
                'cap': 'Capsule', 'caps': 'Capsule', 'capsule': 'Capsule',
                'liq': 'Liquid', 'liquid': 'Liquid', 'solution': 'Liquid', 'syrup': 'Liquid',
                'inj': 'Injection', 'injection': 'Injection',
                'cream': 'Cream', 'oint': 'Ointment', 'ointment': 'Ointment',
                'patch': 'Patch', 'inhaler': 'Inhaler', 'drop': 'Drop', 'drops': 'Drop',
            }
            normalized = form_map.get(v_lower)
            if normalized:
                return normalized
            # Title case if in valid forms
            for valid in valid_forms:
                if v_lower == valid.lower():
                    return valid
            return 'Other'
        return v
    
    @field_validator('route')
    @classmethod
    def normalize_route(cls, v):
        valid_routes = ['Oral', 'Topical', 'Intravenous', 'Intramuscular', 
                        'Subcutaneous', 'Inhalation', 'Rectal', 'Ophthalmic', 
                        'Otic', 'Nasal', 'Other']
        if v:
            v_lower = v.lower().strip()
            route_map = {
                'po': 'Oral', 'oral': 'Oral', 'by mouth': 'Oral',
                'topical': 'Topical', 'external': 'Topical',
                'iv': 'Intravenous', 'intravenous': 'Intravenous',
                'im': 'Intramuscular', 'intramuscular': 'Intramuscular',
                'sc': 'Subcutaneous', 'subq': 'Subcutaneous', 'subcutaneous': 'Subcutaneous',
                'inhalation': 'Inhalation', 'inhaled': 'Inhalation',
                'rectal': 'Rectal', 'pr': 'Rectal',
                'ophthalmic': 'Ophthalmic', 'eye': 'Ophthalmic',
                'otic': 'Otic', 'ear': 'Otic',
                'nasal': 'Nasal', 'intranasal': 'Nasal',
            }
            normalized = route_map.get(v_lower)
            if normalized:
                return normalized
            return 'Other'
        return v
    
    @field_validator('frequency_standard')
    @classmethod
    def normalize_frequency(cls, v):
        valid_freq = ['QD', 'BID', 'TID', 'QID', 'QHS', 'PRN', 'STAT', 
                      'Q4H', 'Q6H', 'Q8H', 'Q12H', 'Weekly', 'Monthly']
        if v:
            v_upper = v.upper().strip()
            freq_map = {
                'once daily': 'QD', 'daily': 'QD', 'qd': 'QD', 'od': 'QD',
                'twice daily': 'BID', 'bid': 'BID', 'two times a day': 'BID',
                'three times daily': 'TID', 'tid': 'TID', 'three times a day': 'TID',
                'four times daily': 'QID', 'qid': 'QID', 'four times a day': 'QID',
                'at bedtime': 'QHS', 'qhs': 'QHS', 'at night': 'QHS',
                'as needed': 'PRN', 'prn': 'PRN',
                'immediately': 'STAT', 'stat': 'STAT',
                'every 4 hours': 'Q4H', 'q4h': 'Q4H',
                'every 6 hours': 'Q6H', 'q6h': 'Q6H',
                'every 8 hours': 'Q8H', 'q8h': 'Q8H',
                'every 12 hours': 'Q12H', 'q12h': 'Q12H',
                'weekly': 'Weekly', 'once a week': 'Weekly',
                'monthly': 'Monthly', 'once a month': 'Monthly',
            }
            normalized = freq_map.get(v.lower().strip())
            if normalized:
                return normalized
            if v_upper in valid_freq:
                return v_upper
        return v
    
    @field_validator('timing')
    @classmethod
    def validate_timing(cls, v):
        valid_timing = ['Morning', 'Afternoon', 'Evening', 'Night', 
                        'Before Meal', 'After Meal', 'With Food', 'On Empty Stomach']
        if v:
            normalized = []
            for t in v:
                t_lower = t.lower().strip()
                timing_map = {
                    'morning': 'Morning', 'am': 'Morning',
                    'afternoon': 'Afternoon',
                    'evening': 'Evening', 'pm': 'Evening',
                    'night': 'Night', 'bedtime': 'Night',
                    'before meal': 'Before Meal', 'before meals': 'Before Meal', 'ac': 'Before Meal',
                    'after meal': 'After Meal', 'after meals': 'After Meal', 'pc': 'After Meal',
                    'with food': 'With Food', 'with meals': 'With Food',
                    'empty stomach': 'On Empty Stomach', 'on empty stomach': 'On Empty Stomach',
                }
                mapped = timing_map.get(t_lower)
                if mapped:
                    normalized.append(mapped)
                elif t.title() in valid_timing:
                    normalized.append(t.title())
            return normalized if normalized else None
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['active', 'completed', 'discontinued', 'on_hold']
        if v and v.lower() not in valid_statuses:
            return 'active'  # Default
        return v.lower() if v else v
    
    @field_validator('prescriber_npi')
    @classmethod
    def validate_npi(cls, v):
        if v:
            # Clean to digits only
            cleaned = re.sub(r'\D', '', v)
            if len(cleaned) == 10:
                return cleaned
            return None  # Invalid NPI
        return v


class MedicationDataGuard(BaseModel):
    """Complete medication data validation guard."""
    user_guid: str = Field(..., description="User GUID from user endpoint")
    medications: List[MedicationRecordGuard] = Field(default=[], description="Medication list")
    
    @field_validator('user_guid')
    @classmethod
    def validate_guid(cls, v):
        guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        if not re.match(guid_pattern, v):
            raise ValueError('Invalid GUID format')
        return v.lower()  # Normalize to lowercase
