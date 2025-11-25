# SkyGuard Error: SCHEMA_VALIDATION

## תיאור השגיאה
ערך בנתוני הטיסה חורג מהמגבלות שהוגדרו בסכמת האימות, למרות שסוג הנתון תקין. שגיאה זו מצביעה על ערכים לא הגיוניים או קיצוניים.

## גבולות תקינים במערכת SkyGuard
- **signal_strength:** 0-100
- **altitude:** -500 עד 50,000 רגל (ים המלח עד תקרת אוירה)
- **speed:** 0-1,500 קשר (מנוחה עד מהירות על-קולית)
- **heading:** 0-359 מעלות
- **transponder_code:** 4 ספרות אוקטליות (0000-7777)

## סיבות נפוצות (Root Cause)
1. **Sensor Glitch (רעש חיישנים):** קפיצות מתח במכ"ם גורמות לקריאת ערך קיצוני
2. **Calibration Needed (נדרש כיול):** חיישנים לא מכויילים מדווחים ערכים מוסטים
3. **Buggy Firmware (באג בקושחה):** גרסת תוכנה חדשה שולחת נתונים בסקאלה שגויה
4. **Unit Mismatch (אי-התאמת יחידות):** מטרים במקום רגל, קמ"ש במקום קשר
5. **Overflow/Underflow:** גלישת מספרים בחיישנים דיגיטליים
6. **Environmental Interference:** הפרעות אלקטרומגנטיות משבשות קריאות
7. **Legacy System:** מטוסים ישנים עם פרוטוקולים לא תואמים לחלוטין
8. **Type Coercion Error:** המרת טיפוסים שגויה (מחרוזת למספר)

## דוגמאות לקלט שגוי

### דוגמה 1: עוצמת אות חורגת (קפיצת מתח)
```json
{
  "aircraft_id": "IAF-001",
  "signal_strength": 999,
  "altitude": 15000,
  "timestamp": "2025-11-25T10:00:00Z"
}
```
**בעיה:** `signal_strength: 999` חורג מהטווח 0-100 - קפיצת מתח במכ"ם

### דוגמה 2: גובה שלילי (מתחת לפני הים)
```json
{
  "aircraft_id": "IAF-002",
  "signal_strength": 85,
  "altitude": -500,
  "location": {"lat": 31.5, "lon": 35.4}
}
```
**בעיה:** `altitude: -500` מתחת לרמת הים - אם לא מעל ים המלח, חיישן לא מכויל

### דוגמה 3: גובה מעל תקרת אוירה
```json
{
  "aircraft_id": "IAF-003",
  "altitude": 200000,
  "speed": 500
}
```
**בעיה:** `altitude: 200000` מעל גבול האטמוספירה - לא הגיוני למטוס

### דוגמה 4: מהירות על-קולית קיצונית
```json
{
  "aircraft_id": "IAF-004",
  "altitude": 30000,
  "speed": 5000
}
```
**בעיה:** `speed: 5000` קשר גבוה פי 3 ממהירות סילון - אי-התאמת יחידות?

### דוגמה 5: עוצמת אות שלילית
```json
{
  "aircraft_id": "IAF-006",
  "signal_strength": -5,
  "altitude": 10000
}
```
**בעיה:** `signal_strength: -5` שלילי - גליטש בחיישן

### דוגמה 6: גובה 0 (אזהרת נחיתה)
```json
{
  "aircraft_id": "IAF-007",
  "altitude": 0,
  "speed": 150,
  "status": "FRIENDLY"
}
```
**בעיה:** `altitude: 0` יכול להצביע על נחיתה או התרסקות - דורש בדיקה

## פתרון מומלץ
1. **Schema Validation:** אמת כל שדה מול סכימה מוגדרת (Zod, JSON Schema)
2. **Range Checks:** בדוק שערכים בטווח ההגיוני לפני קבלה
3. **Unit Conversion:** המר יחידות באופן אחיד (רגל/מטר, קשר/קמ"ש)
4. **Sensor Calibration:** כייל חיישנים באופן קבוע
5. **Outlier Detection:** זהה ערכים חריגים והתעלם מהם
6. **Sanity Checks:** בדוק עקביות בין שדות (גובה 0 + מהירות 500 = בעיה)
7. **Historical Comparison:** השווה לקריאות קודמות - קפיצה של 10,000 רגל בשניה לא הגיונית

## קוד דוגמה לאימות
```python
from typing import Dict, Optional

class SkyGuardValidator:
    LIMITS = {
        'signal_strength': (0, 100),
        'altitude': (-500, 50000),
        'speed': (0, 1500),
        'heading': (0, 359)
    }
    
    @staticmethod
    def validate_numeric_range(value: float, field_name: str) -> bool:
        """Validate numeric field is within acceptable range"""
        if field_name not in SkyGuardValidator.LIMITS:
            return True  # No limits defined
        
        min_val, max_val = SkyGuardValidator.LIMITS[field_name]
        
        if not (min_val <= value <= max_val):
            raise ValueError(
                f"{field_name} value {value} out of range [{min_val}, {max_val}]"
            )
        
        return True
    
    @staticmethod
    def validate_aircraft_data(data: Dict) -> tuple[bool, Optional[str]]:
        """Validate complete aircraft data packet"""
        try:
            # Validate numeric fields
            for field in ['signal_strength', 'altitude', 'speed', 'heading']:
                if field in data:
                    if not isinstance(data[field], (int, float)):
                        return False, f"{field} must be numeric"
                    
                    SkyGuardValidator.validate_numeric_range(data[field], field)
            
            # Sanity checks
            if data.get('altitude', 1000) == 0 and data.get('speed', 0) > 100:
                return False, "Impossible: altitude 0 with high speed"
            
            return True, None
            
        except ValueError as e:
            return False, str(e)

# Example usage
aircraft_data = {
    "aircraft_id": "IAF-001",
    "signal_strength": 999,  # Out of range!
    "altitude": 15000
}

is_valid, error_msg = SkyGuardValidator.validate_aircraft_data(aircraft_data)
if not is_valid:
    raise ValidationError(f"SCHEMA_VALIDATION: {error_msg}")
```

## Status Code
**400 Bad Request** - נתונים לא עומדים בסכימה

## Severity
🟠 **HIGH** - עלול להשפיע על מעקב אחר כלי טיס ולהוביל להחלטות מבצעיות שגויות

## קטגוריה
Data Validation Error / Sensor Anomaly
