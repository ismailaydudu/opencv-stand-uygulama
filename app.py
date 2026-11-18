"""IEEE Trakya standı: kamera -> fotoğraf -> yerel AI -> otomatik JPG.
Tüm Tkinter işlemleri ana thread'de; kamera ve AI ayrı thread'lerde.
"""
import argparse
import logging
import os
import json
from queue import Queue, Empty
from threading import Thread, Lock, Event
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageOps, ImageTk
from core import Processor, ROOT, BACKGROUNDS


class Camera:
    def __init__(self, index):
        self.index = index
        self.lock = Lock()
        self.stop = Event()
        self.frame = None
        self.stamp = 0
        self.error = 'Kamera açılıyor...'
        Thread(target=self.run, daemon=True).start()

    def run(self):
        # Kameranın sahibi tek thread: okuma / kapatma çakışmaz.
        cap = None
        try:
            backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            cap = cv2.VideoCapture(self.index, backend)
            if not cap.isOpened():
                raise RuntimeError('Kamera açılamadı. Kamera izinlerini ve numarasını kontrol edin.')
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            while not self.stop.is_set():
                ok, frame = cap.read()
                with self.lock:
                    if ok:
                        self.frame, self.stamp, self.error = frame, time.monotonic(), ''
                    else:
                        self.error = 'Kamera görüntüsü alınamıyor. Bağlantıyı kontrol edin.'
                if not ok:
                    self.stop.wait(0.1)
        except Exception as exc:
            with self.lock:
                self.error = str(exc)
            logging.exception('Kamera hatası')
        finally:
            if cap is not None:
                cap.release()

    def latest(self):
        with self.lock:
            # Kopmuş kameranın son karesini yeni fotoğraf olarak kullanma.
            if self.frame is None or time.monotonic() - self.stamp > 2:
                return None, self.error or 'Kameradan güncel görüntü bekleniyor.'
            return self.frame.copy(), self.error


class Booth:
    def __init__(self, root, index):
        self.root = root
        self.closed = False
        self.busy = False
        self.ready = False
        self.processor = None
        self.events = Queue()
        self.camera = Camera(index)
        self.result = None
        self.started = 0
        root.title('IEEE Trakya | Fotoğraf Standı v3.2')
        root.geometry('1180x820')
        root.minsize(900, 540)
        root.protocol('WM_DELETE_WINDOW', self.close)
        ttk.Label(root, text='IEEE TRAKYA • COMPUTER SOCIETY', font=('Arial', 20, 'bold')).pack(pady=12)
        panels = ttk.Frame(root)
        panels.pack(fill='both', expand=True, padx=12)
        panels.columnconfigure((0, 1), weight=1)
        panels.rowconfigure(1, weight=1)
        ttk.Label(panels, text='CANLI KAMERA').grid(row=0, column=0)
        ttk.Label(panels, text='SON KAYDEDİLEN FOTOĞRAF').grid(row=0, column=1)
        self.live = ttk.Label(panels, anchor='center')
        self.live.grid(row=1, column=0, sticky='nsew', padx=5)
        self.output = ttk.Label(panels, text='İlk fotoğraf burada görünecek.', anchor='center')
        self.output.grid(row=1, column=1, sticky='nsew', padx=5)
        self.status = tk.StringVar(value='Model hazırlanıyor. İlk kurulumda internet gerekir...')
        self.cam_status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, wraplength=1000).pack(pady=8)
        ttk.Label(root, textvariable=self.cam_status).pack()
        themes = ttk.Frame(root)
        themes.pack(pady=6)
        ttk.Label(themes, text='Arka plan:').pack(side='left', padx=8)
        self.theme = tk.StringVar(value='Bilgisayar - IT ofisi')
        self.theme_box = ttk.Combobox(themes, textvariable=self.theme,
                                    values=list(BACKGROUNDS), state='readonly', width=28)
        self.theme_box.pack(side='left', padx=6)
        self.signature = tk.BooleanVar(value=True)
        ttk.Checkbutton(themes, text='Kulüp imzası', variable=self.signature).pack(side='left', padx=8)
        self.apply = ttk.Button(themes, text='Son fotoğrafa uygula ve kaydet',
                                command=self.rerender, state='disabled')
        self.apply.pack(side='left', padx=8)
        options = ttk.Frame(root)
        options.pack(pady=5)
        ttk.Label(options, text='Arka plan yumuşaklığı').pack(side='left', padx=6)
        self.blur = tk.DoubleVar(value=0.0)
        ttk.Scale(options, from_=0, to=6, variable=self.blur, length=140).pack(side='left')
        ttk.Label(options, text='Kişi ışık / renk uyumu').pack(side='left', padx=6)
        self.color = tk.DoubleVar(value=0.35)
        ttk.Scale(options, from_=0, to=1, variable=self.color, length=140).pack(side='left')
        options2 = ttk.Frame(root)
        options2.pack(pady=3)
        ttk.Label(options2, text='Ortam gölgesi').pack(side='left', padx=6)
        self.shadow = tk.DoubleVar(value=0.14)
        ttk.Scale(options2, from_=0, to=0.30, variable=self.shadow, length=180).pack(side='left')
        ttk.Label(options2, text='Arka plan, ışık ve logo ayarları otomatik kaydedilir.').pack(side='left', padx=12)
        bar = ttk.Frame(root)
        bar.pack(pady=12)
        self.take = ttk.Button(bar, text='FOTOĞRAF ÇEK [Boşluk]', command=self.capture, state='disabled')
        self.take.pack(side='left', padx=6)
        self.file = ttk.Button(bar, text='Dosyadan fotoğraf seç', command=self.select, state='disabled')
        self.file.pack(side='left', padx=6)
        ttk.Button(bar, text='Çıktı klasörünü aç', command=self.open_folder).pack(side='left', padx=6)
        root.bind('<space>', self.on_space)
        Thread(target=self.prepare, daemon=True).start()
        self.tick()

    def prepare(self):
        try:
            self.events.put(('ready', Processor()))
        except Exception as exc:
            logging.exception('Model hazırlığı')
            self.events.put(('init_error', str(exc)))

    def show(self, label, image):
        width = max(320, label.winfo_width() - 12)
        height = max(180, label.winfo_height() - 12)
        preview = ImageOps.contain(image, (width, height))
        label.photo = ImageTk.PhotoImage(preview)
        label.configure(image=label.photo, text='')

    def tick(self):
        if self.closed:
            return
        frame, error = self.camera.latest()
        self.cam_status.set(error)
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Önizleme ile çıktı aynı: yazılar ters dönmesin diye aynalama yok.
            self.show(self.live, Image.fromarray(rgb))
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == 'ready':
                    self.processor = payload
                    self.blur.set(float(payload.settings.get('arka_plan_bulanikligi', 0)))
                    self.color.set(float(payload.settings.get('renk_uyumu', 0.35)))
                    self.shadow.set(float(payload.settings.get('ortam_golgesi', 0.14)))
                    self.theme.set(payload.settings.get('arka_plan') if payload.settings.get('arka_plan') in BACKGROUNDS else 'Bilgisayar - IT ofisi')
                    self.signature.set(bool(payload.settings.get('kulup_imzasi', True)))
                    self.ready = True
                    self.status.set(f'Hazır | Model: {self.processor.model} | Fotoğraf çek veya dosyadan seç.')
                elif kind == 'done':
                    self.busy = False
                    self.result, path, duration = payload
                    self.status.set(f'Kaydedildi: {path.name} | İşlem: {duration:.2f} saniye')
                elif kind in ('error', 'init_error'):
                    self.busy = False
                    self.status.set('İşlem başarısız. Ayrıntı: hatalar.log')
                    messagebox.showerror('İşlem tamamlanamadı', payload + '\n\nModel hatasıysa internet açıkken 1_KUR.bat dosyasını tekrar çalıştırın.')
        except Empty:
            pass
        if self.result is not None:
            self.show(self.output, self.result)
        if self.busy:
            self.status.set(f'Fotoğraf işleniyor... {time.perf_counter() - self.started:.1f} sn')
        self.take.configure(state='normal' if self.ready and not self.busy and frame is not None else 'disabled')
        self.file.configure(state='normal' if self.ready and not self.busy else 'disabled')
        self.apply.configure(state='normal' if self.ready and not self.busy and self.result is not None else 'disabled')
        self.root.after(60, self.tick)

    def on_space(self, event):
        self.capture()
        return 'break'  # Düğmenin varsayılan Space işlemiyle çift çekim olmasın.

    def capture(self):
        if not self.ready or self.busy:
            return
        frame, error = self.camera.latest()
        if frame is None:
            self.status.set(error)
            return
        self.submit(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))

    def select(self):
        if not self.ready or self.busy:
            return
        path = filedialog.askopenfilename(filetypes=[('Fotoğraf', '*.jpg *.jpeg *.png *.webp')])
        if path:
            self.submit(path)

    def rerender(self):
        if self.ready and not self.busy and self.result is not None:
            self.submit(None)

    def submit(self, photo):
        self.processor.settings['arka_plan'] = self.theme.get()
        self.processor.settings['kulup_imzasi'] = self.signature.get()
        self.processor.settings['arka_plan_bulanikligi'] = self.blur.get()
        self.processor.settings['renk_uyumu'] = self.color.get()
        self.processor.settings['ortam_golgesi'] = self.shadow.get()
        self.save_settings()
        self.busy = True  # Thread başlamadan kilitle: art arda tıklama kuyruk yaratmaz.
        self.started = time.perf_counter()
        self.take.configure(state='disabled')
        self.file.configure(state='disabled')
        Thread(target=self.process, args=(photo,), daemon=True).start()

    def save_settings(self):
        """Kullanıcının seçtiği görünüm uygulama yeniden açılınca da kalsın."""
        path = ROOT / 'ayarlar.json'
        temp = path.with_suffix('.json.tmp')
        try:
            temp.write_text(json.dumps(self.processor.settings, ensure_ascii=False,
                                       indent=2), encoding='utf-8')
            temp.replace(path)
        except OSError:
            logging.exception('Ayarlar kaydedilemedi')
            temp.unlink(missing_ok=True)

    def process(self, photo):
        try:
            if isinstance(photo, str):
                with Image.open(photo) as source:
                    photo = ImageOps.exif_transpose(source).convert('RGB')
            self.events.put(('done', self.processor.render() if photo is None else self.processor.process(photo)))
        except Exception as exc:
            logging.exception('Fotoğraf işlenemedi')
            self.events.put(('error', str(exc)))

    def open_folder(self):
        folder = ROOT / 'ciktilar'
        folder.mkdir(exist_ok=True)
        if os.name == 'nt':
            os.startfile(str(folder))
        else:
            messagebox.showinfo('Çıktılar', str(folder))

    def close(self):
        if self.busy:
            messagebox.showinfo('Fotoğraf işleniyor', 'Kaydın tamamlanmasını bekleyin, ardından kapatın.')
            return
        self.closed = True
        self.camera.stop.set()
        self.root.destroy()


if __name__ == '__main__':
    logging.basicConfig(filename=ROOT / 'hatalar.log', level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', type=int, default=0)
    args = parser.parse_args()
    root = tk.Tk()
    Booth(root, args.camera)
    root.mainloop()
