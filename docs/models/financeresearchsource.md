# FinanceResearchSource


## Fields

| Field      | Type                  | Required           | Description                                                                     | Example                                                             |
|------------|-----------------------|--------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------|
| `url`      | *str*                 | :heavy_check_mark: | The URL of the source webpage.                                                  | https://investor.apple.com/sec-filings/annual-reports/default.aspx  |
| `title`    | *Optional[str]*       | :heavy_minus_sign: | The title of the source webpage.                                                | Apple Inc. Annual Report FY2024 (Form 10-K)                         |
| `snippets` | Optional[List[*str*]] | :heavy_minus_sign: | Relevant excerpts from the source page that were used in generating the answer. | ["Record Q1 revenue of $124.3 billion", "Data center capex up 12%"] |
