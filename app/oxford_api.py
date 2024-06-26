import requests
import logging
from bs4 import BeautifulSoup


async def get_data(word, blurred):
    url = f"https://www.oxfordlearnersdictionaries.com/definition/english/{word}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        definitions = []
        for definition in soup.find_all(class_='def'):
            if blurred:
                definitions.append(definition.text.strip().lower().replace(word, '_' * len(word)).replace(word[:-1], '_' * len(word[:-1])).replace(word[:-2], '_' * len(word[:-2])))
            else:
                definitions.append(definition.text.strip())

        examples = []
        for example in soup.find_all(class_='x'):
            if blurred:
                example_text = example.text.strip().lower().replace(word, '_' * len(word)).replace(word[:-1], '_' * len(word[:-1])).replace(word[:-2], '_' * len(word[:-2]))
            else:
                example_text = example.text.strip()
            examples.append(example_text)

        return {
            'definitions': definitions[:2] if definitions else None,
            'examples': examples[:2] if examples else None
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving data for word '{word}': {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error retrieving data for word '{word}': {e}")
        return None
