#### 📄 קובץ: `GEO_OUT_OF_BOUNDS.md`
```markdown
# Meteo-IL Error: GEO_OUT_OF_BOUNDS

## תיאור השגיאה
הקואורדינטות (קו רוחב/אורך) שהתקבלו נמצאות מחוץ לגבולות הגיאוגרפיים של מדינת ישראל או מחוץ לטווח הפיזיקלי האפשרי (-90 עד 90).

## סיבות נפוצות (Root Cause)
1. **GPS Failure:** רכיב ה-GPS בתחנה המטאורולוגית איבד סנכרון לווייני ו"זרק" מיקום אקראי.
2. **Configuration Error:** התחנה הוגדרה ידנית עם קואורדינטות הפוכות (Lat במקום Lon).
3. **Spoofing:** שיבוש GPS אזורי הגורם לדיווח מיקום שגוי.

## דוגמה לקלט שגוי
```json
{
  "lat": 91.0,  // לא קיים פיזיקלית
  "lon": 34.0
}