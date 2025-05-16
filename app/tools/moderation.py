import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

async def check_content_policy(text: str) -> Dict[str, Any]:
    """
    Check if text content violates content policies.
    
    Args:
        text: The text to check
        
    Returns:
        A dictionary containing policy violation analysis
    """
    print(f"Checking content policy for text ({len(text)} chars)")
    
    # In a real implementation, this would use a content moderation API
    # (like OpenAI's moderation endpoint or another service)
    # For now, we'll simulate it
    
    # Simulate processing delay
    await asyncio.sleep(1)
    
    # Simple keyword check (this is a very basic simulation)
    # In a real system, this would be much more sophisticated
    sensitive_keywords = [
        # PII patterns
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN
        
        # Graphic content patterns
        r'\b(decapitat|dismember|mutilat|charred body|severed head)\w*\b',
        
        # Personal identifiers
        r'\bfull name: [A-Z][a-z]+ [A-Z][a-z]+\b',
        r'\bpassport number\b',
        r'\bidentity card\b',
        
        # Security sensitive info
        r'\bexact location of safehouse\b',
        r'\bhiding place\b',
        r'\bwitness location\b'
    ]
    
    violations = []
    categories = []
    
    # Check for keyword matches
    for pattern in sensitive_keywords:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if pattern in sensitive_keywords[:3]:  # PII patterns
                if "pii" not in categories:
                    categories.append("pii")
                violations.append(f"PII detected: {match.group(0)[:3]}***")
            
            elif pattern in sensitive_keywords[3:5]:  # Graphic content
                if "graphic_content" not in categories:
                    categories.append("graphic_content")
                violations.append(f"Graphic content detected: {match.group(0)}")
            
            elif pattern in sensitive_keywords[5:8]:  # Personal identifiers
                if "pii" not in categories:
                    categories.append("pii")
                violations.append(f"Personal identifier detected: {match.group(0)}")
            
            elif pattern in sensitive_keywords[8:]:  # Security sensitive
                if "security_risk" not in categories:
                    categories.append("security_risk")
                violations.append(f"Security sensitive information detected: {match.group(0)}")
    
    # Check for general sentiment (very basic simulation)
    inflammatory_count = sum(1 for word in ["genocide", "apartheid", "ethnic cleansing", "war crimes"] 
                            if word in text.lower())
    
    if inflammatory_count > 5:
        if "inflammatory" not in categories:
            categories.append("inflammatory")
        violations.append("High frequency of inflammatory terms detected")
    
    # Return results
    results = {
        "violations": violations,
        "categories": categories,
        "violation_count": len(violations),
        "has_violations": len(violations) > 0,
        "check_timestamp": datetime.now().isoformat()
    }
    
    return results

async def anonymize_text(text: str) -> str:
    """
    Anonymize sensitive information in text.
    
    Args:
        text: The text to anonymize
        
    Returns:
        Anonymized text
    """
    print(f"Anonymizing text ({len(text)} chars)")
    
    # In a real implementation, this would use NER and other techniques
    # For now, we'll do some simple pattern replacements
    
    # Simulate processing delay
    await asyncio.sleep(1.5)
    
    # Patterns to anonymize with their replacements
    anonymization_patterns = [
        # PII
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "[PHONE NUMBER REDACTED]"),  # Phone numbers
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL REDACTED]"),  # Email
        (r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', "[ID NUMBER REDACTED]"),  # SSN or ID
        
        # Names (very basic simulation - would use NER in real system)
        (r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', "[PERSON]"),  # Simple name pattern
        
        # Specific sensitive information
        (r'exact location: ([^\.]+)', "location: [LOCATION REDACTED]"),
        (r'address: ([^\.]+)', "address: [ADDRESS REDACTED]"),
        (r'phone: ([^\.]+)', "phone: [PHONE REDACTED]"),
        (r'staying at ([^\.]+)', "staying at [LOCATION REDACTED]"),
        
        # Victim details
        (r'victim\'s name is ([^\.]+)', "victim's name is [VICTIM]"),
        (r'witness ([^\.]+)', "witness [WITNESS]")
    ]
    
    anonymized_text = text
    
    for pattern, replacement in anonymization_patterns:
        anonymized_text = re.sub(pattern, replacement, anonymized_text)
    
    return anonymized_text 