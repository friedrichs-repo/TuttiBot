import sys
import os
import requests
from bs4 import BeautifulSoup
from typing import List


class TuttiQuery:
    """
    A class to parse a query to tutti.ch

    Attributes
    --------
    query : list of keywords to search for,
    separated by commas
    region : the region to search in
    for example 'ganze-schweiz' or 'bern'
    category : defining the category of the
    query, for example haushalt/moebel

    Methods
    --------
    request :  returns the set of links for the query,
    parameter 'filters', defaults to none,
    else removes links that don't contain  specified keywords
    send_links_by_mail : send links to email,
    parameter 'email_address' defines the receiver,
    parameter 'blacklist_file' defines path to file containing
    a list of links that have already been sent previously.
    """

    query: List[str]
    region: str
    category: str

    def __init__(self, query, region, category=None):
        self.query = query
        self.region = region
        self.category = category

        if not category:
            self.url = (
                "https://www.tutti.ch/de/li/"
                + self.region
                + "?q="
                + "%20".join(self.query)
            )

        elif category:
            self.url = (
                "https://www.tutti.ch/de/li/"
                + self.region
                + "/"
                + category
                + "?q="
                + "%20".join(self.query)
            )

    def request(self, filters=None):
        r = requests.get(self.url)
        soup = BeautifulSoup(r.text, "html.parser")

        atypes = soup.find_all("a")

        sub_links = []

        for t in atypes:
            sub_links.append(t.get("href"))

        if filters:
            links = [
                "https://www.tutti.ch" + str(l)
                for l in sub_links
                if any([fil in str(l) for fil in filters]) and self.region in str(l)
            ]
            return set(links)

        elif not filters:
            links = [
                "https://www.tutti.ch" + str(l)
                for l in sub_links
                if self.region in str(l)
            ]
            return set(links)

    def _check_and_update_blacklist(self, blacklist_file, links):
        f = open(blacklist_file, "r")
        blacklist = f.read().splitlines()

        new_links = []

        for link in links:
            if link not in blacklist:
                new_links.append(link)

        for link in new_links:
            with open(blacklist_file, "a") as f:
                f.write("\n" + link)

        return new_links

    def send_links_by_mail(self, email_address, blacklist_file, filters=None):
        links = self.request(filters)
        new_links = self._check_and_update_blacklist(blacklist_file, links)

        if len(new_links) > 0:
            mail_body = ""
            for link in new_links:
                if len(mail_body) != 0:
                    mail_body += " and "
                mail_body += link
            email = (
                "echo '"
                + mail_body
                + "' | mail -s 'Found new entries containing "
                + ", ".join(self.query)
                + "' "
                + email_address
            )

            res = os.system(email)
            print("Mail sent. Error code:", res)
        else:
            print("Nothing to send.")


if __name__ == "__main__":
    query = sys.argv[1].split(",")
    region = sys.argv[2]
    category = sys.argv[3]
    email_address = sys.argv[4]

    search = TuttiQuery(query, region, category)
    search.send_links_by_mail(
        email_address, "/home/friedrich/Documents/tuttibot_blacklist"
    )
