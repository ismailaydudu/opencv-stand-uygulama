# v3.2 — Daha doğal birleştirme ve kalıcı ayarlar

## v3.2 yenilikleri
- Kişinin hemen çevresindeki fon örneklenerek ışık ve renk uyumu yapılır; tüm fonun ortalamasından kaynaklanan gereksiz renk kayması azaltılır.
- Kişinin arkasına ince, ayarlanabilir ortam gölgesi eklenir. Fotoğraf yüzü veya kıyafeti yeniden üretilmez.
- Arka plan, blur, ışık uyumu, gölge ve IEEE imzası seçenekleri fotoğraf işlenirken ayarlar.json dosyasına kaydedilir; uygulama tekrar açılınca korunur.
- Bu sürüm SDXL-Turbo veya ücretli API çağırmaz. `rembg` yalnızca kişiyi fondan ayırır; sahne ve kıyafet üretmez.

## Güncelleme
Uygulamayı kapatıp bu ZIP içindeki dosyaları çalışan proje klasörüne kopyalayın ve aynı adlı dosyaları değiştirin. `.venv` ve `ciktilar` klasörlerini silmeyin. Ardından `2_BASLAT.bat` çalıştırın. `assets/backgrounds` klasörünün tamamı bulunmalı.

## Mevcut uygulamayı güncelleme
Uygulamayı kapatın. Bu ZIP'in içindeki IEEE_Trakya_Stand klasörünün **içeriğini** eski çalışan klasörün içine kopyalayın ve aynı adlı dosyaları değiştirin. `.venv` ve `ciktilar` klasörlerini silmeyin. Sonra doğrudan **2_BASLAT.bat** çalıştırın. V2 modelleri daha önce indiyse bu sürüm için yeni model veya paket indirmesi yoktur. `assets/backgrounds` klasörünü de mutlaka kopyalayın.

## Beş seçenek
Makine - Fabrika; Genetik - Laboratuvar; Bilgisayar - IT ofisi; Elektrik - Santral; Network - Veri merkezi. Üstteki Arka plan listesinden seçin. Yeni fotoğraf seçilen fonla kaydedilir. Mevcut fotoğrafta fon veya ayar değiştirmek için **Son fotoğrafa uygula ve kaydet** düğmesine basın. Yeni JPG oluşturulur; eski sonuç silinmez. Bu işlem kişiyi yeniden AI'dan geçirmez.

## Yakınlaştırma düzeltmesi
Eski sürümdeki zorunlu 1280×720 merkez kırpması kaldırıldı. Dikey fotoğraf dikey, yatay fotoğraf yatay kalır; kaynak kadrajın tamamı korunur. 4096 pikselden büyük kenar varsa sadece orantılı küçültülür; küçük fotoğraf büyütülmez. Fon, kişinin fotoğrafının boyutuna uyarlanır. Kamera görüntüsü de kaynaktan gelen oranla işlenir. EXIF yön bilgisi uygulanır.

## Görsel tarz
Beş fon, yerleşik görsel üretici ile doğal fotoğraf tarzında üretilmiş temsili mekânlardır; gerçek Trakya Üniversitesi mekânlarının fotoğrafları değildir. Fütüristik/neon fon yerine fabrika makineleri, genetik laboratuvar cihazları, yazılım ofisi, santral kontrol panoları ve sunucu rafları kullanılır. Kulüp imzası küçültüldü ve isteğe bağlıdır. Yüz yeniden üretilmez. Fonun fotoğraf tarzında olması her kişinin ışığı ve perspektifiyle kusursuz eşleşeceği anlamına gelmez.

Renk uyumu ve Arka plan yumuşaklığı ayarları korunur. Ayar değişince Son fotoğrafa uygula ve kaydet düğmesine basın. Kalıcı varsayılanlar ayarlar.json dosyasındadır.

## Kaynak dosyalar
Beş fon `assets/backgrounds/fabrika.png`, `genetik.png`, `yazilim.png`, `santral.png`, `network.png` dosyalarıdır. Kullanıcı örneği üzerinde beş fon çıktısı `muhendislik_ornekleri` klasöründe bulunur. Eski ONCE_OKU.md dosyasındaki v2 çalışma/kurulum açıklamaları geçerlidir; kadraj ve fon kullanımı için bu belge önceliklidir.

## Üretim promptu
Her fon ayrı bir yerleşik imagegen çağrısıyla üretildi. Ortak yönerge: photorealistic-natural; landscape 3:2 empty photo booth background; eye-level 50mm photography; natural restrained colors and realistic textures; gentle depth of field; center usable for vertical crops; no people, text, logos, neon, CGI, HDR or dramatic glow. Mekânlar sırasıyla CNC ve robot kollu üretim fabrikası, moleküler biyoloji/genetik laboratuvarı, çift monitörlü yazılım ofisi, SCADA panolu santral kontrol odası ve sunucu/network raflı veri merkezidir. Dikey fonda ekipmanların görünürlüğü için yatay kırpma odağı ayarlanır; kişinin fotoğrafı kırpılmaz.

## Doğrulama
Dikey 843×1264 kullanıcı fotoğrafı beş fonla 843×1264 kaydedildi. Dikey, yatay, kare ve büyük dosya oranları ile köşe piksellerinin korunması kontrol edildi. Windows kamera arayüzü burada çalıştırılamadı; ilk açılışta fon listesini ve kaydı bilgisayarınızda deneyin.

## Ayrıntı ve kişi uyumu
Varsayılan arka plan bulanıklığı 0: fon artık bilerek bulanıklaştırılmaz. Yüz/gövde yumuşatma kaldırıldı. Kişi ışık / renk uyumu kaydırıcısı, kişinin parlaklığını ve renk sıcaklığını fon yönünde sınırlı değiştirir; yüzün şekli ve kıyafetler yeniden üretilmez. 0 konumu bu renk/ışık değişimini kapatır.
Kaynak fotoğraf 4096 piksele kadar büyütülmeden/kırpılmadan korunur. Daha büyük fotoğraf orantılı küçültülür. JPG kalite 96 ve renk alt örneklemesi kapalıdır. Fon kaynakları 1536×1024 olduğundan büyük çıktıda fon ölçeklenir; gerçek 4K/iPhone sensör ayrıntısı iddiası yoktur. HEIC doğrudan desteklenmez; iPhone fotoğrafını JPEG/PNG olarak aktarın. Çok büyük dosyalar daha fazla RAM ve işlem süresi gerektirir.
