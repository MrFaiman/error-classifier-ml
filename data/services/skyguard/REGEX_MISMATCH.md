# SkyGuard Error: REGEX_MISMATCH

## תיאור השגיאה
פורמט מחרוזת הקלט אינו תואם לדפוס (Regex Pattern) שהוגדר לשדה זה. שכיח במיוחד בשדות המכילים קודים, מזהים או פרוטוקולים מוגדרים.

## דפוסי Regex נפוצים ב-SkyGuard
- **transponder_code:** `^[0-7]{4}$` (4 ספרות אוקטליות)
- **aircraft_id:** `^[A-Z]{3}-[0-9]{3}$` (למשל: IAF-001)
- **callsign:** `^[A-Z]{2,3}[0-9]{3,4}$` (למשל: EL123)
- **hex_code:** `^[0-9A-F]{6}$` (Mode-S address)

## סיבות נפוצות (Root Cause)
1. **Legacy Systems (מערכות ישנות):** מטוסים ישנים משתמשים בפרוטוקולים לא תואמים
2. **Data Corruption (שיבוש נתונים):** הפרעות רדיו משנות ביטים בשידור
3. **Manual Entry Error (שגיאת הקלדה):** טייס או בקר הזינו קוד שגוי ידנית
4. **Character Encoding Issues:** בעיות קידוד תווים (UTF-8 vs ASCII)
5. **Protocol Mismatch:** שימוש בפרוטוקול Mode A כאשר צפוי Mode S
6. **Truncation/Padding:** קוד קוצץ או הורחב בצורה שגויה
7. **Case Sensitivity:** ערבוב אותיות גדולות/קטנות
8. **Placeholder Values:** קודי בדיקה או ברירת מחדל שנשארו בייצור

## דוגמאות לקלט שגוי

### דוגמה 1: תו הקסדצימלי בקוד אוקטלי
```json
{
  "aircraft_id": "IAF-001",
  "transponder": "12A4",
  "altitude": 15000
}
```
**בעיה:** האות `A` לא תקפה בקוד אוקטלי (רק 0-7) - מערכת ישנה שולחת hex

### דוגמה 2: ספרה 8 או 9 בקוד אוקטלי
```json
{
  "transponder": "8888"
}
```
**בעיה:** הספרה `8` אינה חוקית במערכת אוקטלית - טווח תקף: 0000-7777

### דוגמה 3: קוד קצר מדי
```json
{
  "transponder": "77"
}
```
**בעיה:** רק 2 ספרות במקום 4 - מערכת ישנה או שיבוש

### דוגמה 4: קוד ארוך מדי
```json
{
  "transponder": "12345"
}
```
**בעיה:** 5 ספרות במקום 4 - ייתכן שנוספה ספרת בדיקה בטעות

### דוגמה 5: תווים מיוחדים
```json
{
  "transponder": "12-34"
}
```
**בעיה:** תו `-` במקום ספרה - שגיאת הקלדה

### דוגמה 6: ערך placeholder
```json
{
  "transponder": "____"
}
```
**בעיה:** קו תחתון משמש כ-placeholder - נתונים לא אמיתיים

### דוגמה 7: אותיות באמצע
```json
{
  "transponder": "ABCD"
}
```
**בעיה:** אותיות במקום ספרות - ייתכן ערבוב עם Mode-S hex code

### דוגמה 8: מזהה מטוס לא תקין
```json
{
  "aircraft_id": "IAF001",
  "transponder": "1234"
}
```
**בעיה:** `IAF001` חסר מקף - פורמט נדרש: `IAF-001`

## פתרון מומלץ
1. **Regex Validation:** אמת כל מחרוזת מול regex לפני קבלה
2. **Input Sanitization:** נקה רווחים, המר לאותיות גדולות לפני אימות
3. **Protocol Detection:** זהה אוטומטית אם מגיע hex במקום octal והמר
4. **Length Checks:** ודא אורך תקין לפני regex
5. **Whitelist Characters:** אפשר רק תווים מהרשימה המותרת
6. **Graceful Degradation:** קבל פורמטים ישנים עם אזהרה
7. **Clear Error Messages:** ציין בדיוק מה שגוי ומה הפורמט הנדרש
8. **Historical Data Analysis:** למד מדפוסים של שגיאות חוזרות

## קוד דוגמה לאימות
```python
import re
from typing import Dict, Optional

class RegexValidator:
    PATTERNS = {
        'transponder': r'^[0-7]{4}$',
        'aircraft_id': r'^[A-Z]{3}-[0-9]{3}$',
        'callsign': r'^[A-Z]{2,3}[0-9]{3,4}$',
        'hex_code': r'^[0-9A-F]{6}$'
    }
    
    PATTERN_DESCRIPTIONS = {
        'transponder': '4 octal digits (0-7), e.g., "1234"',
        'aircraft_id': 'Format: XXX-999, e.g., "IAF-001"',
        'callsign': '2-3 letters + 3-4 digits, e.g., "EL123"',
        'hex_code': '6 hexadecimal digits, e.g., "A1B2C3"'
    }
    
    @staticmethod
    def sanitize_input(value: str) -> str:
        """Clean input string"""
        return value.strip().upper()
    
    @staticmethod
    def validate_format(value: str, field_name: str) -> tuple[bool, Optional[str]]:
        """Validate string format against regex pattern"""
        if field_name not in RegexValidator.PATTERNS:
            return True, None  # No pattern defined
        
        # Sanitize input
        clean_value = RegexValidator.sanitize_input(value)
        
        pattern = RegexValidator.PATTERNS[field_name]
        
        if not re.match(pattern, clean_value):
            expected = RegexValidator.PATTERN_DESCRIPTIONS.get(
                field_name, 
                f"Pattern: {pattern}"
            )
            return False, f"Invalid format. Expected: {expected}"
        
        return True, None
    
    @staticmethod
    def detect_common_errors(value: str, field_name: str) -> Optional[str]:
        """Provide helpful error messages for common mistakes"""
        if field_name == 'transponder':
            if len(value) < 4:
                return "Too short - transponder code must be 4 digits"
            if len(value) > 4:
                return "Too long - transponder code must be exactly 4 digits"
            if any(c in value for c in '89'):
                return "Invalid octal digit (8 or 9) - use only 0-7"
            if any(c.isalpha() for c in value):
                return "Letters not allowed in octal transponder code"
            if value == '____':
                return "Placeholder value detected - provide real transponder code"
        
        if field_name == 'aircraft_id':
            if '-' not in value:
                return "Missing separator - format should be XXX-999"
        
        return "Format does not match expected pattern"

# Example usage
def validate_aircraft_code(data: Dict) -> None:
    """Validate aircraft identification codes"""
    for field in ['transponder', 'aircraft_id', 'callsign']:
        if field in data:
            is_valid, error_msg = RegexValidator.validate_format(
                data[field], field
            )
            
            if not is_valid:
                specific_error = RegexValidator.detect_common_errors(
                    data[field], field
                )
                raise ValidationError(
                    f"REGEX_MISMATCH in {field}: {specific_error or error_msg}"
                )

# Test cases
test_data = {
    "transponder": "12A4",  # Invalid: hex in octal field
    "aircraft_id": "IAF-001"
}

try:
    validate_aircraft_code(test_data)
except ValidationError as e:
    print(f"Error: {e}")
```

## Status Code
**400 Bad Request** - פורמט שדה לא תקין

## Severity
**HIGH** - עלול לגרום לאי-זיהוי נכון של כלי טיס

## קטגוריה
Format Validation Error / Protocol Mismatch
