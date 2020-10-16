"""
Get information from playoverwatch user pages.
"""

from bs4 import BeautifulSoup
import requests

URL = 'https://playoverwatch.com/en-us/career/pc/'


def get_page(user):
    """Get page using URL with username given by message."""
    page = requests.get(URL + f'{user.replace("#", "-")}/')
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup


def search_soup(soup, criteria):
    """Search inside returned HTML for certain information."""
    all_stats = []
    if criteria == 'competitive':
        for skill in soup.find_all(attrs={'class': 'competitive-rank-level'}):
            all_stats.append(skill.text.lower())
        return f'\nTank: {all_stats[0]}\nDamage: {all_stats[1]}\nSupport: {all_stats[2]}'

    for statistic in soup.find_all(attrs={'class': 'DataTable-tableColumn'}):
        all_stats.append(statistic.text.lower())

    if criteria in all_stats:
        return all_stats[all_stats.index(criteria) + 1]

    return None
