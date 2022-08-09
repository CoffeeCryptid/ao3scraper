#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug  8 15:21:16 2022

@author: sarah
"""

import argparse
from sys import stdout
import os
from time import sleep
import requests
from lxml import html
import csv
import locale

def create_tables(outdir, table_main, tables):
    """ Create empty csv files """
    #main table
    header = ["id", "title", "date", "rating", "category", "warnings", 
              "iswip", "description", "language", "words", "chap_cur", 
              "chap_total", "comments", "kudos", "bookmarks", "hits"]
    with open(table_main, "w") as file:
        writer = csv.writer(file, delimiter = ";")
        writer.writerow(header)
    
    for name, filepath in tables.items():
        with open(filepath, "w") as file:
            writer = csv.writer(file, delimiter = ";")
            row = ("id", name)
            writer.writerow(row)
            
def extract_info(work):
    """ Extract all necessary info from an AO3 search result
    and return results as a dictionary"""
    results = dict()
    
    # id, title, authors, date
    results["id"] = int(work.attrib["id"][5:])
    results["title"] = work.cssselect("h4.heading > a:first-child")[0].text
    results["authors"] = tuple(x.text for x in work.cssselect("h4.heading > a[rel='author']"))
    results["date"] = work.cssselect("p.datetime")[0].text
    # Required tags, that square in the upper left corner
    req_tags = work.cssselect("ul.required-tags > li > a > span")
    for tag in req_tags:
        tagclass = tag.attrib["class"].split(" ")[1]
        results[tagclass] = tag.text_content()
    # tags
    results["fandoms"] = tuple(x.text for x in work.cssselect(".fandoms > a.tag"))
    results["warning tags"] = tuple(x.text for x in work.cssselect("li.warnings a.tag"))
    results["pairings"] = tuple(x.text for x in work.cssselect("li.relationships > a"))
    results["characters"] = tuple(x.text for x in work.cssselect("li.characters > a"))
    results["freeform"] = tuple(x.text for x in work.cssselect("li.freeforms > a"))
    # description
    description = work.cssselect(".summary > p")
    results["description"] = description[0].text if len(description) > 0 else None
    # stats
    stats = work.cssselect("dl.stats > dd")
    for tag in stats:
        tagclass = tag.attrib["class"]
        results[tagclass] = tag.text_content()
    
    return(results)

def int_or_none(string):
    """Convert a string to int, return None if conversion fails"""
    try:
        return int(string)
    except ValueError:
        return None

def parse_word_count(string):
    """ Convert word count to int, return 0 if unable to parse"""
    try:
        return locale.atoi(string)
    except ValueError:
        return 0

def split_chapter(chapters):
    """ Splits chapter numbers in the form '7/?' or '1/1' into a tuple"""
    chapters = chapters.split("/")
    return tuple(int_or_none(chapt) for chapt in chapters)

def process_main_info(input):
    """Given a single result, extract all necessary information for the main
    table (id, title, etc.) and return a row (list)"""
    attribs = ["id", "title", "date", "rating", "category", "warnings", "iswip", "description", "language"]
    stats = ["comments", "kudos", "bookmarks", "hits"]
    row_main = [input.get(attrib) for attrib in attribs]
    # word count
    row_main.append(parse_word_count(input.get("words")))
    # chapters
    for chap in input.get("chapters").split("/"):
        row_main.append(int_or_none(chap))
    # stats: comments, kudos, bookmarks, hits
    for stat in stats:
        row_main.append(int(input.get(stat, "0")))
        
    return row_main

def process_tag_info(works, key):
    """Given a list of results, extract information like authors, tags, etc.
    and output a long-format table"""
    table = []
    for work in works:
        id = work.get("id") 
        content = work.get(key, tuple())
        for item in content:
            table.append([id, item])
    return table

def append_to_table(filepath, rows):
    """Append a list of rows to a csv file"""
    with open(filepath, "a") as file:
        writer = csv.writer(file, delimiter = ";")
        writer.writerows(rows)
        
def get_next_page(root):
    """ Extract url of the next page from an ao3 page.
    Returns a tuple:
        - is there a next page?
        - the url"""
    next = root.cssselect("li.next > a")
    if len(next) > 0:
        return (True, "https://archiveofourown.org/" + next[0].attrib["href"])
    else:
        return (False, None)
        
def get_all_works(url, outdir, pages):
    """ Extract all results from a search, and save the results to several
    csv files """
    not_finished = True
    n = 1
    stdout.write("Scraping search results")
    stdout.flush()
    
    # Create necessary tables
    table_main = os.path.join(outdir, "main.csv")
    tables = ["authors", "fandoms", "warnings", "pairings", "characters", "tags"]
    tables = {table: os.path.join(outdir, table + ".csv") for table in tables}
    create_tables(outdir, table_main, tables)
    
    # Extract results until there's no next page
    while not_finished:
        stdout.write(".")
        stdout.flush()
        response = requests.get(url)
        
        # Bad response -> we fucked up
        if response.status_code != 200:
            print("Something went wrong. Status code: " + str(response.status_code))
            break
        
        # Get page and extract works
        page = response.text
        root = html.document_fromstring(page)
        works = root.cssselect("li.work")
        
        results = [extract_info(work) for work in works]
        table = [process_main_info(result) for result in results]
        append_to_table(table_main, table)
        for key, filepath in tables.items():
            table = process_tag_info(results, key)
            append_to_table(filepath, table)
            
        not_finished, url = get_next_page(root)
        n += 1
        if n > pages:
            break
        
        sleep(5)
    
    stdout.write("\n")
    stdout.flush()
        
def main():
    # Set locale (needed to parse word count)
    locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description = "A03 Parser")
    parser.add_argument("url")
    parser.add_argument("-o", "--output", help = "Output directory", required = False, default = os.getcwd())
    parser.add_argument("-p", "--pages", help = "Number of pages", type = int, required = False, default = 5001)
    args = parser.parse_args()

    get_all_works(args.url, args.output, args.pages)
    
if __name__ == '__main__':
   main()