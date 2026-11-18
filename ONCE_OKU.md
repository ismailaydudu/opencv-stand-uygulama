# IEEE Trakya Fotoğraf Standı — v3.2

## Bu uygulama ne yapıyor?

Kameradan veya seçilen fotoğraftan kişiyi yerel olarak ayırır; fabrikaya, laboratuvara, IT ofisine, santrale veya veri merkezine yerleştirir. Fotoğraf internet servisine gönderilmez. **SDXL-Turbo ve ücretli API kullanılmaz.** Kişiyi fondan ayırmak için `rembg` adlı yerel kesim modeli gerekir; bu model yalnızca kişiyi maskeleyip arka planı değiştirmeye yarar, kişinin yüzünü/kıyafetini üretmez.

## Kurulum ve başlatma

- Yeni bilgisayarda Python 3.12 64-bit kurulu olmalı. `1_KUR.bat` paketleri kurar ve insan kesim modelini indirir; ilk seferde internet gerekir.
- Kurulu uygulamada `2_BASLAT.bat` ile açın.
- `3_GUNCELLE.bat` yalnızca insan kesim modelini hazırlar. SDXL-Turbo indirmez.
- Bu ZIP ile mevcut uygulamayı güncellerken uygulamayı kapatıp ZIP içindeki proje dosyalarını çalışan klasöre kopyalayın. Aynı adlı dosyaları değiştirin. `.venv` ve `ciktilar` klasörlerini silmeyin. `assets/backgrounds` klasörünün tamamı bulunmalı.

## Kullanım

Arka planı seçip boşluk tuşuyla fotoğraf çekin veya dosyadan fotoğraf açın. Sonuç `ciktilar` klasörüne kaydedilir. Son fotoğrafa yeni fon/ayar uygulamak için **Son fotoğrafa uygula ve kaydet** düğmesini kullanın. Bu işlem kişiyi yeniden kesmez.

Uygulama arka plan, arka plan bulanıklığı, renk/ışık uyumu, ortam gölgesi ve IEEE imzası ayarlarını fotoğraf kaydedilirken `ayarlar.json` dosyasına yazar; sonraki açılışta seçiminiz korunur.

## Görsel kalite ve sınırlar

v3.2, kişinin yakın çevresindeki fon ışığını örnekleyerek renk uyumunu hesaplar ve ayarlanabilir yumuşak bir ortam gölgesi ekler. Kaynak yüz yeniden üretilmez; orijinal ayrıntı korunur. Bu işlem kıyafet değiştirmez ve görüntü üretici gibi yeni ayrıntılar uydurmaz. Saç/kıyafet maskesindeki her kusuru kodla tamamen gidermek mümkün değildir. Fonlar temsili fotoğraflardır; gerçek Trakya Üniversitesi mekânlarını göstermeyebilir.

Kişi çekimde çok yakın veya bulanıksa çıktı da öyle olur. Kamera önizlemesinde kişiyi uygun mesafede ve yeterli ışıkta kadraja alın. Fotoğrafın oranı korunur; otomatik yakınlaştırma ve merkez kırpma yapılmaz.
