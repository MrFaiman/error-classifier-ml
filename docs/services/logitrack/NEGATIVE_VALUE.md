#### 📄 קובץ: `NEGATIVE_VALUE.md`
```markdown
# LogiTrack Error: NEGATIVE_VALUE

## תיאור השגיאה
התקבל מספר שלילי בשדה שאמור לייצג כמות פיזית (מלאי).

## סיבות נפוצות (Root Cause)
1. **Human Error (טעות אנוש):** אפסנאי ניסה להקליד מקף או ניסה לבצע פעולת חיסור דרך שדה הכמות (למשל `-10` כדי להוריד 10 פריטים).
2. **UI Bug:** מערכת ה-Frontend בבסיס אפשרה הזנת מינוס בטופס.

## דוגמה לקלט שגוי
```json
{
  "item_id": "MISSILE-X",
  "quantity": -50
}