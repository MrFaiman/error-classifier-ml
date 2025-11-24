#### 📄 קובץ: `MISSING_FIELD.md`
```markdown
# Meteo-IL Error: MISSING_FIELD

## תיאור השגיאה
אובייקט ה-JSON הגיע ללא אחד משדות החובה (Mandatory Fields).

## סיבות נפוצות (Root Cause)
1. **Sensor Malfunction:** רכיב ספציפי בתחנה (למשל מד רוח) נשרף או נותק, והבקר משמיט את השדה מהדיווח.
2. **Network Packet Loss:** איבוד מידע חלקי בתעבורת UDP (פחות נפוץ ב-JSON, אך אפשרי בפרסור לא תקין).

## דוגמה לקלט שגוי
```json
{
  "location": {...},
  "timestamp": "...",
  // חסר שדה: wind_speed_knots
}