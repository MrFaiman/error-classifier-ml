# LogiTrack Error: SECURITY_ALERT

## תיאור השגיאה
זוהה דפוס חשוד המעיד על ניסיון הזרקת קוד זדוני (SQL Injection, XSS, או Command Injection) באחד משדות הקלט.

## סיבות נפוצות (Root Cause)
1. **Malicious Attack (תקיפה זדונית):** ניסיון חדירה מתוכנן למערכת הלוגיסטיקה
2. **Penetration Testing (בדיקות חדירות):** צוות Red Team מבצע אימות אבטחה
3. **Automated Bot Scanning:** סורק אוטומטי מחפש פרצות אבטחה
4. **Compromised Account (חשבון פרוץ):** משתמש לגיטימי שחשבונו נפרץ
5. **Copy-Paste Error:** משתמש העתיק בטעות קוד מקור כולל תווים מסוכנים

## דוגמאות לקלט שגוי

### דוגמה 1: SQL Injection במזהה בסיס
```json
{
  "base_id": "BASE_X; DROP TABLE inventory;",
  "item_id": "MISSILE-X",
  "quantity": 100
}
```
**בעיה:** ניסיון למחוק טבלת מלאי באמצעות פקודת SQL

### דוגמה 2: SQL Injection בשדה item_id
```json
{
  "item_id": "X' OR 1=1--",
  "quantity": 50,
  "base_id": "BASE_NEVATIM"
}
```
**בעיה:** ניסיון לעקוף אימות SQL באמצעות תנאי תמיד-אמיתי

### דוגמה 3: XSS Attack בהערה
```json
{
  "item_id": "MISSILE-X",
  "note": "<script>alert('XSS')</script>",
  "quantity": 10
}
```
**בעיה:** קוד JavaScript זדוני בשדה טקסט חופשי

### דוגמה 4: Command Injection
```json
{
  "base_id": "BASE_NEVATIM; cat /etc/passwd",
  "item_id": "MISSILE-X"
}
```
**בעיה:** ניסיון להריץ פקודות מערכת הפעלה

### דוגמה 5: XSS עם תמונה
```json
{
  "item_id": "<img src=x onerror=alert('XSS')>",
  "quantity": 100
}
```
**בעיה:** ניסיון הזרקת קוד דרך תג HTML

## פתרון מומלץ
1. **Input Validation:** אמת כל קלט מול רשימת תווים מותרים (whitelist)
2. **Parameterized Queries:** השתמש ב-Prepared Statements למניעת SQL Injection
3. **Output Encoding:** קודד כל פלט לפני הצגה למשתמש
4. **WAF (Web Application Firewall):** התקן חומת אש ליישומי אינטרנט
5. **Rate Limiting:** הגבל מספר בקשות לדקה ממקור יחיד
6. **Security Logging:** תעד כל ניסיון תקיפה לצורך חקירה
7. **Alert System:** שלח התראה מיידית לצוות האבטחה

## קוד דוגמה לזיהוי
```python
import re

# SQL Injection patterns
sql_patterns = [
    r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",  # OR 1=1
    r"(DROP|DELETE|UPDATE|INSERT)\s+(TABLE|FROM)",  # SQL commands
    r"--",  # SQL comment
    r";",   # Statement terminator
]

# XSS patterns
xss_patterns = [
    r"<script",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
]

def detect_security_threat(input_value):
    input_lower = input_value.lower()
    
    for pattern in sql_patterns + xss_patterns:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return True, f"Suspicious pattern detected: {pattern}"
    
    return False, None

# Example usage
is_threat, reason = detect_security_threat("BASE_X; DROP TABLE inventory")
if is_threat:
    raise SecurityException(f"SECURITY_ALERT: {reason}")
```

## Status Code
**403 Forbidden** - בקשה נחסמה עקב חשד לתוכן זדוני

## Severity
**CRITICAL** - דורש תשומת לב מיידית של צוות האבטחה

## קטגוריה
Security Threat / Malicious Input
