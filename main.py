import logging
logging.basicConfig(filename='logs', format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)

from optparse import OptionParser

from epubsearch import EpubParser
from epubsearch import EpubIndexer
from epubsearch import WordMorphoGenerator

import zipfile,os.path
import shutil


def unzip(source_filename, dest_dir):
    with zipfile.ZipFile(source_filename) as zf:
        path = dest_dir
        zf.extractall(path)

def zipdir(source_dir, dest_zip):
    with zipfile.ZipFile(dest_zip, 'w') as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                zf.write(os.path.join(root, file))


class EpubWorker(object):
    '''

    '''
    def __init__(self, book_address, lang='ru'):
        self.is_epub = False
        if book_address[-4:] == 'epub':
            self.is_epub = True
            logging.info('Uncompress {}'.format(book_address))
            book_name = book_address[book_address.rfind('/')+1:-5]
            self.dest_dir = './tmp/'+book_name
            unzip(book_address, self.dest_dir)
            book_address = self.dest_dir

        epub = EpubParser(book_address)
        self.index = EpubIndexer('whoosh')
        logging.info('Indexing')
        self.index.load(epub)

    def search_word(self, search_word):
        logging.info('Search word {}'.format(search_word))
        return self.index.search(search_word)

    def search_lexemes(self, search_word):
        logging.info('Generate words for search')
        search_words = WordMorphoGenerator(search_word).generate()
        logging.info('Search word {} and lexemes'.format(search_word, search_words))
        results_dirty = []
        results_formatted = []
        for word in search_words:
            results_dirty.append(self.index.search(word))
        for result in results_dirty:
            result = result.get('results')
            if result:
                for item in result:
                    results_formatted.append(item['baseCfi'])

        return {'word': search_word,
                'lexemes': search_words,
                'results': results_formatted}

    def close(self):
        shutil.rmtree(self.dest_dir)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.is_epub:
            shutil.rmtree(self.dest_dir)



def get_parameters():
    """
        Parse the user input
    """
    parser = OptionParser()
    parser.add_option('-b', '--book-address', dest='book_address')
    parser.add_option('-s', '--search', dest='search')
    parser.add_option('--lang', dest='language')
    parser.add_option('--lexemes', dest='lexemes')
    (options, args) = parser.parse_args()

    if not options.book_address:
        options.book_address = "Sensei4/"
    else:
        return {'book_address': options.book_address,
                'search': options.search, 'language': options.language, 'lexemes': options.lexemes}


def main():
    logging.info('*'*20)
    # get user defined parameters
    userParams = get_parameters()

    search = userParams['search']
    book_address = userParams['book_address']
    language = userParams['language']
    lexemes = userParams['lexemes']

    with EpubWorker(book_address, language) as worker:
        if lexemes:
            return worker.search_lexemes(search)
        return worker.search_word(search)

if __name__ == '__main__':
    # logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', level=logging.DEBUG)
    print(main())

