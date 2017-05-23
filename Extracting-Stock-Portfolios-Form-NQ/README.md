# Extracting Stock Portfolios from Form NQ

Registered investment management companies are required to 
submit SEC [Form N-Q](https://www.sec.gov/files/formn-q.pdf) 
as full disclosures of their stock holdings on a semiannual basis. 
These are publicly available in the Electronic Data Gathering, 
Analysis, and Retrieval 
[(EDGAR) database](https://www.sec.gov/edgar/searchedgar/companysearch.html).

I decided to extract the forms and wrangle them into a structured format with 
columns for stock holdings
to see what trends become apparent. You can see my blog post with more detail
[here](https://medium.com/@dwolfATL/c929bc400f6a).

* nq_wrangling.py has the Python wrangling script
* CIKs.csv has a list of SEC registered companies by CIK (Central Index Key)
* companylist.csv has a list of publicly traded companies on NYSE/NASDAQ
* filings_sample folder has examples of forms downloaded through 
[R EDGAR package](https://github.com/cran/edgar/tree/master/R)

