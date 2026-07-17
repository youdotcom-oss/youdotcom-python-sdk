# FinanceResearchEffort

Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

Available levels:
- `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.
- `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result.

## Example Usage

```python
from youdotcom.models import FinanceResearchEffort

value = FinanceResearchEffort.DEEP
```


## Values

| Name         | Value        |
| ------------ | ------------ |
| `DEEP`       | deep         |
| `EXHAUSTIVE` | exhaustive   |