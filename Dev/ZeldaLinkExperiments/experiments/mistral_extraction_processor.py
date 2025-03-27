#!/usr/bin/env python3
"""
Mistral Extraction Processor - Extract structured data from OCR text
using schema_v2.json with confidence scoring and source tracking
"""

import os
import sys
import json
import re
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union

class MistralExtractionProcessor:
    """
    Process OCR text from Mistral OCR and extract structured data
    according to schema_v2.json with confidence scoring
    """
    
    def __init__(self, ocr_json_path: str, schema_path: str = None, output_path: str = None):
        """
        Initialize the extraction processor
        
        Args:
            ocr_json_path: Path to the OCR JSON file
            schema_path: Path to the schema JSON file (defaults to schema_v2.json)
            output_path: Path to save the output JSON file (optional)
        """
        self.ocr_json_path = ocr_json_path
        self.schema_path = schema_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema_v2.json")
        self.output_path = output_path
        
        # Load OCR data and schema
        self.ocr_data = self._load_ocr_data()
        self.schema = self._load_schema()
        
        # Extract OCR text and organize by page
        self.pages = []
        self.markdown_by_page = {}
        self._extract_ocr_text()
        
        # Initialize result structure based on schema
        self.results = self._initialize_result_structure()
        
        # Swedish number format patterns
        self.number_pattern = r'(?:(?:\d{1,3}(?: \d{3})*)|(?:\d+))(?:,\d{1,2})?(?: (?:kr|SEK|kronor))?'
        
        # Document context
        self.document_name = os.path.basename(ocr_json_path).split('_ocr.')[0]
    
    def _load_ocr_data(self) -> Dict:
        """Load the OCR JSON data from file"""
        try:
            with open(self.ocr_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading OCR data: {e}")
            return {}
    
    def _load_schema(self) -> Dict:
        """Load the schema JSON data from file"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading schema: {e}")
            return {}
    
    def _extract_ocr_text(self):
        """Extract text from OCR data and organize by page"""
        if 'pages' not in self.ocr_data:
            print("Error: OCR data does not contain 'pages' key")
            return
        
        for idx, page in enumerate(self.ocr_data['pages']):
            page_num = idx + 1
            markdown = page.get('markdown', '')
            self.pages.append(markdown)
            self.markdown_by_page[page_num] = markdown
    
    def _initialize_result_structure(self) -> Dict:
        """Initialize the result structure based on schema"""
        result = {}
        
        # Create basic structure from schema properties
        properties = self.schema.get('properties', {})
        for key in properties:
            if 'properties' in properties[key]:
                result[key] = {}
            elif properties[key]['type'] == 'array':
                result[key] = []
            else:
                result[key] = None
        
        # Add metadata
        result['meta'] = {
            'extraction_confidence': 0.0,
            'extraction_date': datetime.datetime.now().isoformat(),
            'extraction_method': 'hybrid',
            'ocr_source': 'Mistral OCR',
            'document_language': 'sv-SE',
            'uncertain_fields': [],
            'normalization_rules': {
                'decimal_separator': '.',
                'thousand_separator': '',
                'currency_format': 'numeric'
            }
        }
        
        return result
    
    def process(self) -> Dict:
        """
        Process OCR data and extract structured information
        
        Returns:
            Dictionary containing extracted data with confidence scores
        """
        print(f"Processing OCR data from {self.ocr_json_path}")
        
        # Extract organization info
        self._extract_organization_info()
        
        # Extract property details
        self._extract_property_details()
        
        # Extract financial report
        self._extract_financial_report()
        
        # Extract board information
        self._extract_board_info()
        
        # Extract maintenance information
        self._extract_maintenance_info()
        
        # Extract financial metrics
        self._extract_financial_metrics()
        
        # Calculate overall confidence
        self._calculate_overall_confidence()
        
        # Save results if output path is provided
        if self.output_path:
            self._save_results()
        
        return self.results
    
    def _normalize_swedish_number(self, text: str) -> Optional[float]:
        """
        Convert Swedish formatted numbers to standard float values
        
        Args:
            text: String containing Swedish formatted number (e.g. "1 234,56 kr")
            
        Returns:
            Float value or None if conversion fails
        """
        if not text:
            return None
            
        # Remove currency indicators
        text = re.sub(r'(?:kr|SEK|kronor|:-)', '', text).strip()
        
        # Remove spaces (used as thousand separators)
        text = text.replace(" ", "")
        
        # Replace comma with period for decimal point
        text = text.replace(",", ".")
        
        # Convert to numeric value
        try:
            return float(text)
        except ValueError:
            return None
    
    def _find_text_with_pattern(self, pattern: str, pages: List[str] = None) -> List[Tuple[str, str, float]]:
        """
        Find text matching pattern in OCR pages
        
        Args:
            pattern: Regular expression pattern to search for
            pages: List of pages to search, or None for all pages
            
        Returns:
            List of tuples (matched_text, page_source, confidence)
        """
        if pages is None:
            pages = self.pages
        
        results = []
        for idx, page in enumerate(pages):
            page_num = idx + 1
            matches = re.finditer(pattern, page, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                matched_text = match.group(0)
                # Calculate basic confidence - can be improved
                confidence = 0.7 if len(matched_text) > 3 else 0.5
                results.append((matched_text, f"page {page_num}", confidence))
        
        return results
    
    def _find_value_after_label(self, label: str, pages: List[str] = None, max_chars: int = 100) -> List[Tuple[str, str, float]]:
        """
        Find values that appear after a specific label
        
        Args:
            label: The label text to search for
            pages: List of pages to search, or None for all pages
            max_chars: Maximum number of characters to look ahead after the label
            
        Returns:
            List of tuples (value_text, page_source, confidence)
        """
        if pages is None:
            pages = self.pages
        
        results = []
        pattern = rf'{re.escape(label)}[:\s]*([^.\n]+)'
        
        for idx, page in enumerate(pages):
            page_num = idx + 1
            matches = re.finditer(pattern, page, re.IGNORECASE)
            
            for match in matches:
                value_text = match.group(1).strip()
                if value_text:
                    # Higher confidence for values right after label
                    confidence = 0.8
                    results.append((value_text, f"page {page_num}", confidence))
        
        return results
    
    def _create_field_with_confidence(self, value: Any, confidence: float, source: str) -> Dict:
        """Create a field object with value, confidence, and source"""
        return {
            "value": value,
            "confidence": min(max(confidence, 0.0), 1.0),  # Ensure confidence is between 0 and 1
            "source": source
        }
    
    def _extract_organization_info(self):
        """Extract organization name, number, and other details"""
        print("Extracting organization information...")
        
        # Extract organization name
        org_name_matches = self._find_text_with_pattern(r'Brf\s+[A-Za-zÀ-ÖØ-öø-ÿ]+')
        if org_name_matches:
            match_text, source, confidence = org_name_matches[0]
            self.results["organization"]["organization_name"] = self._create_field_with_confidence(
                match_text.strip(), confidence, source
            )
        
        # Extract organization number
        org_number_matches = self._find_text_with_pattern(r'\d{6}-\d{4}')
        if org_number_matches:
            match_text, source, confidence = org_number_matches[0]
            self.results["organization"]["organization_number"] = self._create_field_with_confidence(
                match_text.strip(), confidence, source
            )
        
        # Extract registered office
        registered_office_matches = self._find_value_after_label("säte", self.pages[:5])
        if registered_office_matches:
            match_text, source, confidence = registered_office_matches[0]
            self.results["organization"]["registered_office"] = self._create_field_with_confidence(
                match_text.strip(), confidence, source
            )
        
        # Extract association tax status
        tax_status_matches = self._find_value_after_label("privatbostadsföretag", self.pages[:10])
        if tax_status_matches:
            self.results["organization"]["association_tax_status"] = self._create_field_with_confidence(
                "äkta bostadsrättsförening", 0.9, tax_status_matches[0][1]
            )
        else:
            # Look for "äkta förening" section
            for idx, page in enumerate(self.pages[:10]):
                if re.search(r'äkta\s+(?:bostadsrätts)?förening', page, re.IGNORECASE):
                    self.results["organization"]["association_tax_status"] = self._create_field_with_confidence(
                        "äkta bostadsrättsförening", 0.8, f"page {idx+1}"
                    )
                    break
    
    def _extract_property_details(self):
        """Extract property details from OCR text"""
        print("Extracting property details...")
        
        # Extract property designation (fastighetsbeteckning)
        property_designation_matches = self._find_text_with_pattern(r'(?:fastighetsbeteckning|fastigheten)\s*(?:är)?\s*([A-Za-zÀ-ÖØ-öø-ÿ]+\s+\d+:\d+)')
        if property_designation_matches:
            for match_text, source, confidence in property_designation_matches:
                designation = re.search(r'([A-Za-zÀ-ÖØ-öø-ÿ]+\s+\d+:\d+)', match_text)
                if designation:
                    self.results["property_details"]["property_designation"] = self._create_field_with_confidence(
                        designation.group(1).strip(), confidence, source
                    )
                    break
        
        # Extract address
        address_matches = []
        for idx, page in enumerate(self.pages[:10]):
            # Look for typical address format: street + number, postal code + city
            address_match = re.search(r'([A-Za-zÀ-ÖØ-öø-ÿ]+vägen\s+\d+(?:[,]\s+\d+)?)', page, re.IGNORECASE)
            if address_match:
                address_matches.append((address_match.group(1), f"page {idx+1}", 0.8))
        
        if address_matches:
            match_text, source, confidence = address_matches[0]
            self.results["property_details"]["address"] = self._create_field_with_confidence(
                match_text.strip(), confidence, source
            )
            
            # Extract address components
            components = {}
            street_match = re.search(r'([A-Za-zÀ-ÖØ-öø-ÿ]+vägen)', match_text, re.IGNORECASE)
            if street_match:
                components["street"] = self._create_field_with_confidence(
                    street_match.group(1).strip(), confidence, source
                )
            
            number_match = re.search(r'vägen\s+(\d+(?:[,]\s+\d+)?)', match_text, re.IGNORECASE)
            if number_match:
                components["number"] = self._create_field_with_confidence(
                    number_match.group(1).strip(), confidence, source
                )
            
            # Look for municipality
            for idx, page in enumerate(self.pages[:10]):
                municipality_match = re.search(r'(?:kommun|säte):\s*([A-Za-zÀ-ÖØ-öø-ÿ]+)', page, re.IGNORECASE)
                if municipality_match:
                    components["municipality"] = self._create_field_with_confidence(
                        municipality_match.group(1).strip(), 0.7, f"page {idx+1}"
                    )
                    break
            
            if components:
                self.results["property_details"]["address_components"] = components
        
        # Extract total area
        area_matches = self._find_value_after_label("total area", self.pages[:10])
        area_matches.extend(self._find_value_after_label("total byggnadsyta", self.pages[:10]))
        area_matches.extend(self._find_value_after_label("total lägenhetsyta", self.pages[:10]))
        
        if area_matches:
            for match_text, source, confidence in area_matches:
                # Look for area value with unit
                area_value_match = re.search(r'(\d[\d\s]*(?:,\d+)?)\s*(?:kvm|m²)', match_text, re.IGNORECASE)
                if area_value_match:
                    area_value = self._normalize_swedish_number(area_value_match.group(1))
                    if area_value:
                        self.results["property_details"]["total_area_sqm"] = self._create_field_with_confidence(
                            area_value, confidence, source
                        )
                        break
        
        # Extract number of apartments
        apartment_matches = self._find_value_after_label("antal lägenheter", self.pages[:10])
        apartment_matches.extend(self._find_value_after_label("lägenhetsfördelning", self.pages[:10]))
        
        if apartment_matches:
            apartment_count = 0
            source = apartment_matches[0][1]
            confidence = 0.7
            
            # Find apartment distribution table
            for idx, page in enumerate(self.pages[:10]):
                if "rum och kök" in page.lower():
                    # Look for apartment distribution
                    distribution = {}
                    
                    # Try to find studio apartments (1 rum och kök)
                    studio_match = re.search(r'(\d+)\s*st\s*1\s*rum', page, re.IGNORECASE)
                    if studio_match:
                        count = int(studio_match.group(1))
                        apartment_count += count
                        distribution["studio"] = self._create_field_with_confidence(
                            count, 0.8, f"page {idx+1}"
                        )
                    
                    # Find other apartment types
                    for rooms in range(2, 6):
                        room_match = re.search(r'(\d+)\s*st\s*' + str(rooms) + r'\s*rum', page, re.IGNORECASE)
                        if room_match:
                            count = int(room_match.group(1))
                            apartment_count += count
                            field_name = {
                                2: "one_bedroom",
                                3: "two_bedroom",
                                4: "three_bedroom",
                                5: "four_plus_bedroom"
                            }.get(rooms)
                            if field_name:
                                distribution[field_name] = self._create_field_with_confidence(
                                    count, 0.8, f"page {idx+1}"
                                )
                    
                    if distribution:
                        self.results["property_details"]["apartment_distribution"] = distribution
                        source = f"page {idx+1}"
                    break
            
            if apartment_count > 0:
                self.results["property_details"]["number_of_apartments"] = self._create_field_with_confidence(
                    apartment_count, confidence, source
                )
        
        # Extract year built
        year_built_matches = self._find_value_after_label("byggnadsår", self.pages[:10])
        year_built_matches.extend(self._find_value_after_label("byggår", self.pages[:10]))
        
        if year_built_matches:
            for match_text, source, confidence in year_built_matches:
                year_match = re.search(r'(\d{4})', match_text)
                if year_match:
                    self.results["property_details"]["year_built"] = self._create_field_with_confidence(
                        year_match.group(1), confidence, source
                    )
                    break
        
        # Extract tax value
        tax_value_matches = self._find_value_after_label("taxeringsvärde", self.pages[:15])
        
        if tax_value_matches:
            for match_text, source, confidence in tax_value_matches:
                value_match = re.search(self.number_pattern, match_text)
                if value_match:
                    value = self._normalize_swedish_number(value_match.group(0))
                    if value:
                        self.results["property_details"]["tax_value"] = self._create_field_with_confidence(
                            value, confidence, source
                        )
                        break
    
    def _extract_financial_report(self):
        """Extract financial report information from OCR text"""
        print("Extracting financial report information...")
        
        # Find annual report year
        year_matches = self._find_text_with_pattern(r'årsredovisning\s+(\d{4})', self.pages[:3])
        
        if year_matches:
            for match_text, source, confidence in year_matches:
                year_match = re.search(r'(\d{4})', match_text)
                if year_match:
                    self.results["financial_report"]["annual_report_year"] = self._create_field_with_confidence(
                        year_match.group(1), confidence, source
                    )
                    break
        
        # Find balance sheet information
        balance_sheet = {}
        income_statement = {}
        
        # Find pages with financial statements
        balance_sheet_page = None
        income_statement_page = None
        
        for idx, page in enumerate(self.pages):
            if "balansräkning" in page.lower():
                balance_sheet_page = idx
            if "resultaträkning" in page.lower():
                income_statement_page = idx
        
        # Extract balance sheet
        if balance_sheet_page is not None:
            # Look for start of balance sheet in this and next pages
            balance_sheet_pages = self.pages[balance_sheet_page:balance_sheet_page+3]
            
            # Extract assets
            assets = {}
            
            # Current assets (omsättningstillgångar)
            current_assets_matches = self._find_value_after_label("omsättningstillgångar", balance_sheet_pages)
            
            if current_assets_matches:
                for match_text, source, confidence in current_assets_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            assets["current_assets"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Fixed assets (anläggningstillgångar)
            fixed_assets_matches = self._find_value_after_label("anläggningstillgångar", balance_sheet_pages)
            
            if fixed_assets_matches:
                for match_text, source, confidence in fixed_assets_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            assets["fixed_assets"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Total assets (summa tillgångar)
            total_assets_matches = self._find_value_after_label("summa tillgångar", balance_sheet_pages)
            
            if total_assets_matches:
                for match_text, source, confidence in total_assets_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            assets["total_assets"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            if assets:
                balance_sheet["assets"] = assets
            
            # Extract liabilities
            liabilities = {}
            
            # Short-term liabilities (kortfristiga skulder)
            short_term_matches = self._find_value_after_label("kortfristiga skulder", balance_sheet_pages)
            
            if short_term_matches:
                for match_text, source, confidence in short_term_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            liabilities["short_term_liabilities"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Long-term liabilities (långfristiga skulder)
            long_term_matches = self._find_value_after_label("långfristiga skulder", balance_sheet_pages)
            
            if long_term_matches:
                for match_text, source, confidence in long_term_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            liabilities["long_term_liabilities"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Total liabilities (summa skulder)
            total_liabilities_matches = self._find_value_after_label("summa skulder", balance_sheet_pages)
            
            if total_liabilities_matches:
                for match_text, source, confidence in total_liabilities_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            liabilities["total_liabilities"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            if liabilities:
                balance_sheet["liabilities"] = liabilities
            
            # Extract equity (eget kapital)
            equity_matches = self._find_value_after_label("eget kapital", balance_sheet_pages)
            
            if equity_matches:
                for match_text, source, confidence in equity_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            balance_sheet["equity"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
        
        # Extract income statement
        if income_statement_page is not None:
            # Look for start of income statement in this and next pages
            income_statement_pages = self.pages[income_statement_page:income_statement_page+3]
            
            # Revenue (intäkter/nettoomsättning)
            revenue_matches = self._find_value_after_label("intäkter", income_statement_pages)
            revenue_matches.extend(self._find_value_after_label("nettoomsättning", income_statement_pages))
            
            if revenue_matches:
                for match_text, source, confidence in revenue_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            income_statement["revenue"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Expenses (kostnader)
            expenses_matches = self._find_value_after_label("kostnader", income_statement_pages)
            
            if expenses_matches:
                for match_text, source, confidence in expenses_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            income_statement["expenses"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
            
            # Net income (årets resultat)
            net_income_matches = self._find_value_after_label("årets resultat", income_statement_pages)
            
            if net_income_matches:
                for match_text, source, confidence in net_income_matches:
                    value_match = re.search(self.number_pattern, match_text)
                    if value_match:
                        value = self._normalize_swedish_number(value_match.group(0))
                        if value:
                            income_statement["net_income"] = self._create_field_with_confidence(
                                value, confidence, source
                            )
                            break
        
        # Update financial report
        if balance_sheet:
            self.results["financial_report"]["balance_sheet"] = balance_sheet
        
        if income_statement:
            self.results["financial_report"]["income_statement"] = income_statement
    
    def _extract_board_info(self):
        """Extract board information from OCR text"""
        print("Extracting board information...")
        
        # Find board members
        board_members = []
        
        # Find page with board members
        board_page = None
        
        for idx, page in enumerate(self.pages):
            if "styrelse" in page.lower():
                board_page = idx
                break
        
        if board_page is not None:
            # Look for names and roles
            board_pages = self.pages[board_page:board_page+2]
            
            # Typical roles in Swedish BRFs
            roles = ["ordförande", "ledamot", "suppleant", "sekreterare", "kassör"]
            
            for page_idx, page in enumerate(board_pages):
                lines = page.split('\n')
                
                for line in lines:
                    # Check for lines with names and possibly roles
                    if re.search(r'[A-ZÀ-Ö][a-zà-ö]+ [A-ZÀ-Ö][a-zà-ö]+', line):
                        name = None
                        role = None
                        
                        # Extract name
                        name_match = re.search(r'([A-ZÀ-Ö][a-zà-ö]+ [A-ZÀ-Ö][a-zà-ö]+)', line)
                        if name_match:
                            name = name_match.group(1)
                        
                        # Check for role on the same line
                        for r in roles:
                            if r.lower() in line.lower():
                                role = r
                                break
                        
                        if name:
                            member = {
                                "name": name,
                                "confidence": 0.7,
                                "source": f"page {board_page + page_idx + 1}"
                            }
                            
                            if role:
                                member["role"] = role
                            
                            board_members.append(member)
        
        # Find auditors
        auditors = []
        
        # Find page with auditors
        auditor_page = None
        
        for idx, page in enumerate(self.pages):
            if "revisor" in page.lower():
                auditor_page = idx
                break
        
        if auditor_page is not None:
            # Look for names and companies
            auditor_pages = self.pages[auditor_page:auditor_page+2]
            
            for page_idx, page in enumerate(auditor_pages):
                lines = page.split('\n')
                
                for line in lines:
                    if "revisor" in line.lower():
                        name = None
                        company = None
                        
                        # Extract name
                        name_match = re.search(r'([A-ZÀ-Ö][a-zà-ö]+ [A-ZÀ-Ö][a-zà-ö]+)', line)
                        if name_match:
                            name = name_match.group(1)
                        
                        # Check for company
                        company_match = re.search(r'([A-ZÀ-Ö][A-Za-zÀ-ÖØ-öø-ÿ]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ]+)*)\s*(?:AB|HB|KB)', line)
                        if company_match:
                            company = company_match.group(0)
                        
                        if name or company:
                            auditor = {
                                "confidence": 0.7,
                                "source": f"page {auditor_page + page_idx + 1}"
                            }
                            
                            if name:
                                auditor["name"] = name
                            
                            if company:
                                auditor["company"] = company
                            
                            auditors.append(auditor)
        
        # Update board information
        if board_members:
            self.results["board"]["board_members"] = board_members
        
        if auditors:
            self.results["board"]["auditors"] = auditors
        
        # Find number of board meetings
        meeting_matches = self._find_value_after_label("antal styrelsemöten", self.pages)
        
        if meeting_matches:
            for match_text, source, confidence in meeting_matches:
                number_match = re.search(r'\d+', match_text)
                if number_match:
                    self.results["board"]["board_meetings"] = self._create_field_with_confidence(
                        int(number_match.group(0)), confidence, source
                    )
                    break
    
    def _extract_maintenance_info(self):
        """Extract maintenance information from OCR text"""
        print("Extracting maintenance information...")
        
        # Find maintenance section
        maintenance_page = None
        
        for idx, page in enumerate(self.pages):
            if "underhåll" in page.lower() or "underhållsplan" in page.lower():
                maintenance_page = idx
                break
        
        if maintenance_page is not None:
            # Extract maintenance plan
            plan_matches = self._find_value_after_label("underhållsplan", self.pages[maintenance_page:maintenance_page+3])
            
            if plan_matches:
                match_text, source, confidence = plan_matches[0]
                self.results["maintenance"]["maintenance_plan"] = self._create_field_with_confidence(
                    match_text.strip(), confidence, source
                )
            
            # Extract historical actions
            historical_actions = []
            
            # Look for years and descriptions of past maintenance
            for page_idx, page in enumerate(self.pages[maintenance_page:maintenance_page+3]):
                lines = page.split('\n')
                
                for i, line in enumerate(lines):
                    # Look for years in the text
                    year_match = re.search(r'\b(20\d\d)\b', line)
                    if year_match and i < len(lines) - 1:
                        year = year_match.group(1)
                        description = lines[i+1].strip()
                        
                        if description and len(description) > 5:
                            historical_actions.append({
                                "year": year,
                                "description": description,
                                "confidence": 0.6,
                                "source": f"page {maintenance_page + page_idx + 1}"
                            })
            
            if historical_actions:
                self.results["maintenance"]["historical_actions"] = historical_actions
            
            # Extract planned actions
            planned_actions = []
            
            # Look for future maintenance plans
            future_section = False
            
            for page_idx, page in enumerate(self.pages[maintenance_page:maintenance_page+3]):
                if "planerat underhåll" in page.lower() or "framtida underhåll" in page.lower():
                    future_section = True
                
                if future_section:
                    lines = page.split('\n')
                    
                    for i, line in enumerate(lines):
                        # Look for years in the text with future dates
                        year_match = re.search(r'\b(202\d|203\d)\b', line)
                        if year_match and i < len(lines) - 1:
                            year = year_match.group(1)
                            description = lines[i+1].strip()
                            
                            if description and len(description) > 5:
                                action = {
                                    "year": year,
                                    "description": description,
                                    "confidence": 0.6,
                                    "source": f"page {maintenance_page + page_idx + 1}"
                                }
                                
                                # Look for cost estimate
                                cost_match = re.search(self.number_pattern, line + ' ' + description)
                                if cost_match:
                                    value = self._normalize_swedish_number(cost_match.group(0))
                                    if value:
                                        action["estimated_cost"] = value
                                
                                planned_actions.append(action)
            
            if planned_actions:
                self.results["maintenance"]["planned_actions"] = planned_actions
    
    def _extract_financial_metrics(self):
        """Extract key financial metrics"""
        print("Extracting financial metrics...")
        
        metrics = {}
        
        # Find monthly fee per square meter
        fee_matches = self._find_text_with_pattern(r'(?:månadsavgift|årsavgift)(?:.{1,30})((?:\d[\d\s]*,\d{2})\s*(?:kr/m²|kr/kvm))')
        
        if fee_matches:
            for match_text, source, confidence in fee_matches:
                # Extract value
                value_match = re.search(r'((?:\d[\d\s]*,\d{2}))\s*(?:kr/m²|kr/kvm)', match_text)
                if value_match:
                    value = self._normalize_swedish_number(value_match.group(1))
                    if value:
                        # If yearly fee, convert to monthly
                        if "årsavgift" in match_text.lower():
                            value = value / 12
                        
                        metrics["monthly_fee_per_sqm"] = self._create_field_with_confidence(
                            value, confidence, source
                        )
                        break
        
        # Find debt per square meter
        debt_matches = self._find_text_with_pattern(r'(?:lån|skuld)(?:.{1,30})((?:\d[\d\s]*,\d{2})\s*(?:kr/m²|kr/kvm))')
        
        if debt_matches:
            for match_text, source, confidence in debt_matches:
                # Extract value
                value_match = re.search(r'((?:\d[\d\s]*,\d{2}))\s*(?:kr/m²|kr/kvm)', match_text)
                if value_match:
                    value = self._normalize_swedish_number(value_match.group(1))
                    if value:
                        metrics["debt_per_sqm"] = self._create_field_with_confidence(
                            value, confidence, source
                        )
                        break
        
        # Find energy consumption
        energy_matches = self._find_text_with_pattern(r'(?:energiförbrukning|energianvändning)(?:.{1,30})((?:\d[\d\s]*,\d{1,2})\s*(?:kWh/m²|kWh/kvm))')
        
        if energy_matches:
            for match_text, source, confidence in energy_matches:
                # Extract value
                value_match = re.search(r'((?:\d[\d\s]*,\d{1,2}))\s*(?:kWh/m²|kWh/kvm)', match_text)
                if value_match:
                    value = self._normalize_swedish_number(value_match.group(1))
                    if value:
                        metrics["energy_consumption"] = self._create_field_with_confidence(
                            value, confidence, source
                        )
                        break
        
        # Find annual fee change
        fee_change_matches = self._find_text_with_pattern(r'(?:avgiftshöjning|avgiftsförändring)(?:.{1,30})((?:\d[\d\s]*,\d{1,2})\s*(?:%|procent))')
        
        if fee_change_matches:
            for match_text, source, confidence in fee_change_matches:
                # Extract value
                value_match = re.search(r'((?:\d[\d\s]*,\d{1,2}))\s*(?:%|procent)', match_text)
                if value_match:
                    value = self._normalize_swedish_number(value_match.group(1))
                    if value:
                        metrics["annual_fee_change_percent"] = self._create_field_with_confidence(
                            value, confidence, source
                        )
                        break
        
        if metrics:
            self.results["financial_metrics"] = metrics
    
    def _calculate_overall_confidence(self):
        """Calculate overall extraction confidence"""
        confidences = []
        uncertain_fields = []
        
        # Helper function to recursively process fields
        def process_fields(data, path=""):
            if isinstance(data, dict):
                if "confidence" in data and "value" in data:
                    # This is a field with confidence
                    confidences.append(data["confidence"])
                    
                    # Check if confidence is low
                    if data["confidence"] < 0.5:
                        uncertain_fields.append({
                            "field_path": path,
                            "confidence": data["confidence"],
                            "reason": "Low extraction confidence"
                        })
                else:
                    # Process nested fields
                    for key, value in data.items():
                        process_fields(value, f"{path}.{key}" if path else key)
            elif isinstance(data, list):
                # Process list items
                for i, item in enumerate(data):
                    process_fields(item, f"{path}[{i}]")
        
        # Process all fields
        process_fields(self.results)
        
        # Calculate overall confidence
        if confidences:
            overall_confidence = sum(confidences) / len(confidences)
            self.results["meta"]["extraction_confidence"] = overall_confidence
        else:
            self.results["meta"]["extraction_confidence"] = 0.0
        
        # Update uncertain fields
        self.results["meta"]["uncertain_fields"] = uncertain_fields
    
    def _save_results(self):
        """Save extracted results to file"""
        try:
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            print(f"Saved extraction results to {self.output_path}")
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract structured data from OCR text")
    parser.add_argument("--ocr-json", "-i", required=True, help="Path to OCR JSON file")
    parser.add_argument("--schema", "-s", help="Path to schema JSON file")
    parser.add_argument("--output", "-o", help="Path to output JSON file")
    
    args = parser.parse_args()
    
    # Process OCR data
    processor = MistralExtractionProcessor(
        ocr_json_path=args.ocr_json,
        schema_path=args.schema,
        output_path=args.output
    )
    
    results = processor.process()
    
    # Print summary
    print("\nExtraction Summary:")
    print(f"  Organization: {results.get('organization', {}).get('organization_name', {}).get('value', 'Not found')}")
    print(f"  Org Number: {results.get('organization', {}).get('organization_number', {}).get('value', 'Not found')}")
    print(f"  Annual Report Year: {results.get('financial_report', {}).get('annual_report_year', {}).get('value', 'Not found')}")
    print(f"  Overall Confidence: {results.get('meta', {}).get('extraction_confidence', 0) * 100:.1f}%")
    print(f"  Uncertain Fields: {len(results.get('meta', {}).get('uncertain_fields', []))}")
    
    # Return success status
    return 0


if __name__ == "__main__":
    sys.exit(main())