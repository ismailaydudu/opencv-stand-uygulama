"""Stanttan ÖNCE internet açıkken model indir ve deneme hesaplaması yap."""
from core import Processor
if __name__ == '__main__':
    print('Model hazırlanıyor; ilk seferde indirilmesi zaman alabilir.', flush=True)
    processor = Processor()
    print('Model hazır. Artık aynı bilgisayar ve kullanıcıyla çevrimdışı çalışabilirsiniz.')
