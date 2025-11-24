#### 📄 קובץ: `SECURITY_ALERT.md`
```markdown
# LogiTrack Error: SECURITY_ALERT

## תיאור השגיאה
זוהה דפוס המעיד על ניסיון הזרקת קוד (SQL Injection או XSS) באחד משדות הטקסט החופשיים.

## סיבות נפוצות (Root Cause)
1. **Malicious Activity:** ניסיון פנימי או חיצוני לחדור לבסיס הנתונים של הלוגיסטיקה.
2. **Penetration Testing:** צוות "צוות אדום" (Red Team) מבצע בדיקות חדירות למערכת.

## דוגמה לקלט שגוי
```json
{
  "base_id": "BASE_X; DROP TABLE inventory;"
}