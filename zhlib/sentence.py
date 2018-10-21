from bs4 import BeautifulSoup
import requests


def jukuu(vocab):
    params = {
        'q': vocab
    }
    r = requests.get('http://www.jukuu.com/search.php', params=params)
    soup = BeautifulSoup(r.text, 'html.parser')

    for c, e in zip([c.text for c in soup.find_all('tr', {'class': 'c'})],
                    [e.text for e in soup.find_all('tr', {'class': 'e'})]):
        yield {
            'sentence': c,
            'english': e
        }
