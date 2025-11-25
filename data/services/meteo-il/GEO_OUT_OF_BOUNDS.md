# Meteo-IL Error: GEO_OUT_OF_BOUNDS

## תיאור השגיאה
הקואורדינטות הגיאוגרפיות (קו רוחב/אורך) חורגות מהטווח הפיזיקלי התקף או מחוץ לאזור התפעול המוגדר של מערכת Meteo-IL.

## גבולות תקינים
- **קו רוחב (Latitude):** -90 עד 90 מעלות
- **קו אורך (Longitude):** -180 עד 180 מעלות
- **ישראל:** Lat: 29.5-33.3, Lon: 34.2-35.9

## סיבות נפוצות (Root Cause)
1. **GPS Failure (כשל GPS):** תחנה איבדה סנכרון לוויינים ודיווחת מיקום אקראי
2. **Configuration Error (שגיאת הגדרה):** קואורדינטות הוחלפו (Lat במקום Lon) בהגדרה ידנית
3. **GPS Spoofing (זיוף GPS):** הפרעה מכוונת לאותות GPS המשבשת את המיקום
4. **Default Values (ערכי ברירת מחדל):** המערכת אותחלה ל-"Null Island" (0,0)
5. **Sensor Malfunction (תקלת חיישן):** חיישן GPS פגום שולח נתונים משובשים
6. **Type Error (שגיאת סוג):** קואורדינטות נשלחו כמחרוזת במקום מספר
7. **Precision Loss (אובדן דיוק):** עיגול או קיצוץ שגוי של מספרים עשרוניים

## דוגמאות לקלט שגוי

### דוגמה 1: קו רוחב מעל הגבול הפיזיקלי
```json
{
  "lat": 91.0,
  "lon": 34.5,
  "station_id": "TEL_AVIV_CENTRAL"
}
```
**בעיה:** קו רוחב מעל 90° לא קיים פיזיקלית

### דוגמה 2: קו אורך חורג מהטווח
```json
{
  "lat": 32.0,
  "lon": 200.0,
  "station_id": "HAIFA_PORT"
}
```
**בעיה:** קו אורך מעל 180° לא תקף

### דוגמה 3: Null Island (ערכי ברירת מחדל)
```json
{
  "lat": 0.0,
  "lon": 0.0,
  "station_id": "JERUSALEM_WEST"
}
```
**בעיה:** (0,0) נמצא באוקיינוס האטלנטי, לא בישראל - מצביע על איפוס מערכת

### דוגמה 4: קואורדינטות מחוץ לישראל
```json
{
  "lat": 45.0,
  "lon": 35.0,
  "station_id": "NEGEV_SOUTH"
}
```
**בעיה:** מיקום ברומניה, לא בישראל

### דוגמה 5: קואורדינטות הפוכות
```json
{
  "lat": 34.8,
  "lon": 32.0,
  "station_id": "EILAT_AIRPORT"
}
```
**בעיה:** הערכים מוחלפים - צריך להיות Lat: 32.0, Lon: 34.8

### דוגמה 6: מחרוזת במקום מספר
```json
{
  "lat": "32.5",
  "lon": 34.8,
  "station_id": "BEER_SHEVA"
}
```
**בעיה:** קו רוחב נשלח כמחרוזת, עלול לגרום לשגיאות השוואה

## פתרון מומלץ
1. **Range Validation:** אמת שהקואורדינטות בטווח הפיזיקלי התקף
2. **Geographical Bounds:** בדוק שהמיקום נמצא באזור התפעול של ישראל
3. **GPS Health Check:** בצע בדיקת תקינות GPS לפני קבלת נתונים
4. **Fallback to Last Known Position:** במקרה של כשל, השתמש במיקום האחרון הידוע
5. **Type Checking:** ודא שהקואורדינטות הן מספרים ולא מחרוזות
6. **Alert on Anomalies:** שלח התראה כאשר מיקום קופץ מעל X ק"מ פתאום
7. **Coordinate Swap Detection:** זהה אוטומטית קואורדינטות הפוכות

## קוד דוגמה לאימות
```python
class GeoValidator:
    # ישראל - גבולות מורחבים מעט לכיסוי אזורים גבוליים
    ISRAEL_BOUNDS = {
        'lat_min': 29.0,
        'lat_max': 33.5,
        'lon_min': 34.0,
        'lon_max': 36.0
    }
    
    @staticmethod
    def validate_coordinates(lat, lon, strict_israel=True):
        # בדיקת טווח פיזיקלי
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise TypeError("Coordinates must be numeric")
        
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude {lat} out of valid range [-90, 90]")
        
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude {lon} out of valid range [-180, 180]")
        
        # בדיקת גבולות ישראל
        if strict_israel:
            if not (GeoValidator.ISRAEL_BOUNDS['lat_min'] <= lat <= GeoValidator.ISRAEL_BOUNDS['lat_max']):
                raise ValueError(f"Latitude {lat} outside Israel operational zone")
            
            if not (GeoValidator.ISRAEL_BOUNDS['lon_min'] <= lon <= GeoValidator.ISRAEL_BOUNDS['lon_max']):
                raise ValueError(f"Longitude {lon} outside Israel operational zone")
        
        # בדיקת Null Island
        if lat == 0.0 and lon == 0.0:
            raise ValueError("Coordinates at (0,0) indicate system reset or GPS failure")
        
        return True

# Example usage
try:
    GeoValidator.validate_coordinates(91.0, 34.5)
except ValueError as e:
    print(f"GEO_OUT_OF_BOUNDS: {e}")
```

## Status Code
**400 Bad Request** - קואורדינטות לא תקפות

## Severity
🟡 **MEDIUM** - עלול להשפיע על דיוק תחזיות אך לא משבית את המערכת

## קטגוריה
Data Validation Error / Sensor Error
