from pywikibot import family

class Family(family.Family):
    name = 'noita'

    langs = {   # All available languages are listed here.
        'en': None,
        'ja': None,
        'tr': None,
        'zh': None,
    }

    def protocol(self, code):
        return 'HTTPS'

    def version(self, code):
        return "1.39.0"  # The MediaWiki version used. 
    
    def hostname(self,code):
        return 'noita.wiki.gg' # The same for all languages

    def scriptpath(self, code):
        return '/%s' % code # The language code is included in the path
