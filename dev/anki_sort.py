import requests
import logging


class AnkiExporter:
    ANKICONNECT_URL = 'http://127.0.0.1:8765'

    def change_deck(self, type_, tier):
        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'findCards',
            'version': 6,
            'params': {
                'query': f'card:Forward tag:zhlib tag:{type_} tag:tier{tier} -tag:*HSK*'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'changeDeck',
            'version': 6,
            'params': {
                'cards': response['result'],
                'deck': f'Chinese::{type_}::tier{tier}::zh->en'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'findCards',
            'version': 6,
            'params': {
                'query': f'card:Reverse tag:zhlib tag:{type_} tag:tier{tier} -tag:*HSK*'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'changeDeck',
            'version': 6,
            'params': {
                'cards': response['result'],
                'deck': f'Chinese::{type_}::tier{tier}::en->zh'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        return 1

    def change_deck_hsk(self, lv):
        type_ = 'Vocab'

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'findCards',
            'version': 6,
            'params': {
                'query': f'card:Forward tag:zhlib tag:{type_} tag:HSK_Level_{lv}'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'changeDeck',
            'version': 6,
            'params': {
                'cards': response['result'],
                'deck': f'Chinese::{type_}::HSK{lv}::zh->en'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'findCards',
            'version': 6,
            'params': {
                'query': f'card:Reverse tag:zhlib tag:{type_} tag:HSK_Level_{lv}'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        r = requests.post(self.ANKICONNECT_URL, json={
            'action': 'changeDeck',
            'version': 6,
            'params': {
                'cards': response['result'],
                'deck': f'Chinese::{type_}::HSK{lv}::en->zh'
            }
        })
        response = r.json()
        if response['error']:
            logging.error(response['error'])
            return 0

        return 1


if __name__ == '__main__':
    for t in range(1, 7):
        AnkiExporter().change_deck_hsk(t)
