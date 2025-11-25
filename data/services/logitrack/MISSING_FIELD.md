# LogiTrack Error: MISSING_FIELD

## תיאור השגיאה
שדה חובה חסר מהבקשה או שהתקבל כ-null/undefined/missing.

## סיבות נפוצות (Root Cause)
1. **Data Corruption (שיבוש נתונים):** שדה חובה נמחק או לא נשמר במהלך העברת הנתונים
2. **Integration Error (שגיאת אינטגרציה):** מערכת חיצונית לא שלחה שדה חובה
3. **Incomplete Request (בקשה חלקית):** המשתמש לא מילא שדה חובה בטופס
4. **Database Error (שגיאת מסד נתונים):** שדה חסר עקב שגיאה במסד הנתונים
5. **Packet Loss (אובדן מנות):** נתונים חלקיים התקבלו עקב בעיות רשת

## דוגמאות לקלט שגוי

### דוגמה 1: שדה item_id חסר
```json
{
  "quantity": 100,
  "base_id": "BASE_NEVATIM"
}
```
**בעיה:** השדה `item_id` חובה אך חסר מהבקשה

### דוגמה 2: שדה base_id חסר
```json
{
  "item_id": "MISSILE-X",
  "quantity": 50
}
```
**בעיה:** השדה `base_id` נדרש לניתוב אך חסר

### דוגמה 3: שדה מוגדר כ-undefined
```json
{
  "item_id": "MISSILE-X",
  "quantity": 50,
  "base_id": undefined
}
```
**בעיה:** השדה `base_id` קיים אך ערכו undefined

### דוגמה 4: רשימת מלאי ריקה
```json
{
  "inventory": []
}
```
**בעיה:** רשימת המלאי ריקה - אין נתונים לעדכון

### דוגמה 5: אובייקט ריק
```json
{
  "location": {}
}
```
**בעיה:** נשלח אובייקט ריק במקום נתוני מיקום

## פתרון מומלץ
1. **Validation:** ודא שכל השדות החובה קיימים לפני שליחת הבקשה
2. **Default Values:** הגדר ערכי ברירת מחדל לשדות לא קריטיים
3. **Error Messages:** הצג הודעת שגיאה ברורה למשתמש עם רשימת השדות החסרים
4. **Schema Validation:** השתמש בסכימת JSON Schema לאימות מבנה הנתונים
5. **Monitoring:** עקוב אחר שגיאות MISSING_FIELD לזיהוי בעיות אינטגרציה

## קוד דוגמה לאימות
```python
required_fields = ['item_id', 'quantity', 'base_id']
missing_fields = [field for field in required_fields if field not in data or data[field] is None]

if missing_fields:
    raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
```

## Status Code
**400 Bad Request** - הבקשה חסרה שדות חובה

## קטגוריה
Data Validation Error
