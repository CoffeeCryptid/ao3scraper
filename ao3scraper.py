#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 01:04:16 2022

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

class Work():
    def __init__(self, input):
        self.extract_info(input)
        self.process_chapters()
        self.process_word_count()
        
    def extract_info(self, input):
        # id, title, authors, date
        self.id = int(input.attrib["id"][5:])
        self.title = input.cssselect("h4.heading > a:first-child")[0].text
        self.authors = tuple(x.text for x in input.cssselect("h4.heading > a[rel='author']"))
        self.date = input.cssselect("p.datetime")[0].text
        # Required tags, that square in the upper left corner
        req_tags = input.cssselect("ul.required-tags > li > a > span")
        for tag in req_tags:
            tagclass = tag.attrib["class"].split(" ")[1]
            self.__dict__[tagclass] = tag.text_content()
        # tags
        self.fandoms = tuple(x.text for x in input.cssselect(".fandoms > a.tag"))
        self.warning_tags = tuple(x.text for x in input.cssselect("li.warnings a.tag"))
        self.pairings = tuple(x.text for x in input.cssselect("li.relationships > a"))
        self.characters = tuple(x.text for x in input.cssselect("li.characters > a"))
        self.freeform = tuple(x.text for x in input.cssselect("li.freeforms > a"))
        # description
        description = input.cssselect(".summary > p")
        self.description = description[0].text if len(description) > 0 else None
        # stats
        stats = input.cssselect("dl.stats > dd")
        for tag in stats:
            tagclass = tag.attrib["class"]
            self.__dict__[tagclass] = tag.text_content()
    
    def process_chapters(self):
        """ Split number of chapters (1/? -> [1, None]) """
        result = []
        for chap in self.chapters.split("/"):
            try:
                chap = int(chap)
            except ValueError:
                chap = None 
            result.append(chap)
        
        self.chap_cur, self.chap_total = result
    
    def process_word_count(self):
        """ Convert string variable word count to integer """
        try:
            self.words = locale.atoi(self.words)
        except ValueError:
            self.words = 0
            
    def fetch(self, key):
        """Extract information like authors, tags, etc."""
        if key == "main":
            attribs = ["id", "title", "date", "rating", "category", "warnings", 
                       "iswip", "description", "language", "words", "chap_cur", "chap_total"]
            stats = ["comments", "kudos", "bookmarks", "hits"]
            row = [self.__dict__[attrib] for attrib in attribs]
            # stats: comments, kudos, bookmarks, hits
            for stat in stats:
                row.append(int(self.__dict__.get(stat, "0")))
            return [row]
        
        else: 
            id = self.id
            content = self.__dict__[key]
            table = []
            for item in content:
                table.append([id, item])
            return table
    
def create_tables(outdir, tables):
    """ Create empty csv files """
    for name, filepath in tables.items():
        with open(filepath, "w") as file:
            writer = csv.writer(file, delimiter = ";")
            if name == "main":
                #main table
                header = ("id", "title", "date", "rating", "category", "warnings", 
                          "iswip", "description", "language", "words", "chap_cur", 
                          "chap_total", "comments", "kudos", "bookmarks", "hits")
                writer.writerow(header)
            else:
                header = ("id", name)
                writer.writerow(header)

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
    table_names = ["main", "authors", "fandoms", "warning_tags", "pairings", "characters", "freeform"]
    table_paths = {table: os.path.join(outdir, table + ".csv") for table in table_names}
    create_tables(outdir, table_paths)
    
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
        works = [Work(node) for node in root.cssselect("li.work")]
        tables = {table: [] for table in table_names}
        
        for key in table_names:
            for work in works:
                tables[key] += work.fetch(key)
            append_to_table(table_paths[key], tables[key])
            
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