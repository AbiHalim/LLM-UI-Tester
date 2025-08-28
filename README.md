# Team Asbujawa TikTok Tech Jam 2025

![Architecture Diagram](<img/Asbujawa TikTok Tech jam.jpg>)

## Guide for image-comparator (Abi & Judha)

1. Put `before.png` and `after.png` inside `image-comparator/input/`
2. Run `img_comparator.py` : It will generate images containing cropped portions which contain differences between the 2 images, and a manifest with extra information.
3. Run `diff_evaluator.py` : It will call Google Gemini to explain the differences, and output an `analysis_all.json`

### Example before & after image:

![Before & after ](img/example_jam5band.png)

### Output:

```
{
  "page_summary": "The AFTER page has a 'Username copied' message and a 'Share screenshot to' popup.",
  "changes": [
    {
      "id": "chg-001",
      "type": "text_change",
      "severity": "medium",
      "before_text": "9.41",
      "after_text": "9.42",
      "explanation": "The time displayed in the top left corner has changed from 9.41 to 9.42.",
      "risk": "none"
    },
    {
      "id": "chg-002",
      "type": "icon_change",
      "severity": "low",
      "before_text": "signal strength and battery",
      "after_text": "signal strength and battery",
      "explanation": "The signal strength and battery icons have changed.",
      "risk": "none"
    },
    {
      "id": "chg-003",
      "type": "visibility",
      "severity": "low",
      "before_text": "What's up?",
      "after_text": "Username copied",
      "explanation": "The 'What's up?' message has been replaced with a 'Username copied' message.",
      "risk": "none"
    },
    {
      "id": "chg-004",
      "type": "visibility",
      "severity": "medium",
      "before_text": "null",
      "after_text": "See translation",
      "explanation": "A 'See translation' button has appeared.",
      "risk": "none"
    },
    {
      "id": "chg-005",
      "type": "visibility",
      "severity": "medium",
      "before_text": "null",
      "after_text": "Share screenshot to",
      "explanation": "A 'Share screenshot to' popup has appeared.",
      "risk": "none"
    }
  ]
}
```
