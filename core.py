"""Fotoğraf işleme: arayüzden bağımsız, tekrar kullanılan tek AI oturumu."""
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import os
import time
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter
import cv2
import numpy as np
import json

ROOT = Path(__file__).resolve().parent
SIZE = (1280, 720)
# CPU'nun tamamını tüketmeyerek kameraya da işlem zamanı bırakıyoruz.
os.environ.setdefault('OMP_NUM_THREADS', '2')


def font(size):
    for name in ('C:/Windows/Fonts/arialbd.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


BACKGROUNDS = {
    'Makine - Fabrika': 'fabrika',
    'Genetik - Laboratuvar': 'genetik',
    'Bilgisayar - IT ofisi': 'yazilim',
    'Elektrik - Santral': 'santral',
    'Network - Veri merkezi': 'network',
}


def prepare_photo(photo):
    """Dikey/yatay oranı koru. Kırpma ve büyütme YOK; sadece büyük dosyayı küçült."""
    photo = ImageOps.exif_transpose(photo).convert('RGB')
    photo.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
    return photo


def brand(image):
    """Küçük ve boyuta uyumlu kulüp imzası; fotoğrafın üstünü kaplamaz."""
    width, height = image.size
    scale = min(width, height) / 900
    pad = max(6, round(18 * scale))
    size = max(10, round(21 * scale))
    draw = ImageDraw.Draw(image)
    text = 'IEEE TRAKYA  |  COMPUTER SOCIETY'
    f = font(size)
    while draw.textbbox((0, 0), text, font=f)[2] > width - 4 * pad and size > 6:
        size -= 1
        f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    draw.rounded_rectangle((pad, pad, box[2] + 3 * pad, size + 3 * pad),
                           radius=pad//2, fill=(18, 30, 40))
    draw.text((2 * pad, 2 * pad), text, font=f, fill='white')
    path = ROOT / 'assets/logo.png'
    if path.exists():
        with Image.open(path) as source:
            logo = source.convert('RGBA')
            logo.thumbnail((max(1,width//7), max(1,height//12)))
            image.paste(logo, (width-logo.width-pad, height-logo.height-pad), logo)
    return image


def refine_mask(photo, mask):
    """Kılavuzlu filtre: maskeyi fotoğrafın sınırlarına yaklaştırır.
    Büyük erozyon kullanmıyoruz; ince saç ve parmaklar kaybolmasın.
    """
    rgb = np.asarray(photo, dtype=np.float32) / 255.0
    guide = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    alpha = np.asarray(mask.convert('L'), dtype=np.float32) / 255.0
    def mean(x):
        return cv2.boxFilter(x, -1, (9, 9), borderType=cv2.BORDER_REFLECT)
    mu, mp = mean(guide), mean(alpha)
    variance = mean(guide * guide) - mu * mu
    covariance = mean(guide * alpha) - mu * mp
    a = covariance / (variance + 0.001)
    refined = mean(a) * guide + mean(mp - a * mu)
    # Güvenli iç bölge opak kalır; yarı saydam gövde etkisi azalır.
    refined = np.clip((refined - 0.025) / 0.95, 0, 1)
    return refined


def add_contact_shadow(background, alpha, strength=0.14):
    """Kişinin kenarına hafif, yumuşak bir ortam gölgesi ekler."""
    if strength <= 0:
        return background
    height, width = alpha.shape
    shift_x = max(1, round(width * 0.004))
    shift_y = max(1, round(height * 0.008))
    transform = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
    shifted = cv2.warpAffine(alpha.astype(np.float32), transform, (width, height),
                             flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    sigma = max(1.5, min(width, height) * 0.012)
    shadow = cv2.GaussianBlur(shifted, (0, 0), sigmaX=sigma, sigmaY=sigma)
    # Gölge yalnızca kişinin dışına taşar; yüz ve kıyafet karartılmaz.
    shadow *= 1.0 - np.clip(alpha, 0, 1)
    shadow = np.clip(shadow * float(np.clip(strength, 0, 0.35)), 0, 0.18)
    return background * (1.0 - shadow[..., None])


def compose(photo, mask, background, strength=0.3, blur=0.0,
            shadow=0.14, branding=True):
    """Yüzü yeniden üretmeden doğal renk uyumu, gölge ve kenar işlemesi."""
    alpha = refine_mask(photo, mask)
    foreground = np.asarray(photo, dtype=np.float32)
    # Varsayılan olarak kaynak ayrıntıları korunur: yüz yumuşatma yok.
    bg = np.asarray(background.filter(ImageFilter.GaussianBlur(blur)) if blur > 0
                    else background, dtype=np.float32)
    # Fonun tüm ortalaması yerine kişinin hemen çevresindeki ortam ışığını örnekle.
    # Böylece karanlık bir sunucu rafı, tüm fotoğrafı mavi/koyu yapmaz.
    subject = (alpha > 0.04).astype(np.uint8)
    radius = max(9, min(65, round(min(photo.size) * 0.045)))
    kernel_size = radius * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (kernel_size, kernel_size))
    near = (cv2.dilate(subject, kernel) > 0) & (alpha < 0.04)
    if int(near.sum()) < 100:
        near = np.ones(alpha.shape, dtype=bool)
    local_bg = bg[near]
    # Sınırlı fotoğrafik ışık/renk uyumu: yüzü yeniden çizmez.
    # Arka planın aşırı koyu/açık olması kişiyi bozmasın diye kazanç sınırlı.
    solid_pixels = foreground[alpha > 0.97]
    if len(solid_pixels) > 100 and strength > 0:
        luma_weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        subject_luma = np.median(solid_pixels @ luma_weights)
        background_luma = np.median(local_bg @ luma_weights)
        exposure = np.clip((background_luma + 35) / (subject_luma + 35), 0.82, 1.18)
        foreground *= 1 + (exposure - 1) * strength
        # Ortamın renk eğilimini sınırlı aktar; cilt aşırı renklenmesin.
        tint = np.median(local_bg, axis=0)
        tint = np.clip(tint - tint.mean(), -15, 15)
        foreground = np.clip(foreground + tint * strength, 0, 255)
    # Belirsiz kenarda en yakın sağlam ön plan rengini kısmen kullan.
    # Bu, eski duvar renginin ince açık renkli çizgisini azaltmayı hedefler.
    solid = (alpha > 0.97).astype(np.float32)
    weights = cv2.GaussianBlur(solid, (0, 0), 2)
    nearest = cv2.GaussianBlur(foreground * solid[..., None], (0, 0), 2)
    nearest /= np.maximum(weights[..., None], 0.001)
    edge = ((alpha > 0.08) & (alpha < 0.95) & (weights > 0.1))
    foreground[edge] = foreground[edge] * 0.65 + nearest[edge] * 0.35
    bg = add_contact_shadow(bg, alpha, shadow)
    result = foreground * alpha[..., None] + bg * (1 - alpha[..., None])
    result = Image.fromarray(np.uint8(np.clip(result, 0, 255)))
    return brand(result) if branding else result


class Processor:
    def __init__(self, model=None):
        # Import ve model hazırlığı arayüzün işçi thread'inde gerçekleşir.
        from rembg import new_session, remove
        self.remove = remove
        config_path = ROOT / 'ayarlar.json'
        self.settings = json.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
        self.model = model or self.settings.get('model', 'u2net_human_seg')
        if self.model not in ('u2netp', 'u2net_human_seg'):
            raise ValueError('Model u2netp veya u2net_human_seg olmalı.')
        self.session = new_session(self.model, providers=['CPUExecutionProvider'])
        # İnsan modeli hareketli bir uzvu kaçırırsa genel maske koruma sağlar.
        self.safety_session = (new_session('u2netp', providers=['CPUExecutionProvider'])
                               if self.model == 'u2net_human_seg' else None)
        self.backgrounds = {}
        for title, key in BACKGROUNDS.items():
            with Image.open(ROOT / 'assets/backgrounds' / (key + '.png')) as source:
                self.backgrounds[title] = source.convert('RGB')
        self.last_photo = None
        self.last_mask = None
        # İlk gerçek müşteriden önce ONNX'in ilk hesaplamasını yaptır.
        self.remove(Image.new('RGB', SIZE, (120, 120, 120)), session=self.session, only_mask=True)
        if self.safety_session is not None:
            self.remove(Image.new('RGB', SIZE, (120, 120, 120)), session=self.safety_session, only_mask=True)

    def process(self, photo):
        start = time.perf_counter()
        photo = prepare_photo(photo)
        mask = self.remove(photo, session=self.session, only_mask=True)
        if self.safety_session is not None:
            safety = self.remove(photo, session=self.safety_session, only_mask=True)
            human = np.asarray(mask, dtype=np.float32) / 255
            general = np.asarray(safety, dtype=np.float32) / 255
            # Yüksek güvenli genel ön planı koru; düşük güvenli kenarları ekleme.
            protected = general * np.clip((general - 0.15) / 0.45, 0, 1)
            mask = Image.fromarray(np.uint8(np.maximum(human, protected) * 255))
        self.last_photo, self.last_mask = photo, mask
        return self.render(start)

    def render(self, start=None):
        """Önceki kişiyi tekrar kesmeden farklı fonla yeni dosya kaydet."""
        start = time.perf_counter() if start is None else start
        if self.last_photo is None:
            raise ValueError('Önce bir fotoğraf çekin veya seçin.')
        photo, mask = self.last_photo, self.last_mask
        title = self.settings.get('arka_plan', 'Bilgisayar - IT ofisi')
        if title not in self.backgrounds:
            title = 'Bilgisayar - IT ofisi'
        # Sadece fon doldurulur/kırpılır. Kişinin fotoğrafı asla kırpılmaz.
        # Dikey kadrajda mesleki ekipmanlar görünür kalsın diye fon odağı.
        focus_x = {'Makine - Fabrika': 0.20, 'Genetik - Laboratuvar': 0.25,
                   'Bilgisayar - IT ofisi': 0.05}.get(title, 0.5)
        background = ImageOps.fit(self.backgrounds[title], photo.size,
                                  Image.Resampling.LANCZOS, centering=(focus_x, 0.5))
        result = compose(photo, mask, background,
                         strength=float(np.clip(self.settings.get('renk_uyumu', 0.3), 0, 1)),
                         blur=float(np.clip(self.settings.get('arka_plan_bulanikligi', 0.0), 0, 8)),
                         shadow=float(np.clip(self.settings.get('ortam_golgesi', 0.14), 0, 0.35)),
                         branding=bool(self.settings.get('kulup_imzasi', True)))
        folder = ROOT / 'ciktilar'
        folder.mkdir(exist_ok=True)
        name = datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + uuid4().hex[:6] + '.jpg'
        path = folder / name
        # Yarım dosyanın sonuç diye görünmesini engelle.
        temp = path.with_suffix('.tmp')
        try:
            result.save(temp, format='JPEG', quality=96, subsampling=0)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
        return result, path, time.perf_counter() - start
