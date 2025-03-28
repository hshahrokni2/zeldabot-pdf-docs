#!/usr/bin/env python3
"""Test the updated schema fields."""

import json
from src.extraction.schema import (
    BRFExtraction, IncomeStatement, FinancialMetrics,
    StringField, NumberField, IntegerField, create_field_with_confidence,
    RevenueBreakdown, ExpenseBreakdown
)

def create_test_data():
    """Create test data with year-over-year comparison fields."""
    # Current year data
    revenue = create_field_with_confidence(3788000.0, 0.9, "test data")
    expenses = create_field_with_confidence(2835200.0, 0.9, "test data")
    net_income = create_field_with_confidence(952800.0, 0.9, "test data")
    
    # Previous year data (10% less)
    prev_revenue = create_field_with_confidence(3409200.0, 0.8, "test data")
    prev_expenses = create_field_with_confidence(2551680.0, 0.8, "test data")
    prev_net_income = create_field_with_confidence(857520.0, 0.8, "test data")
    
    # Create revenue breakdowns
    revenue_breakdown = RevenueBreakdown(
        annual_fees=NumberField(**create_field_with_confidence(3030400.0, 0.9, "test data")),
        rental_income=NumberField(**create_field_with_confidence(568200.0, 0.9, "test data")),
        other_income=NumberField(**create_field_with_confidence(189400.0, 0.8, "test data"))
    )
    
    prev_revenue_breakdown = RevenueBreakdown(
        annual_fees=NumberField(**create_field_with_confidence(2727360.0, 0.8, "test data")),
        rental_income=NumberField(**create_field_with_confidence(511380.0, 0.8, "test data")),
        other_income=NumberField(**create_field_with_confidence(170460.0, 0.7, "test data"))
    )
    
    # Create expense breakdowns
    expense_breakdown = ExpenseBreakdown(
        electricity=NumberField(**create_field_with_confidence(283520.0, 0.9, "test data")),
        heating=NumberField(**create_field_with_confidence(567040.0, 0.9, "test data")),
        water_and_sewage=NumberField(**create_field_with_confidence(283520.0, 0.9, "test data")),
        property_maintenance=NumberField(**create_field_with_confidence(425280.0, 0.8, "test data")),
        property_insurance=NumberField(**create_field_with_confidence(141760.0, 0.9, "test data")),
        financial_costs=NumberField(**create_field_with_confidence(1134080.0, 0.9, "test data"))
    )
    
    prev_expense_breakdown = ExpenseBreakdown(
        electricity=NumberField(**create_field_with_confidence(255168.0, 0.8, "test data")),
        heating=NumberField(**create_field_with_confidence(510336.0, 0.8, "test data")),
        water_and_sewage=NumberField(**create_field_with_confidence(255168.0, 0.8, "test data")),
        property_maintenance=NumberField(**create_field_with_confidence(382752.0, 0.7, "test data")),
        property_insurance=NumberField(**create_field_with_confidence(127584.0, 0.8, "test data")),
        financial_costs=NumberField(**create_field_with_confidence(1020672.0, 0.8, "test data"))
    )
    
    # Create financial metrics with average interest rate
    financial_metrics = FinancialMetrics(
        monthly_fee_per_sqm=NumberField(**create_field_with_confidence(165.0, 0.8, "test data")),
        debt_per_sqm=NumberField(**create_field_with_confidence(33052.0, 0.8, "test data")),
        loan_amortization_amount=NumberField(**create_field_with_confidence(1250000.0, 0.9, "test data")),
        total_debt=NumberField(**create_field_with_confidence(98500000.0, 0.9, "test data")),
        average_interest_rate=NumberField(**create_field_with_confidence(4.12, 0.85, "test data"))
    )
    
    # Create income statement with year-over-year data
    income_statement = IncomeStatement(
        revenue=NumberField(**revenue),
        expenses=NumberField(**expenses),
        net_income=NumberField(**net_income),
        revenue_breakdown=revenue_breakdown,
        expense_breakdown=expense_breakdown,
        previous_year_revenue=NumberField(**prev_revenue),
        previous_year_expenses=NumberField(**prev_expenses),
        previous_year_net_income=NumberField(**prev_net_income),
        previous_year_revenue_breakdown=prev_revenue_breakdown,
        previous_year_expense_breakdown=prev_expense_breakdown
    )
    
    # Return the data as a dictionary
    return {
        "income_statement": income_statement.dict(),
        "financial_metrics": financial_metrics.dict()
    }

def print_field_analysis(data):
    """Print analysis of the test data."""
    income_stmt = data["income_statement"]
    
    # Revenue analysis
    curr_revenue = income_stmt["revenue"]["value"]
    prev_revenue = income_stmt["previous_year_revenue"]["value"]
    revenue_change = ((curr_revenue - prev_revenue) / prev_revenue) * 100
    
    print("\nYear-over-Year Revenue Analysis:")
    print("-------------------------------")
    print(f"Current Year Revenue: {curr_revenue:,.2f}")
    print(f"Previous Year Revenue: {prev_revenue:,.2f}")
    print(f"Change: {revenue_change:.1f}%")
    
    # Revenue breakdown analysis
    curr_fees = income_stmt["revenue_breakdown"]["annual_fees"]["value"]
    prev_fees = income_stmt["previous_year_revenue_breakdown"]["annual_fees"]["value"]
    fees_change = ((curr_fees - prev_fees) / prev_fees) * 100
    
    curr_rental = income_stmt["revenue_breakdown"]["rental_income"]["value"]
    prev_rental = income_stmt["previous_year_revenue_breakdown"]["rental_income"]["value"]
    rental_change = ((curr_rental - prev_rental) / prev_rental) * 100
    
    print("\nRevenue Breakdown:")
    print("----------------")
    print(f"Annual Fees: {curr_fees:,.2f} vs {prev_fees:,.2f} ({fees_change:.1f}%)")
    print(f"Rental Income: {curr_rental:,.2f} vs {prev_rental:,.2f} ({rental_change:.1f}%)")
    
    # Average interest rate
    avg_rate = data["financial_metrics"]["average_interest_rate"]["value"]
    loan_amount = data["financial_metrics"]["total_debt"]["value"]
    annual_interest = loan_amount * (avg_rate / 100)
    
    print("\nFinancial Analysis:")
    print("-----------------")
    print(f"Average Interest Rate: {avg_rate:.2f}%")
    print(f"Total Debt: {loan_amount:,.2f}")
    print(f"Annual Interest: {annual_interest:,.2f}")

if __name__ == "__main__":
    # Create and print the test data
    test_data = create_test_data()
    
    # Save to file
    with open('schema_test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Print analysis
    print("Successfully created test data with year-over-year fields!")
    print(f"Test data saved to: schema_test_data.json")
    
    # Print analysis
    print_field_analysis(test_data)