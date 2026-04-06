"""
ENHANCED OCR utilities for KU Academic Reports - FINAL VERSION
Handles BOTH transcript formats:
1. Standard: "Name of the Student : UPRETI NITESH"
2. Alternate: ":NEPAL DILASHA" appearing BEFORE the label line

Also handles OCR artifacts like ® instead of F
"""

import re
import logging

# Make fuzzywuzzy optional
try:
    from fuzzywuzzy import process
    HAS_FUZZYWUZZY = True
except ImportError:
    HAS_FUZZYWUZZY = False

logger = logging.getLogger(__name__)

# Enhanced patterns for BOTH formats
NAME_PATTERNS_ENHANCED = [
    # Format 1: Standard - "Name of the Student : SURNAME FIRST"
    r'Name\s+of\s+the\s+Student\s*[:=]\s*[:]*\s*([A-Z][A-Z\s]+?)(?=\s*Surname|\s*Registration|\s*$)',
    
    # Format 2: After colon with extra spacing
    r'Name\s+of\s+the\s+Student\s*[:=]\s*(.+?)(?=\s*Surname|\s*First|\s*Registration)',
    
    # Format 3: Generic fallback
    r'Student\s*[:=]\s*([A-Z][A-Z\s]+)',
]

# OCR artifacts that represent F grade
F_GRADE_ARTIFACTS = [
    r'®',  # Common OCR mistake for circled F
    r'\(F\)',  # Circled F
    r'\bF\b',  # Plain F
    r'©',  # Another OCR artifact
    r'@',  # Yet another
]

# Subject code patterns
SUBJECT_CODE_PATTERN = r'\b([A-Z]{2,4}\s?\d{2,4})\b'


def extract_name_multi_strategy(raw_text, db_student_names=None):
    """
    Multi-strategy name extraction supporting BOTH KU formats.
    """
    
    # Strategy 1: Colon-prefix format (":NEPAL DILASHA" BEFORE label)
    name = try_colon_prefix_extraction(raw_text)
    if name:
        logger.info(f"Strategy 1 (Colon Prefix): Extracted '{name}'")
        return fuzzy_match_if_available(name, db_student_names)
    
    # Strategy 2: Enhanced Pattern Matching
    name = try_pattern_extraction(raw_text)
    if name:
        logger.info(f"Strategy 2 (Pattern): Extracted '{name}'")
        return fuzzy_match_if_available(name, db_student_names)
    
    # Strategy 3: Line-by-Line Context Analysis
    name = try_line_context_extraction(raw_text)
    if name:
        logger.info(f"Strategy 3 (Line Context): Extracted '{name}'")
        return fuzzy_match_if_available(name, db_student_names)
    
    # Strategy 4: Position-Based (Surname/First/Middle labels)
    name = try_position_based_extraction(raw_text)
    if name:
        logger.info(f"Strategy 4 (Position): Extracted '{name}'")
        return fuzzy_match_if_available(name, db_student_names)
    
    # Strategy 5: Desperate - find first valid name-like string
    name = try_desperate_extraction(raw_text)
    if name:
        logger.info(f"Strategy 5 (Desperate): Extracted '{name}'")
        return fuzzy_match_if_available(name, db_student_names)
    
    logger.warning("All name extraction strategies failed")
    return None


def try_colon_prefix_extraction(raw_text):
    """
    NEW STRATEGY: Handle ":NEPAL DILASHA" format.
    
    This format appears as:
    Line N: :NEPAL DILASHA (or with OCR artifacts: . :NEPAL DILASHA)
    Line N+1: Name of the Student Surname First Middle
    
    The colon prefix line comes BEFORE the label!
    """
    lines = raw_text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for lines with colon followed by capitals
        # Handle OCR artifacts: ". :NEPAL" or just ":NEPAL"
        stripped = line.strip()
        
        # Remove leading dots and spaces that OCR might add
        cleaned_line = re.sub(r'^[\.\s]+:', ':', stripped)
        
        if cleaned_line.startswith(':') or (':' in cleaned_line[:10] and any(c.isupper() for c in cleaned_line)):
            # Extract the part after the colon
            if ':' in cleaned_line:
                parts = cleaned_line.split(':', 1)
                if len(parts) == 2:
                    name_part = parts[1].strip()
                else:
                    continue
            else:
                continue
            
            # Validate this looks like a name (all caps or mostly caps, 2+ words)
            words = name_part.split()
            if len(words) >= 2 and any(word.isupper() for word in words):
                # Check if next few lines have name-related labels
                # Be flexible with OCR typos: "Sumame" instead of "Surname", etc.
                for offset in [1, 2, 3]:
                    if i + offset < len(lines):
                        check_line = lines[i + offset].strip()
                        # Flexible matching for "Name", "Surname", "First", "Middle"
                        if any(keyword in check_line for keyword in ['Name of the Student', 'Surname', 'Surnam', 'First', 'Middle']):
                            # This is likely the name!
                            cleaned = clean_name(name_part)
                            if is_valid_name(cleaned):
                                return cleaned
                            break
    
    return None


def try_pattern_extraction(raw_text):
    """Strategy: Pattern matching with enhanced patterns"""
    for pattern in NAME_PATTERNS_ENHANCED:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            raw_name = match.group(1).strip()
            cleaned = clean_name(raw_name)
            if is_valid_name(cleaned):
                return cleaned
    return None


def try_line_context_extraction(raw_text):
    """
    Strategy: Line-by-line analysis looking for name context.
    """
    lines = raw_text.split('\n')
    
    for i, line in enumerate(lines):
        # Look for the "Name of the Student" label
        if re.search(r'Name\s+of\s+the\s+Student', line, re.IGNORECASE):
            # Extract everything after the colon on this line
            parts = re.split(r'[:=]', line, maxsplit=1)
            if len(parts) >= 2:
                candidate = parts[1].strip()
                # Remove any trailing labels
                candidate = re.sub(r'\s*(Surname|First|Middle|Registration).*$', '', candidate, flags=re.IGNORECASE)
                cleaned = clean_name(candidate)
                if is_valid_name(cleaned):
                    return cleaned
            
            # Check next line for continuation
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Skip if it's the "Surname First Middle" label line
                if not re.match(r'^\s*Surname\s+First\s+Middle', next_line, re.IGNORECASE):
                    if re.match(r'^[A-Z\s]+$', next_line) and len(next_line) > 3:
                        cleaned = clean_name(next_line)
                        if is_valid_name(cleaned):
                            return cleaned
    
    return None


def try_position_based_extraction(raw_text):
    """
    Strategy: Look for the "Surname First Middle" structure.
    """
    lines = raw_text.split('\n')
    
    for i, line in enumerate(lines):
        # Find the "Surname First Middle" label line
        if re.search(r'Surname\s+First\s+Middle', line, re.IGNORECASE):
            # The actual name should be 1-2 lines above
            for offset in [1, 2]:
                if i - offset >= 0:
                    candidate_line = lines[i - offset].strip()
                    # Remove the "Name of the Student :" label if present
                    candidate_line = re.sub(r'Name\s+of\s+the\s+Student\s*[:=]\s*', '', candidate_line, flags=re.IGNORECASE)
                    # Remove any colons at the start
                    candidate_line = candidate_line.lstrip(':').strip()
                    
                    cleaned = clean_name(candidate_line)
                    if is_valid_name(cleaned):
                        return cleaned
    
    return None


def try_desperate_extraction(raw_text):
    """
    Strategy: Desperate mode - find any line with 2-4 capitalized words.
    """
    lines = raw_text.split('\n')
    search_window = lines[:max(10, len(lines) // 3)]
    
    noise_words = {
        "NAME", "STUDENT", "THE", "OF", "REGISTRATION", "NO", "NUMBER",
        "UNIVERSITY", "SCHOOL", "ENGINEERING", "KATHMANDU", "ACADEMIC",
        "RECORD", "BACHELOR", "TECHNOLOGY", "INFORMATION", "LEVEL",
        "EXAMINATION", "ROLL", "SURNAME", "FIRST", "MIDDLE"
    }
    
    for line in search_window:
        # Skip lines with common labels
        if re.search(r'(Level|Registration|Examination|Name of the)', line, re.IGNORECASE):
            continue
        
        # Look for lines with 2-4 capitalized words
        words = re.findall(r'\b[A-Z][A-Z]+\b', line)
        
        # Filter out noise words
        clean_words = [w for w in words if w not in noise_words and len(w) > 1]
        
        # If we have 2-4 clean words, might be a name
        if 2 <= len(clean_words) <= 4:
            candidate = ' '.join(clean_words)
            if is_valid_name(candidate):
                return candidate.title()
    
    return None


def clean_name(raw_name):
    """
    Clean extracted name string.
    
    IMPORTANT: Be careful not to remove location names if they're part of the actual name!
    Example: "NEPAL DILASHA" - NEPAL is the surname, not a location prefix
    """
    if not raw_name:
        return ""
    
    # Split into words first
    words = raw_name.split()
    
    # Only remove location prefix if we have 3+ words
    # Example: "NEPAL KATHMANDU DILASHA" -> "Kathmandu Dilasha"
    # But keep: "NEPAL DILASHA" as is (NEPAL is the surname)
    if len(words) >= 3:
        location_words = ['NEPAL', 'KATHMANDU', 'POKHARA', 'DHARAN']
        if words[0].upper() in location_words:
            # Remove first word
            name = ' '.join(words[1:])
        else:
            name = raw_name
    else:
        # 2 words or less - keep as is
        name = raw_name
    
    # Remove numbers and special chars
    name = re.sub(r'[0-9]', '', name)
    name = re.sub(r'[^\w\s\-]', ' ', name)
    
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Title case
    name = name.title()
    
    return name


def is_valid_name(name):
    """
    Validate if a string looks like a valid student name.
    """
    if not name or len(name) < 4 or len(name) > 50:
        return False
    
    words = name.split()
    if len(words) < 2:
        return False
    
    # Check if all same character
    if len(set(name.replace(' ', ''))) <= 2:
        return False
    
    # Check against noise words
    noise_words = {
        "NAME", "STUDENT", "THE", "OF", "REGISTRATION", "NO", "NUMBER",
        "UNIVERSITY", "SCHOOL", "ENGINEERING", "KATHMANDU", "ACADEMIC"
    }
    
    if any(word.upper() in noise_words for word in words):
        return False
    
    # Must be mostly alphabetic
    alpha_ratio = sum(c.isalpha() for c in name) / len(name.replace(' ', ''))
    if alpha_ratio < 0.8:
        return False
    
    return True


def extract_failed_subjects_enhanced(raw_text):
    """
    ENHANCED: Extract failed subjects with OCR artifact handling.
    
    Handles:
    - ® symbol (common OCR mistake for circled F)
    - (F) with various OCR variations  
    - Plain F grade
    - INC remark
    - 0.00 grade points
    - Mangled table OCR
    - OCR artifacts in course codes: "MATH [01" instead of "MATH 101"
    - Multiple strategies to find failed subjects
    """
    failed_subjects = []
    lines = raw_text.split('\n')
    
    for line_idx, line in enumerate(lines):
        # Skip header lines
        if not line.strip():
            continue
            
        line_upper = line.upper()
        
        # Skip obvious header/footer lines
        if any(skip in line_upper for skip in ['COURSE NUMBER', 'COURSE TITLE', 'CREDIT', 'CHECKED BY', 'DATE OF ISSUE', 'GPA (GRADE', 'Exam:', 'EXAM DATE', 'STADE', 'VALUE', 'GRADE POINT']):
            continue
        
        has_failure_indicator = False
        failure_type = None
        
        # Strategy 1: Check for OCR artifacts of F grade
        for artifact in F_GRADE_ARTIFACTS:
            if re.search(artifact, line):
                has_failure_indicator = True
                failure_type = "F_Artifact"
                break
        
        # Strategy 2: Check for INC remark (very reliable indicator)
        if not has_failure_indicator and re.search(r'\bINC\b', line_upper):
            if 'INCOMPLETE' not in line_upper:  # Exclude if it's the word "INCOMPLETE"
                has_failure_indicator = True
                failure_type = "INC"
        
        # Strategy 3: Check for explicit F grade (common in cleaner OCR)
        if not has_failure_indicator and re.search(r'\bF\b', line_upper):
            # Make sure it's not in a word like "FIRST" or "FROM"
            if not re.search(r'(FIRST|FROM|FORMATION|FOUNDATION|FOR|FAILED|FACULTY|FINAL)', line_upper):
                has_failure_indicator = True
                failure_type = "F_Explicit"
        
        # Strategy 4: Check for 0.00 grade appearing (grade value AND grade points)
        # This is very common in failed grades
        if not has_failure_indicator:
            zero_count = line.count('0.00')
            zero_patterns = len(re.findall(r'\b0\.00\b', line))
            if zero_patterns >= 2:  # Two separate 0.00 values
                has_failure_indicator = True
                failure_type = "Zero_Grade"
            elif zero_patterns == 1 and re.search(r'0[\s\|]+0[\s\|]', line):  # 0 with 0 nearby
                has_failure_indicator = True
                failure_type = "Zero_Grade_Alt"
        
        # Strategy 5: Check for patterns like "| 0.00 | 0.00 |" (table format)
        if not has_failure_indicator and re.search(r'0[\s\|]+0\.00[\s\|]+0\.00', line):
            has_failure_indicator = True
            failure_type = "Table_Zero"
        
        # Strategy 6: Look for "FAILED" keyword
        if not has_failure_indicator and 'FAIL' in line_upper:
            has_failure_indicator = True
            failure_type = "Failed_Keyword"
        
        # Strategy 7: Detect garbled/corrupted grade table entries
        # When OCR mangles grade data, it often produces single letters or short garbled text
        # Pattern: Line with course code followed by garbled grade indicators like "pa |", "pe fe", etc.
        if not has_failure_indicator and re.search(r'[A-Z]{2,5}\s*\d{3}', line):
            # Check for garbled patterns: "pa ", "pe ", "p[letter] ", short letter combos, pipes and symbols
            garbled = re.search(r'(p[a-z]\s|[a-z]\s+[a-z]\s|[a-z]\s[\|&]|[pP][aeiou]\s*[\|&\d])', line)
            if garbled:
                has_failure_indicator = True
                failure_type = "Garbled_Grade"
        
        # If we found a failure indicator, extract the subject code
        if has_failure_indicator:
            logger.debug(f"Line {line_idx}: Failure type '{failure_type}' detected")
            
            # Try multiple subject code extraction patterns
            subject_found = extract_subject_from_line(line, failed_subjects)
            
            if not subject_found:
                # Try looking backwards in the line or previous lines for subject code
                subject_found = extract_subject_backward(line, lines, line_idx, failed_subjects)
    
    logger.info(f"Total failed subjects extracted: {len(failed_subjects)}")
    return failed_subjects


def extract_subject_from_line(line, failed_subjects):
    """Extract subject code from a single line."""
    line_upper = line.upper()
    
    # Patterns to try (in order of confidence)
    subject_patterns = [
        # Pattern 1: Standard with space (MATH 101)
        (r'\b([A-Z]{2,5})\s+(\d{3})\b', "standard_space"),
        
        # Pattern 2: No space (MATH101)
        (r'\b([A-Z]{2,5})(\d{3})\b', "no_space"),
        
        # Pattern 3: OCR artifacts - bracket instead of space (MATH [01)
        (r'\b([A-Z]{2,5})\s*\[+(\d+)\b', "bracket"),
        
        # Pattern 4: OCR artifacts - pipe instead of space (MATH |01)
        (r'\b([A-Z]{2,5})\s*\|+(\d+)\b', "pipe"),
        
        # Pattern 5: Single letter I as 1 (MATH I01 -> MATH 101)
        (r'\b([A-Z]{2,5})\s*[I|l](\d+)\b', "letter_i"),
        
        # Pattern 6: Missing first digit (MATH 01 -> MATH 101, MATH 02 -> MATH 102)
        (r'\b([A-Z]{2,5})\s*(\d{2})\b', "two_digit"),
    ]
    
    for pattern, pattern_type in subject_patterns:
        matches = list(re.finditer(pattern, line_upper))
        if matches:
            for match in matches:
                if len(match.groups()) >= 2:
                    prefix = match.group(1)
                    number = str(match.group(2))
                else:
                    continue
                
                # Clean up OCR artifacts in prefix
                prefix = clean_subject_prefix(prefix)
                
                # Clean up OCR artifacts in number
                number = number.replace('O', '0')  # O -> 0
                number = number.replace('l', '1')  # l -> 1
                number = number.replace('I', '1')  # I -> 1
                
                # Ensure number is 3 digits for two-digit pattern
                if pattern_type == "two_digit" and len(number) == 2:
                    # Try to infer the first digit (usually 1 or 2)
                    first_digit = '1'  # Default to 1, could be made smarter
                    number = first_digit + number
                
                # Pad to 3 digits if needed
                if len(number) < 3:
                    number = number.zfill(3)
                elif len(number) > 3:
                    number = number[:3]
                
                subject_code = prefix + number
                
                # Validate subject code
                if is_valid_subject_code(subject_code) and subject_code not in failed_subjects:
                    failed_subjects.append(subject_code)
                    logger.info(f"Found failed subject: {subject_code} (pattern: {pattern_type})")
                    return True
    
    return False


def extract_subject_backward(line, all_lines, line_idx, failed_subjects):
    """Try to find subject code by looking before the failure indicator."""
    line_upper = line.upper()
    
    # Get the part of the line before the failure indicator
    # Look for positions of indicators
    indicators = [
        r'\bF\b', r'®', r'©', r'@', r'\bINC\b', 
        r'0\.00.*0\.00', r'\(F\)', r'\[F\]'
    ]
    
    for indicator_pattern in indicators:
        match = re.search(indicator_pattern, line_upper)
        if match:
            # Everything before the indicator
            before_text = line[:match.start()]
            
            # Try to find subject code in this part
            pattern = r'([A-Z]{2,5})\s*(\d{2,3})\b'
            subject_matches = list(re.finditer(pattern, before_text.upper()))
            
            if subject_matches:
                # Take the last match (closest to the indicator)
                last_match = subject_matches[-1]
                prefix = last_match.group(1)
                number = last_match.group(2)
                
                prefix = clean_subject_prefix(prefix)
                number = number.replace('O', '0').replace('I', '1').replace('l', '1')
                
                if len(number) == 2:
                    number = '1' + number
                
                subject_code = prefix + number[:3]
                
                if is_valid_subject_code(subject_code) and subject_code not in failed_subjects:
                    failed_subjects.append(subject_code)
                    logger.info(f"Found failed subject (backward search): {subject_code}")
                    return True
            break
    
    return False


def clean_subject_prefix(prefix):
    """Clean OCR artifacts in subject code prefix."""
    if not prefix:
        return prefix
    
    # Common substitutions
    replacements = {
        'MATII': 'MATH',
        'MATI': 'MATH',
        'COIIIP': 'COMP',
        'COINIP': 'COMP',
        'COIIP': 'COMP',
        'COIN': 'COM',
        'AIIMC': 'AIMC',
        'AIISP': 'AISP',
        'EIIIT': 'ELIT',
        'EIIT': 'ELIT',
        '1NGLISH': 'ENGLISH',
        'IIIEM': 'IIEM',
        'IIEM': 'IIEM',
    }
    
    for wrong, correct in replacements.items():
        prefix = prefix.replace(wrong, correct)
    
    return prefix.strip()


def is_valid_subject_code(code):
    """Validate if string looks like a valid subject code."""
    if not code or len(code) < 5 or len(code) > 8:
        return False
    
    # Must start with 2-5 letters and end with 3 digits
    if not re.match(r'^[A-Z]{2,5}\d{3}$', code):
        return False
    
    # Exclude noise patterns
    if code in ['YEAR', 'YEAT', 'TOTAL', 'TOTA', 'GRADE', 'GRAT']:
        return False
    
    return True


def fuzzy_match_if_available(extracted_name, db_student_names):
    """
    If database names are available, try fuzzy matching.
    """
    if not HAS_FUZZYWUZZY or not db_student_names or not extracted_name:
        return extracted_name
    
    try:
        best_match, score = process.extractOne(extracted_name, db_student_names)
        if score > 80:
            logger.info(f"Fuzzy matched '{extracted_name}' to '{best_match}' (score: {score})")
            return best_match
        else:
            logger.info(f"Fuzzy match score too low ({score}), using extracted: '{extracted_name}'")
            return extracted_name
    except Exception as e:
        logger.warning(f"Fuzzy matching failed: {e}")
        return extracted_name


# ===========================
# Main Entry Points
# ===========================

def extract_student_name_improved(raw_text, db_student_names=None):
    """
    Main entry point for name extraction.
    Supports BOTH KU transcript formats.
    """
    return extract_name_multi_strategy(raw_text, db_student_names)


def extract_failed_subjects(raw_text):
    """
    Main entry point for failed subjects extraction.
    Handles OCR artifacts like ® instead of F.
    """
    return extract_failed_subjects_enhanced(raw_text)


# ===========================
# Backwards Compatibility
# ===========================

def extract_ocr_data_from_image(image_array):
    """Legacy function for backwards compatibility"""
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.fromarray(image_array), config='--psm 6')


def extract_registration_number(raw_text):
    """
    ENHANCED: Extract registration number from KU academic report.
    
    Handles multiple formats:
    - "Registration No : 12345"
    - "Registration No. : 12345" (with period)
    - "Registration No. :12345" (no space before colon)
    - "Registration No: REG-12345" 
    - "Reg No : 12345"
    - "Roll No : 12345"
    - Numbers after "Registration" label on same or next line
    """
    if not raw_text:
        return None
    
    lines = raw_text.split('\n')
    
    # Multi-format patterns to try (ORDER MATTERS - most specific first)
    patterns = [
        # Format 1: "Registration No. :037392-24" or "Registration No :037392-24" (with/without period, may have space)
        r'Registration\s+No\.?\s*[:=]\s*([A-Z0-9\-]+)',
        
        # Format 2: Examination/Exam Roll
        r'(?:Examination|Exam)\s+(?:Roll|Reg|Registration)\s+No\.?\s*[:=]\s*([A-Z0-9\-]+)',
        
        # Format 3: Just "Roll No" or "Reg No"
        r'(?:Roll|Reg)\s+No\.?\s*[:=]\s*([A-Z0-9\-]+)',
        
        # Format 4: Codes without spaces (e.g., "RegNo:")
        r'(?:Registration|Reg|Roll)No\.?\s*[:=]\s*([A-Z0-9\-]+)',
        
        # Format 5: Generic with more flexible spacing
        r'(?:Registration|Reg|Roll|REG)\s*No\.?\s*[:=]\s*([A-Z0-9\-]+)',
    ]
    
    # First pass: look for explicit "Registration" label
    for line in lines:
        line_upper = line.upper()
        
        # Skip header and irrelevant lines
        if any(skip in line_upper for skip in ['COURSE', 'CREDIT', 'SEMESTER', 'GRADE POINT', 'GPA']):
            continue
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if len(match.groups()) > 0:
                    reg_num = match.group(1).strip()
                else:
                    # Find next group of digits/letters after the match
                    reg_num = extract_next_token(line, match.end())
                
                if reg_num:
                    reg_num = clean_registration_number(reg_num)
                    if is_valid_registration_number(reg_num):
                        logger.info(f"Found registration number: {reg_num}")
                        return reg_num
    
    logger.warning("Could not extract registration number from text")
    return None


def extract_next_token(line, start_pos):
    """Extract the next alphanumeric token after a position."""
    remaining = line[start_pos:].strip()
    match = re.match(r'([A-Za-z0-9\-]+)', remaining)
    if match:
        return match.group(1)
    return None


def clean_registration_number(reg_num):
    """
    Clean extracted registration number by fixing OCR artifacts.
    
    Handles:
    - O (letter O) -> 0 (zero)
    - l (lowercase L) -> 1 (one)
    - I (capital I) in numbers -> 1
    """
    if not reg_num:
        return None
    
    # Fix common OCR character substitutions
    # Only replace in number parts, not in letter prefixes
    reg_num = reg_num.upper().strip()
    
    # Replace OCR artifacts in numbers
    # Be careful: only O->0 in numeric context
    cleaned = ""
    for char in reg_num:
        if char == 'O' and len(cleaned) > 0 and cleaned[-1].isdigit():
            cleaned += '0'  # O after a digit is likely 0
        elif char == 'O' and re.search(r'\d', reg_num[reg_num.index(char):]):
            cleaned += '0'  # O if followed by digit is likely 0
        elif char in 'lI' and re.search(r'\d', reg_num[reg_num.index(char):]):
            cleaned += '1'  # l/I before a digit is likely 1
        else:
            cleaned += char
    
    return cleaned


def is_valid_registration_number(reg_num):
    """
    Validate if string looks like a valid registration number.
    
    Must:
    - Be 4-15 characters
    - Contain at least 3-4 digits
    - Optional prefix (REG-, DR-, etc.)
    """
    if not reg_num or len(reg_num) < 4 or len(reg_num) > 15:
        return False
    
    # Must have at least 3 digits
    digit_count = sum(1 for c in reg_num if c.isdigit())
    if digit_count < 3:
        return False
    
    # First character must be alphanumeric
    if not reg_num[0].isalnum():
        return False
    
    # Valid characters: numbers, letters, hyphen, dot
    if not all(c.isalnum() or c in '-.' for c in reg_num):
        return False
    
    return True


def parse_ku_report(raw_text, processed_image=None, db_student_names=None):
    """Legacy function for backwards compatibility"""
    return {
        'name': extract_student_name_improved(raw_text, db_student_names) or 'Unknown',
        'failed_subjects': extract_failed_subjects(raw_text),
        'semester': 1,
        'gpa': 0.0,
        'is_failing': False,
        'extraction_confidence': 0.85,
        'registration_no': extract_registration_number(raw_text),
    }


def get_student_name_from_ocr_data(processed_image):
    """Legacy function for backwards compatibility"""
    return None
