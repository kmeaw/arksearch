#!/usr/bin/env python
#
# Copyright 2016 Major Hayden
# Copyright 2017 kmeaw
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
Searches Intel's ARK site and returns data about various processors.

TOTALLY UNOFFICIAL. ;)
"""
from bs4 import BeautifulSoup
import HTMLParser

import click
import requests

from terminaltables import AsciiTable

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like"
              "Gecko) Chrome/47.0.2526.111 Safari/537.36")


def get_full_ark_url(quickurl):
    full_url = "http://ark.intel.com{0}".format(quickurl)
    return full_url


def get_cpu_html(quickurl):
    """Connect to Intel's ark website and retrieve HTML."""
    full_url = get_full_ark_url(quickurl)
    headers = {
        'User-Agent': USER_AGENT,
    }
    r = requests.get(full_url, headers=headers)
    return r.text


def generate_table_data(*html_outputs):
    """Generate an ASCII table based on the HTML provided."""

    table_data = [
    ]

    keys = {}

    hp = HTMLParser.HTMLParser()

    for i, html_output in enumerate(html_outputs):
        soup = BeautifulSoup(html_output, 'html.parser')
        for table in soup.select('ul.specs-list'):
            rows = table.find_all("li")
            for row in rows:
                key = row.find('span', class_='label').get_text("\n", strip=True)
                value = hp.unescape(row.find('span', class_='value').get_text("\n", strip=True))

                if key == 'T\nCASE':
                    key = 'T(CASE)'
                if "\n" in key:
                    key = key[:key.index("\n")]

                if key not in keys:
                    keys[key] = len(keys)
                    table_data.append([key] + [None] * len(html_outputs))
                table_data[keys[key]][i + 1] = value

    if len(html_outputs) > 1:
        table_data = filter(lambda row: len(set(row[1:])) > 1, table_data)
    table_data.insert(0, ['Parameter'] + ['Value'] * len(html_outputs))

    return table_data


def quick_search(*search_terms):
    result = []
    for search_term in search_terms:
        url = "http://ark.intel.com/search/AutoComplete?term={0}"
        headers = {
            'User-Agent': USER_AGENT,
        }
        r = requests.get(url.format(search_term, headers=headers))
        result.append(r.json())
    return result


@click.command()
@click.argument('search_terms', nargs=-1)
@click.pass_context
def search(ctx, search_terms):
    """Main function of the script."""
    ark_jsons = quick_search(*search_terms)
    cpu_data = []

    for ark_json, search_term in zip(ark_jsons, search_terms):
        if len(ark_json) < 1:
            click.echo("Couldn't find any processors matching "
                       "{0}".format(search_term))
            ctx.exit(0)

        click.echo(u"Processors found: {0}".format(len(ark_json)))
        choice_dict = {}
        counter = 0
        for cpu in ark_json:
            choice_dict[counter] = cpu['quickUrl']
            click.echo(u"[{0}] {1}".format(counter, cpu['value']))
            counter += 1
        if counter == 1:
            choice = 0
        else:
            choice = click.prompt(u"Which processor", prompt_suffix='? ', type=int)

        cpu_data.append(get_cpu_html(choice_dict[int(choice)]))

    table_data = generate_table_data(*cpu_data)
    table = AsciiTable(table_data)
    click.echo(table.table)
    ctx.exit(0)

if __name__ == '__main__':
    search()
