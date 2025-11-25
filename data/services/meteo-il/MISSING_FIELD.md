# Meteo-IL Error: MISSING_FIELD

## תיאור השגיאה
שדה חובה חסר מהדיווח המטאורולוגי, מונע עיבוד מלא של הנתונים.

## שדות חובה במערכת Meteo-IL
- `station_id` - מזהה תחנה
- `timestamp` - חותמת זמן
- `location.lat` - קו רוחב
- `location.lon` - קו אורך
- `temperature` - טמפרטורה
- `wind_speed` - מהירות רוח
- `pressure` - לחץ אטמוספרי

## סיבות נפוצות (Root Cause)
1. **Sensor Malfunction (תקלת חיישן):** חיישן ספציפי (מד רוח, מד חום) נכשל או התנתק
2. **Network Packet Loss (אובדן מנות):** חלק מהנתונים אבד בהעברה (UDP)
3. **Power Failure (הפסקת חשמל):** התחנה אותחלה ולא כל החיישנים חזרו לפעולה
4. **Firmware Bug (באג בקושחה):** גרסה חדשה של התוכנה משמיטה שדות
5. **Configuration Error (שגיאת הגדרה):** התחנה לא מוגדרת לדווח שדה מסוים
6. **Calibration Mode (מצב כיול):** התחנה במצב תחזוקה ולא שולחת נתונים מלאים
7. **JSON Parsing Error (שגיאת פענוח):** שגיאה בפרסר שחתכה חלק מהנתונים

## דוגמאות לקלט שגוי

### דוגמה 1: חסר wind_speed
```json
{
  "station_id": "HAIFA_PORT",
  "timestamp": "2025-11-25T10:00:00Z",
  "location": {
    "lat": 32.8,
    "lon": 34.9
  },
  "temperature": 22.5,
  "pressure": 1013.25
}
```
**בעיה:** שדה `wind_speed` חסר - סביר שמד הרוח התקלקל

### דוגמה 2: wind_speed מוגדר כ-null
```json
{
  "station_id": "JERUSALEM_WEST",
  "timestamp": "2025-11-25T10:00:00Z",
  "location": {...},
  "temperature": 18.0,
  "wind_speed": null,
  "pressure": 1015.00
}
```
**בעיה:** `wind_speed` קיים אך ערכו null - מד רוח לא מחזיר נתונים

### דוגמה 3: חסר location.lat
```json
{
  "station_id": "TEL_AVIV_CENTRAL",
  "timestamp": "2025-11-25T10:00:00Z",
  "location": {
    "lon": 34.7
  },
  "temperature": 24.0,
  "wind_speed": 15.5
}
```
**בעיה:** חסר קו רוחב - GPS חלקי או תקלת הגדרה

### דוגמה 4: אובייקט location ריק
```json
{
  "station_id": "BEER_SHEVA",
  "timestamp": "2025-11-25T10:00:00Z",
  "location": {},
  "temperature": 20.0,
  "wind_speed": 10.0
}
```
**בעיה:** אובייקט המיקום קיים אך ריק - כשל GPS מלא

### דוגמה 5: חסר timestamp
```json
{
  "station_id": "GOLAN_HEIGHTS",
  "location": {...},
  "temperature": 15.5,
  "wind_speed": 25.0,
  "pressure": 1018.00
}
```
**בעיה:** חותמת זמן חסרה - כשל בסנכרון שעון המערכת

## פתרון מומלץ
1. **Schema Validation:** אמת נוכחות כל השדות החובה לפני עיבוד
2. **Sensor Health Monitoring:** עקוב אחר תקינות כל חיישן בנפרד
3. **Fallback Values:** השתמש בערכים מהדיווח הקודם (עם סימון!)
4. **Alert System:** שלח התראה כאשר שדה חובה חסר X פעמים ברציפות
5. **Redundancy:** התקן חיישנים מיותרים לשדות קריטיים
6. **Graceful Degradation:** המשך לעבד נתונים חלקיים עם רמת אמון מופחתת
7. **Automated Diagnosis:** זהה אוטומטית איזה חיישן תקול לפי דפוס השדות החסרים

## קוד דוגמה לאימות
```python
from typing import Dict, List, Any

class MeteoValidator:
    REQUIRED_FIELDS = [
        'station_id',
        'timestamp',
        'location.lat',
        'location.lon',
        'temperature',
        'wind_speed',
        'pressure'
    ]
    
    @staticmethod
    def get_nested_value(data: Dict, path: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = path.split('.')
        value = data
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value
    
    @staticmethod
    def validate_required_fields(data: Dict) -> tuple[bool, List[str]]:
        """Check for missing required fields"""
        missing_fields = []
        
        for field_path in MeteoValidator.REQUIRED_FIELDS:
            value = MeteoValidator.get_nested_value(data, field_path)
            
            if value is None or value == '':
                missing_fields.append(field_path)
        
        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields

# Example usage
weather_data = {
    "station_id": "HAIFA_PORT",
    "timestamp": "2025-11-25T10:00:00Z",
    "location": {"lat": 32.8, "lon": 34.9},
    "temperature": 22.5,
    "pressure": 1013.25
    # wind_speed חסר!
}

is_valid, missing = MeteoValidator.validate_required_fields(weather_data)
if not is_valid:
    raise ValidationError(f"MISSING_FIELD: {', '.join(missing)}")
```

## Status Code
**400 Bad Request** - נתונים חסרים

## Severity
🟠 **HIGH** - עלול להשפיע על דיוק תחזיות ולהצביע על תקלת חומרה

## קטגוריה
Data Validation Error / Hardware Failure
