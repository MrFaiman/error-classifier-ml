#### 📄 קובץ: `REGEX_MISMATCH.md`
```markdown
# SkyGuard Error: REGEX_MISMATCH

## תיאור השגיאה
פורמט המחרוזת אינו תואם לביטוי הרגולרי (Regex) שהוגדר. נפוץ מאוד בשדות קוד כמו `transponder_code`.

## סיבות נפוצות (Root Cause)
1. **Legacy Systems:** מטוסים ישנים (F-15/16 מדגמים מוקדמים) המשדרים קוד הקסדצימלי (A-F) במקום אוקטלי (0-7).
2. **Data Corruption:** שיבוש בתקשורת שהפך ביטים, יצר תווים לא חוקיים.
3. **Manual Entry:** הטייס הזין קוד ידני שגוי (פחות מ-4 ספרות או יותר).

## דוגמה לקלט שגוי
```json
{
  "transponder_code": "12A4"  // האות A אסורה
}