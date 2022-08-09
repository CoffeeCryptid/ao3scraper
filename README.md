# AO3 Scraper

A Python script to scrape search results from AO3.

## How to use:

```
python3 ao3scraper.py <url> -o <output directory> -p <number of pages>
```

- url: URL of AO3 search results
- -o / output directory: path of output directory (optional argument)
- -p / number of pages: maximum number of pages to scrape (optional argument)

## Dependencies:

- requests
- lxml
- csv

## Output:

AO3 Scraper outputs several csv files. main.csv contains id, title, category, etc. of every work. 
Since every work can have several authors and a large number of tags, this information is stored in other csv files:

- authors.csv  
- warnings.csv  
- fandoms.csv  
- pairings.csv  
- characters.csv  
- tags.csv  

The files can be merged by the id variable.

## Why another AO3 scraper?

I'm aware there is already [another AO3 Scraper](https://github.com/radiolarian/AO3Scraper/).
I've written this scraper primarily for my own needs, which are rather different from what radiolarian's AO3 scraper does.
The AO3 scraper by radiolarian scrapes IDs from the search results and then scrapes the individual works.
This scraper serves a different purpose, which is to scrape as much information as possible directly from the search results.
