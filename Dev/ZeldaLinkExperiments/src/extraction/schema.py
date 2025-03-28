#!/usr/bin/env python3
"""
Pydantic models for the Swedish housing association (BRF) annual report extraction.
Based on schema_v2.json with confidence tracking and source information.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any, Tuple
from pydantic import BaseModel, Field, ConfigDict, ValidationError


class ConfidenceEnum(str, Enum):
    """Confidence level for extracted data."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExtractionField(BaseModel):
    """Base model for extraction fields with confidence and source tracking."""
    value: Optional[Any] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    source: Optional[str] = None


class StringField(ExtractionField):
    """String field with confidence and source tracking."""
    value: Optional[str] = None


class NumberField(ExtractionField):
    """Numeric field with confidence and source tracking."""
    value: Optional[float] = None


class IntegerField(ExtractionField):
    """Integer field with confidence and source tracking."""
    value: Optional[int] = None


class BooleanField(ExtractionField):
    """Boolean field with confidence and source tracking."""
    value: Optional[bool] = None


# Organization models
class ContactDetails(BaseModel):
    """Contact details for a BRF."""
    phone: Optional[StringField] = None
    email: Optional[StringField] = None
    website: Optional[StringField] = None

class Organization(BaseModel):
    """Organization information for a BRF."""
    organization_name: Optional[StringField] = None
    organization_number: Optional[StringField] = None
    registered_office: Optional[StringField] = None
    association_statutes: Optional[StringField] = None
    association_tax_status: Optional[StringField] = None
    contact_details: Optional[ContactDetails] = None


# Property details models
class AddressComponent(BaseModel):
    """Components of a property address."""
    street: Optional[StringField] = None
    number: Optional[StringField] = None
    postal_code: Optional[StringField] = None
    municipality: Optional[StringField] = None


class ApartmentDistribution(BaseModel):
    """Distribution of apartments by size."""
    studio: Optional[IntegerField] = None
    one_bedroom: Optional[IntegerField] = None
    two_bedroom: Optional[IntegerField] = None
    three_bedroom: Optional[IntegerField] = None
    four_plus_bedroom: Optional[IntegerField] = None


class CommercialRental(BaseModel):
    """Commercial rental information."""
    type: str
    area_sqm: float
    annual_rent: float
    confidence: float
    source: str


class PropertyDetails(BaseModel):
    """Property details for a BRF."""
    property_designation: Optional[StringField] = None
    address: Optional[StringField] = None
    address_components: Optional[AddressComponent] = None
    total_area_sqm: Optional[NumberField] = None
    residential_area_sqm: Optional[NumberField] = None
    commercial_area_sqm: Optional[NumberField] = None
    number_of_apartments: Optional[IntegerField] = None
    apartment_distribution: Optional[ApartmentDistribution] = None
    commercial_rentals: List[CommercialRental] = Field(default_factory=list)
    year_built: Optional[StringField] = None
    tax_value: Optional[NumberField] = None


# Financial report models
class Assets(BaseModel):
    """Assets section of the balance sheet."""
    current_assets: Optional[NumberField] = None
    fixed_assets: Optional[NumberField] = None
    total_assets: Optional[NumberField] = None


class Liabilities(BaseModel):
    """Liabilities section of the balance sheet."""
    short_term_liabilities: Optional[NumberField] = None
    long_term_liabilities: Optional[NumberField] = None
    total_liabilities: Optional[NumberField] = None


class BalanceSheet(BaseModel):
    """Balance sheet for a BRF."""
    assets: Optional[Assets] = None
    liabilities: Optional[Liabilities] = None
    equity: Optional[NumberField] = None


class RevenueBreakdown(BaseModel):
    """Revenue breakdown for a BRF."""
    annual_fees: Optional[NumberField] = None
    rental_income: Optional[NumberField] = None
    other_income: Optional[NumberField] = None

class ExpenseBreakdown(BaseModel):
    """Expense breakdown for a BRF."""
    electricity: Optional[NumberField] = None
    heating: Optional[NumberField] = None
    water_and_sewage: Optional[NumberField] = None
    waste_management: Optional[NumberField] = None
    property_maintenance: Optional[NumberField] = None
    repairs: Optional[NumberField] = None
    maintenance: Optional[NumberField] = None
    property_tax: Optional[NumberField] = None
    property_insurance: Optional[NumberField] = None
    cable_tv_internet: Optional[NumberField] = None
    board_costs: Optional[NumberField] = None
    management_fees: Optional[NumberField] = None
    other_operating_costs: Optional[NumberField] = None
    financial_costs: Optional[NumberField] = None

class IncomeStatement(BaseModel):
    """Income statement for a BRF."""
    revenue: Optional[NumberField] = None
    expenses: Optional[NumberField] = None
    net_income: Optional[NumberField] = None
    revenue_breakdown: Optional[RevenueBreakdown] = None
    expense_breakdown: Optional[ExpenseBreakdown] = None
    previous_year_revenue: Optional[NumberField] = None
    previous_year_expenses: Optional[NumberField] = None
    previous_year_net_income: Optional[NumberField] = None
    previous_year_revenue_breakdown: Optional[RevenueBreakdown] = None
    previous_year_expense_breakdown: Optional[ExpenseBreakdown] = None


class FinancialReport(BaseModel):
    """Financial report for a BRF."""
    annual_report_year: Optional[StringField] = None
    balance_sheet: Optional[BalanceSheet] = None
    income_statement: Optional[IncomeStatement] = None


# Financial metrics models
class FinancialMetrics(BaseModel):
    """Financial metrics for a BRF."""
    monthly_fee_per_sqm: Optional[NumberField] = None
    debt_per_sqm: Optional[NumberField] = None
    energy_consumption: Optional[NumberField] = None
    annual_fee_change_percent: Optional[NumberField] = None
    loan_amortization_amount: Optional[NumberField] = None
    total_debt: Optional[NumberField] = None
    average_interest_rate: Optional[NumberField] = None


# Loan models
class Loan(BaseModel):
    """Loan information for a BRF."""
    lender: str
    loan_number: Optional[str] = None
    amount: float
    interest_rate: float
    interest_rate_type: Optional[str] = None
    maturity_date: Optional[str] = None
    confidence: float
    source: str


# Expenses models
class EnergyCosts(BaseModel):
    """Energy costs for a BRF."""
    energy_costs: Optional[NumberField] = None
    heating_costs: Optional[NumberField] = None
    water_costs: Optional[NumberField] = None


class FacilityCosts(BaseModel):
    """Facility costs for a BRF."""
    waste_management_costs: Optional[NumberField] = None
    cleaning_costs: Optional[NumberField] = None
    snow_removal_costs: Optional[NumberField] = None
    property_management_costs: Optional[NumberField] = None


class AdminCosts(BaseModel):
    """Administrative costs for a BRF."""
    insurance_costs: Optional[NumberField] = None
    cable_tv_internet_costs: Optional[NumberField] = None
    property_tax: Optional[NumberField] = None


class OperatingCosts(BaseModel):
    """Operating costs for a BRF."""
    energy_costs: Optional[NumberField] = None
    heating_costs: Optional[NumberField] = None
    water_costs: Optional[NumberField] = None
    waste_management_costs: Optional[NumberField] = None
    cleaning_costs: Optional[NumberField] = None
    snow_removal_costs: Optional[NumberField] = None
    property_management_costs: Optional[NumberField] = None
    insurance_costs: Optional[NumberField] = None
    cable_tv_internet_costs: Optional[NumberField] = None
    property_tax: Optional[NumberField] = None


class MaintenanceCosts(BaseModel):
    """Maintenance costs for a BRF."""
    repairs: Optional[NumberField] = None
    planned_maintenance: Optional[NumberField] = None


class AdministrativeCosts(BaseModel):
    """Administrative costs for a BRF."""
    board_fees: Optional[NumberField] = None
    audit_fees: Optional[NumberField] = None
    accounting_fees: Optional[NumberField] = None


class FinancialCosts(BaseModel):
    """Financial costs for a BRF."""
    interest_expenses: Optional[NumberField] = None
    amortization: Optional[NumberField] = None


class ExpensesDetail(BaseModel):
    """Detailed expenses for a BRF."""
    operating_costs: Optional[OperatingCosts] = None
    maintenance_costs: Optional[MaintenanceCosts] = None
    administrative_costs: Optional[AdministrativeCosts] = None
    financial_costs: Optional[FinancialCosts] = None
    depreciation: Optional[NumberField] = None


# Note models
class Note(BaseModel):
    """Note from a BRF annual report."""
    note_number: int
    title: str
    content: str
    values: Dict[str, Any] = Field(default_factory=dict)
    confidence: float
    source: str
    needs_review: bool = False


# Board models
class BoardMember(BaseModel):
    """Board member information."""
    name: str
    role: Optional[str] = None
    confidence: float
    source: str


class Auditor(BaseModel):
    """Auditor information."""
    name: Optional[str] = None
    company: Optional[str] = None
    confidence: float
    source: str


class Board(BaseModel):
    """Board information for a BRF."""
    board_members: List[BoardMember] = Field(default_factory=list)
    board_meetings: Optional[IntegerField] = None
    auditors: List[Auditor] = Field(default_factory=list)


# Maintenance models
class MaintenanceAction(BaseModel):
    """Maintenance action information."""
    year: str
    description: str
    confidence: float
    source: str


class PlannedMaintenanceAction(MaintenanceAction):
    """Planned maintenance action information."""
    estimated_cost: Optional[float] = None


class Maintenance(BaseModel):
    """Maintenance information for a BRF."""
    historical_actions: List[MaintenanceAction] = Field(default_factory=list)
    planned_actions: List[PlannedMaintenanceAction] = Field(default_factory=list)
    maintenance_plan: Optional[StringField] = None


# Supplier models
class Supplier(BaseModel):
    """Supplier information."""
    name: str
    service_type: str
    contract_period: Optional[str] = None
    confidence: float
    source: str


# Event models
class SignificantEvent(BaseModel):
    """Significant event information."""
    date: str
    description: str
    category: Optional[str] = None
    confidence: float
    source: str


# Metadata models
class UncertainField(BaseModel):
    """Information about an uncertain field."""
    field_path: str
    reason: str
    confidence: float


class NormalizationRules(BaseModel):
    """Rules for normalizing Swedish number formats."""
    decimal_separator: str = "."
    thousand_separator: str = ""
    currency_format: str = "numeric"


class ExtractionMeta(BaseModel):
    """Metadata about the extraction process."""
    extraction_confidence: float = 0.0
    extraction_date: str
    extraction_method: str = "hybrid"
    ocr_source: str = "Mistral OCR"
    document_language: str = "sv-SE"
    uncertain_fields: List[UncertainField] = Field(default_factory=list)
    normalization_rules: NormalizationRules = Field(default_factory=NormalizationRules)


# Schema improvement models
class SchemaImprovementSuggestion(BaseModel):
    """Suggestion for improving the extraction schema."""
    field_path: str
    suggested_name: str
    suggested_type: str
    example_value: Any
    reason: str
    confidence: float


class SchemaImprovement(BaseModel):
    """Schema improvement information."""
    suggestions: List[SchemaImprovementSuggestion] = Field(default_factory=list)
    model: str
    timestamp: str


# Main extraction model
class BRFExtraction(BaseModel):
    """Main extraction model for a BRF annual report."""
    model_config = ConfigDict(
        json_schema_extra={
            "title": "Homeowner Association Annual Report v2.0",
            "description": "Schema for the annual financial and operational report of a Swedish Homeowner Association (BRF) with enhanced extraction metadata"
        }
    )
    
    organization: Organization
    property_details: Optional[PropertyDetails] = None
    financial_report: FinancialReport
    financial_metrics: Optional[FinancialMetrics] = None
    financial_loans: List[Loan] = Field(default_factory=list)
    expenses_detail: Optional[ExpensesDetail] = None
    notes: List[Note] = Field(default_factory=list)
    board: Optional[Board] = None
    maintenance: Optional[Maintenance] = None
    suppliers: List[Supplier] = Field(default_factory=list)
    significant_events: List[SignificantEvent] = Field(default_factory=list)
    meta: ExtractionMeta
    schema_improvements: Optional[SchemaImprovement] = None


# Helper function to create a field with confidence
def create_field_with_confidence(value: Any, confidence: float, source: str) -> Dict:
    """Create a field dictionary with value, confidence and source."""
    return {
        "value": value,
        "confidence": min(max(confidence, 0.0), 1.0),  # Ensure confidence is between 0 and 1
        "source": source
    }


def validate_extraction(extraction_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extraction data against the Pydantic models.
    
    Args:
        extraction_data: Extraction data to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        # Convert to Pydantic model
        BRFExtraction(**extraction_data)
        return True, []
    except ValidationError as e:
        # Return validation errors
        error_messages = []
        for err in e.errors():
            path = ".".join(str(p) for p in err["loc"])
            error_messages.append(f"{path}: {err['msg']}")
        return False, error_messages
    except Exception as e:
        # Return any other errors
        return False, [str(e)]