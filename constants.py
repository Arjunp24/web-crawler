SEED_URLS = ['http://en.wikipedia.org/wiki/Barack_Obama',
             'http://en.wikipedia.org/wiki/Family_of_Barack_Obama',
             'https://people.com/tag/sasha-obama/',
             'https://people.com/tag/malia-obama/']

BAD_CONTENT = [' wiki against automated account creation', 'Wikipedia does not have an article',
                  'We could not find the above page',
                  'Other reasons this message may be displayed', 'No pages link to', 'Click on a date time to view',
                  'Enter a page name to see changes', 'Get Our Newsletter']

BAD_LINKS = ['ads.', 'ad.', 'index.php', 'archive.org', 'mailto:', '?share=sms',
                        'javascript:', 'www.politico.com', 'whatsapp://', 'fb-messenger://', 'sms://',
                        'pinterest', 'signin?']

KEYWORDS = ["obama", "family", "michelle", "sasha"]

URL_KEYWORD_SCORE_DICT = {"obama": 100, "family": 50, "michelle": 20, "sasha": 20, "barack": 30}

ANCHOR_TEXT_KEYWORD_DICT = {"obama": 200, "family": 110, "michelle": 50, "sasha": 50, "barack": 60}

WEB_PAGES_TO_CRAWL = 40000
