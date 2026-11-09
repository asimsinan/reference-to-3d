[English](README.md) | **Türkçe**

# reference-to-3d — bir Claude Code skill'i

Resimlerden Blender'da **resmin birebir aynısı** görünen 3B modeller üretir.

Bu skill, Claude'un göz kararı "benzer bir şey" modellemesi yerine resmin kendisini kullanmasını sağlar: biçim için
resmin çizgilerini, yüzey için piksellerini, sonucu kontrol etmek için de izlenimleri değil sayıları.

| Siz verirsiniz | Siz alırsınız |
|---|---|
| Bir turnaround sayfası ya da ayrı ön / yan / arka / üst görünümler (fotoğraf veya konsept çizim) | Çizgilere oturtulmuş, görünümlerin kendi pikselleriyle kaplanmış bir model |
| Tek bir yerden görülen bir iç mekân resmi (araç kokpiti, oyun kamerası) | O yerden piksel piksel aynı görünen bir iç mekân |
| Bir odanın tek fotoğrafı ya da render'ı | İçinde **dolaşılabilen** bir oda: kamera fotoğraftan çözülür, eşyalar 3B olur, görünmeyen taraflar fotoğrafın tekrar eden parçalarından kurulur |
| Gerçek bir odanın farklı yerlerden çekilmiş birkaç sıradan telefon fotoğrafı (bir ofis, bir daire) | Odanın tamamı ve bütün kameralar birlikte çözülür; dışarıdaki koridor, açılıp kapanan kapı, her nesne kendi fotoğrafından modellenir (raftaki gibi yaslanan kitaplar, çevirmeli telefon, yazıcı) ve tek HTML dosyasında gezinme görüntüleyicisi |
| Boyutları bilinen bir ürünün sıradan bir fotoğrafı (dizüstü bilgisayar, telefon, sandalye) | Gerçek ölçülerinde kurulmuş ürün; fotoğraf her yüzeye düzeltilerek yerleştirilir |
| Dönel bir nesnenin tek fotoğrafı (tencere, şişe, vazo, kupa) | Eksen etrafında döndürülmüş profil, katı parçalar olarak yan saplar, bir kabın içi, her yanı saran fotoğraf, ardından fotoğrafın ışığı yerine gerçek malzemeler (çelik, plastik, porselen) |
| Boyutunu bilmediğiniz bir ürünün önden ve yandan iki sıradan fotoğrafı (masa telefonu, yazıcı, su ısıtıcı) | İki kamera ve tek gövde fotoğrafların kenarlarından birlikte çözülür, her parça bir fotoğrafın gösterdiğinden biçimlenir (ahizenin kavisi, kademeler, kablonun çıktığı yer), ardından fotoğrafların baskıları korunarak gerçek malzemeler |
| İçinde eşya olan bir kabın tek fotoğrafı (kalemli ve makaslı bir kalemlik, sepet, kavanoz) | Yukarıdaki gibi kap, fotoğraftan yerleştirilip tabanına oturtulmuş içindekiler, içinden görülen tel kafes duvar, kafesin arkasındakiler fotoğrafın teller arasında gösterdiğiyle kaplanmış |
| Üstünde eşyalar olan bir mobilya takımının, odasıyla birlikte tek ürün fotoğrafı (masa, bank, tabureler, bardaklar, tabak, mumlar, bitki) | Her parça fotoğrafa oturtulur (oturaklar minderlerinin silüetine, açılı ayaklar, her nesne durduğu yerde ve neyin üstünde duruyorsa onun üstünde), malzemeler fotoğrafın kendi piksellerinden alınır, çevresindeki oda kurulur ve ışık fotoğrafın renklerine olduğu kadar kontrastına da oturtulur |

![Bir ofis ve koridoru: üst sırada telefon fotoğrafları, alt sırada her fotoğrafın çözülen kamerasından model](docs/showcase/office-room.jpg)

*Üstte on beş telefon fotoğrafından altısı (EXIF yok, 1x ve 0.5x lensler): koridor, koridordan kapı, pencereden ve
kapıdan oda, kitaplık, yazıcı. Altta aynı çözülen kameralardan model (Blender, Cycles). Tek parametrik oda
(2,55 × 5,38 × 2,81 m) ve bütün kameralar, elle okunan köşelerden ve birden çok fotoğrafta görünen eşyalardan birlikte
çözüldü; koridor, menteşesinde dönen kapı kanadı, her kitabı ayrı ve yaslanan bir hacim olan kitaplık, çevirmeli
telefon, masa telefonu, dizüstü ve yazıcı kendi fotoğraflarından modellendi; hepsi tarayıcıda gezilebiliyor (WASD,
kapı E ile açılıyor). Kullanıcının beş tur boyunca yaptığı düzeltmeler `references/multi-photo-room.md` içinde. Nasıl:
[`examples/office-room-multiphoto/`](examples/office-room-multiphoto/).*

![Kablolu bir masa telefonu: önden ve yandan referans fotoğraflar, ardından ön fotoğrafın kamerasından, çaprazdan, arkadan ve üstten model](docs/showcase/desk-phone.jpg)

*Üstte soldaki ikisi referans: krem rengi bir masa telefonunun önden ve ahize tarafından iki telefon fotoğrafı; ölçü
yok, EXIF yok. Gerisi model, gerçek malzemelerle (fotoğrafın baskıları korunmuş krem ABS, yazılarıyla parlak siyah
tuşlar; Blender, Cycles): ön fotoğrafın kamerasından, sonra iki fotoğrafın da göstermediği taraflardan. İki kamera ve
tek gövde, fotoğrafların düz kenarlarından ve iki fotoğrafta da görünen tuşlardan birlikte çözüldü (yan fotoğraf,
tek ön fotoğrafın çözemediğini düzeltti: 16/47 mm'lik bir kama değil, 23/31 mm'lik bir gövde); ahizenin kavisi,
gövdenin kademesi ve kablonun çıkışı yan fotoğraftan okundu. Ön fotoğrafın kamerasından fotoğraf dokulu sürüm
6.7/255 (medyan 0.3) farkla örtüşüyor; gerçek malzemeli sürümün ön yüzü %1 içinde. Nasıl:
[`examples/desk-phone-two-photos/`](examples/desk-phone-two-photos/).*

![Şeffaf bir kolonya spreyi: referans telefon fotoğrafı, ardından aynı kameradan, çaprazdan, arkadan ve üstten model](docs/showcase/cologne-bottle.jpg)

*Solda referans: masadaki 100 ml'lik bir kolonya spreyinin tek telefon fotoğrafı. Gerisi model, gerçek malzemelerle
(içinde sıvısıyla şeffaf PET, üzerine basılı kâğıt etiket, siyah tırtıklı bilezik, füme kapak; Blender, Cycles):
fotoğrafın kamerasından, sonra fotoğrafın hiç göstermediği yanlardan. Kamera gövdenin düz kenarlarından ve bilezik,
omuz ve taban çemberlerinden çözüldü (fotoğrafın, yere paralel bir kameradan kırpılmış olduğu ortaya çıktı), etiket
silindire açılıp fotoğrafın gölgesi arındırıldı, yamuk takılı püskürtücü başlık düzeltildi; fotoğrafın kamerasından
fotoğraf dokulu sürüm 0,966 (IoU) ve 2,3/255 ile, gerçek malzemeli sürümün etiketi, kapağı ve bileziği fotoğrafa 5
seviye içinde uyuyor. Nasıl yapıldığı: [`examples/cologne-bottle-revolved/`](examples/cologne-bottle-revolved/).*

![El boyaması damalı bir vazo: referans ürün fotoğrafı, ardından aynı kameradan, çaprazdan, arkadan ve üstten model](docs/showcase/vase.jpg)

*Solda referans: altın ağızlı ve altın bantlı, el boyaması damalı porselen bir vazonun, kırmızı çiçeklerin önünde
ayna tepsi üzerindeki 600 x 900'lük tek ürün fotoğrafı. Gerisi model, gerçek malzemelerle (sırlı porselen, metal
olarak altın yaldız; Blender, Cycles): fotoğrafın kamerasından, sonra fotoğrafın hiç göstermediği yanlardan. Kamera
ağızdan, altın banttan ve ayaktan birlikte çözüldü; vazonun üzerine açılan fotoğrafta on düz kare sütunu çıktı ve
desen bunlardan, fotoğrafın ışığı ve yansımaları olmadan çepeçevre yeniden kuruldu. Fotoğrafın kamerasından silüet
0,988 (IoU), fotoğraf dokulu gövde 1,0/255 ile örtüşüyor; kullanıcının iki düzeltmesi (dar kalan ağız, soluk renkler)
örneğin README'sinde. Nasıl yapıldığı: [`examples/vase-checker-revolved/`](examples/vase-checker-revolved/).*

![Bir yemek takımı: referans ürün fotoğrafı, ardından aynı kameradan, çaprazdan, bank tarafından ve arkadan model](docs/showcase/dining-set.jpg)

*Solda referans: açılır tablalı meşe bir yemek masasının, bir bank ve iki taburesiyle, altlıklar üstünde iki bardak,
iki muffinli ahşap bir kâse, küre bir mum, silindir bir mum ve küçük bir bitkiyle, tül perdeli pencereli bir odadaki
1000 x 1000'lik tek ürün fotoğrafı. Gerisi model (Blender, Cycles): fotoğrafın kamerasından, sonra fotoğrafın hiç
göstermediği yanlardan. Kamera, masa tablasının kenarlarından ve ayakların tabanlarından, terazide ve optik merkezi
kaydırılmış olarak (düzeltilmiş bir ürün çekimi) çözüldü; her oturak minderinin silüetine oturtuldu, her nesne masaya
değdiği yerden ve neyin üstünde durduğuyla yerleştirildi. Bütün malzemeler fotoğrafın kendi piksellerinden geliyor
(meşenin paleti, damar aralığı ve kontrastı etek tahtalarından, ayaklar açılarak, kumaş minderlerden), oda
fotoğraftan kuruldu ve ışık fotoğrafın renklerine olduğu kadar kontrastına da oturtuldu: bölgeler 10/255 içinde,
mobilyanın kontrastı fotoğrafın 49'una karşı 40 (önce 25). Kullanıcının düzeltmeleri ve bunlardan çıkan kural
(malzeme yalnızca referanstan, fark kalmayana kadar karşılaştır) `references/single-photo-scene.md` içinde. Nasıl
yapıldığı: [`examples/dining-set-single-photo/`](examples/dining-set-single-photo/).*

![Kalemleri, makası, kaşığı ve yapıştırıcısıyla tel kafes bir kalemlik: referans telefon fotoğrafı, ardından aynı kameradan, sağdan, arkadan ve üstten model](docs/showcase/pen-holder.jpg)

*Solda referans: masadaki tel kafes bir kalemliğin tek telefon fotoğrafı. Gerisi model, gerçek malzemelerle (siyah
boyalı tel, çelik, kalemlerin kendi baskıları; Blender, Cycles): önce fotoğrafın kamerasından, sonra fotoğrafın hiç
göstermediği yanlardan. Kamera ağız ve taban çemberleriyle duvar kenarlarından çözüldü, kafesin göz aralığı
silindire açılmış fotoğraftan ölçüldü, her eşya ayağının tabana değdiği yere yerleştirildi; fotoğrafın kamerasından
bakınca kalemliğin dış çizgisi 0,988 (IoU), ağız üstündeki kalemler 3,7/255 farkla örtüşüyor. Nasıl yapıldığı:
[`examples/pen-holder-mesh/`](examples/pen-holder-mesh/).*

![Bir kupa: referans telefon fotoğrafı, ardından aynı kameradan, arkadan, kulp tarafından ve üstten model](docs/showcase/mug.jpg)

*Solda referans: masadaki bir kupanın sıradan bir telefon fotoğrafı. Gerisi model, gerçek porselen olarak (Blender,
Cycles): önce fotoğrafın kendi kamerasından, sonra fotoğrafın hiç göstermediği yanlardan. Kamera ağzın ve tabanın
dış çizgilerinden çözüldü, profil eksen etrafında döndürüldü, kulp kendi dış çizgisi boyunca süpürüldü; fotoğrafın
kamerasından bakınca dış çizgi 0,982 (IoU), fotoğraf dokulu sürümün renkleri 1,4/255 farkla örtüşüyor. Nasıl
yapıldığı: [`examples/mug-revolved/`](examples/mug-revolved/).*

![Bir düdüklü tencere: referans ürün fotoğrafı, ardından cilalı çelik model üç yandan](docs/showcase/pressure-cooker.jpg)

*Solda referans: yandan çekilmiş tek bir ürün fotoğrafı. Gerisi model: eksen etrafında döndürülmüş profil, katı
parçalar olarak saplar, sonra gerçek cilalı çelik ve plastik (Blender, Cycles). Üstten ve arkadan görünümler
fotoğrafta yok. Nasıl yapıldığı:
[`examples/pressure-cooker-revolved/`](examples/pressure-cooker-revolved/).*

Sonuç **.blend** dosyası olarak kaydedilir (dokular dosyanın içinde). İsterseniz oyun motorları (Unity, Unreal,
Godot, three.js) için **glTF/GLB** olarak da dışa aktarılır; tekerlek ve kapı gibi hareketli parçalar ayrı mesh olur.

---

## 1. Gerekenler

| | |
|---|---|
| **Claude Code** | Terminal, masaüstü uygulaması ya da IDE eklentisi — [claude.com/claude-code](https://claude.com/claude-code) |
| **Blender** | 4.2 veya üstü (5.2 ile denendi) — [blender.org](https://www.blender.org/download/) |
| **uv** | Python betiklerini çalıştırır ve gereken paketleri (numpy, OpenCV…) kendisi kurar — [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |

uv'yi tek satırla kurun:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows'ta (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Python paketlerini sizin kurmanız **gerekmez**; her betik kendi paketlerini belirtir, uv onları indirir.

## 2. Skill'i Claude Code'a yükleme

Skill, içinde bir `SKILL.md` dosyası bulunan bir klasörden ibarettir. Claude Code skill'leri iki yerde arar:

| Nereye | Nerede kullanılır | Ne zaman seçilir |
|---|---|---|
| `~/.claude/skills/reference-to-3d/` | **tüm** projelerinizde | her yerde kullanmak istiyorsanız (önerilen) |
| `<projeniz>/.claude/skills/reference-to-3d/` | yalnızca o projede | projenin deposu üzerinden ekiple paylaşmak istiyorsanız |

### Yol A — git ile (önerilen)

macOS / Linux:

```bash
git clone https://github.com/asimsinan/reference-to-3d.git ~/.claude/skills/reference-to-3d
```

Windows (PowerShell):

```powershell
git clone https://github.com/asimsinan/reference-to-3d.git "$env:USERPROFILE\.claude\skills\reference-to-3d"
```

### Yol B — git olmadan

1. GitHub'da **Code → Download ZIP**'e tıklayın.
2. ZIP'i açın.
3. Klasörün adını `reference-to-3d` yapın ve `~/.claude/skills/` içine taşıyın (Windows: `%USERPROFILE%\.claude\skills\`).

Hangi yolu seçerseniz seçin, sonuçta dosya şurada olmalı: `~/.claude/skills/reference-to-3d/SKILL.md`. `SKILL.md`
doğrudan bu klasörün içinde olmalı, bir klasör daha derinde değil.

### Yüklendiğini kontrol edin

**Yeni** bir Claude Code oturumu açın (skill'ler açılışta okunur) ve `/` yazın; listede `reference-to-3d` görünmeli.
Claude'a *"Hangi skill'lerin var?"* diye de sorabilirsiniz.

### Blender'ın yerini söyleyin (yalnızca varsayılan yerde değilse)

Skill, macOS'ta Blender'ı `/Applications/Blender.app` içinde bekler. Linux'ta (`blender` komutu PATH'te), Windows'ta
ya da Blender başka bir yerdeyse, sohbette bir kez söylemeniz yeter. Ya da projenizin `CLAUDE.md` dosyasına bir satır
ekleyin, örneğin:

```
Blender is at C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
```

## 3. Kullanım

1. Resim(ler)i proje klasörünüze koyun ya da Claude Code sohbetine yapıştırın/sürükleyin.
2. Ne istediğinizi söyleyin. İki yolu var:
   - **Komutla:** `/reference-to-3d resimdeki odayı modelle`
   - **Ya da doğal bir dille isteyin.** İstek uyuyorsa Claude skill'i kendisi yükler, örneğin:
     - *"Bu dört görünümden aracın 3B modelini yap."*
     - *"Resimdeki odayı modelle, içinde dolaşabilmek istiyorum."*
     - *"Fotoğraftaki dizüstü bilgisayarı 3B yap, MacBook Pro 14."*
     - *"Ekteki resimdeki düdüklü tencereyi 3B modelle."*
     - *"Kalemliği içindekilerle 3B modelle."*
     - *"Fotoğraftaki kolonyayı 3B modelle."*
     - *"Bu masa telefonunu modelle, biri önden biri yandan iki fotoğraf."*
     - *"Ekteki bardağı 3d modelle, sonra gerçek porselen yap."*
     - *"Unity için GLB olarak dışa aktar, tekerlekler ayrı parça olsun."*

### Claude ne yapar?

1. **Resmi okur**: görünümleri adlandırır, kamerayı çözer, gerçek bir ölçü arar (size sorabilir, örneğin "kapı kaç metre?").
2. **Biçimi kurar**: çizgilere oturtarak ya da çözülen kamera üzerinden ölçerek.
3. **Resmin kendi piksellerini modelin üzerine yerleştirir.**
4. Sonucu görünüm görünüm resimle **ölçer** (çizgi örtüşmesi ve renk farkı, sayıyla) ve size **yan yana bir
   karşılaştırma** gösterir (solda resim, sağda model).
5. Gösterdiğiniz farkları her seferinde bir görünüm üzerinden **düzeltir**.
6. `.blend` dosyasını **kaydeder** (bakılmaya hazır açılır); isterseniz GLB de verir.

### İyi sonuç için ipuçları

- Biliyorsanız **gerçek bir ölçü verin** (kapı 2.0 m, minibüs 1.9 m yüksekliğinde). Geri kalan her şey ondan çıkar.
- **Modelin nerede kullanılacağını söyleyin**: tek bir render, oyun motoru, ya da içinde dolaşmak.
- **Karşılaştırma görüntülerine bakın ve neyin farklı olduğunu söyleyin**; "benzer"den "birebir"e böyle gidilir.
- **Görüntü üretme kredisi** (hiçbir resmin göstermediği tarafları doldurmak için) yalnızca siz onaylarsanız harcanır.
  Önce her zaman ücretsiz yol önerilir: o tarafları resmin kendi tekrar eden parçalarından kurmak.

### Akılda tutulacak sınırlar

- Resmin ışığı ve yansımaları dokuya işlenir; sahnenizin ışıklarıyla değişmez.
- Hiçbir resmin göstermediği yüzeyler gerçeğin kendisi değil, makul tahminlerdir; Claude bunların hangileri olduğunu söyler.
- Bir odanın tek resminden yapılan model, o resmin kamerasından birebirdir. İçinde dolaşınca yakından bakıldığında
  tekrar eden parçalar fark edilir (aynı pencere bölmesi, aynı makine).

## 4. İçinde ne var?

```
reference-to-3d/
├── SKILL.md                     Claude'un izlediği talimatlar (nasıl çalıştığını okumak isterseniz buradan başlayın)
├── scripts/                     Claude'un çalıştırdığı araçlar (her birinin kullanımı kendi başlığında)
│   ├── split_sheet.py           turnaround sayfası → adlandırılmış görünümler ve maskeler
│   ├── hull.py, loft.py         çizgilerden biçim (her nesne / uzun nesneler)
│   ├── textures.py, project.py  görünümlerin piksellerini modele yerleştirir; render, .blend, GLB (Blender)
│   ├── compare.py               görünüm başına çizgi örtüşmesi ve renk farkı, karşılaştırma görüntüleri
│   ├── solve_camera_vp.py       bir oda fotoğrafının kamerasını çizgilerinden çözer (odak, eğim, ölçek)
│   ├── rectify_plane.py         odanın bir duvarını/zeminini fotoğraftan düz görünecek şekilde çıkarır
│   └── shot_ui.py               .blend dosyasını açıldığı haliyle ekran görüntüsüne alır
├── docs/showcase/               bu README'deki görseller
├── references/                  Claude'un gerektiğinde okuduğu ayrıntılı rehberler
│   ├── single-view-interior.md  tek resimden iç mekân; dolaşılabilir odalar
│   ├── single-photo-object.md   boyutu bilinen bir ürünün tek fotoğrafı
│   ├── single-photo-revolved.md dönel bir nesnenin tek fotoğrafı (tencere, şişe, vazo, kupa)
│   ├── single-photo-container.md içinde eşya olan bir kabın tek fotoğrafı (kalemlik); içinden görülen kafes duvarlar
│   ├── two-photo-object.md      boyutu bilinmeyen bir ürünün önden ve yandan iki fotoğrafı (masa telefonu)
│   ├── multi-photo-room.md      birçok telefon fotoğrafından gerçek bir oda; koridor ve kapıyla gezilebilir
│   ├── single-photo-scene.md    üstünde eşyalar olan bir mobilya takımı ve odası, tek ürün fotoğrafından
│   ├── game-export.md           oyun motorları için adlar, pivotlar ve ayarlar
│   └── pitfalls.md              daha önce neyin, neden yanlış gittiği
└── examples/                    betikleriyle birlikte on eksiksiz örnek
    ├── laptop-single-photo/     tek fotoğraftan bir dizüstü bilgisayar
    ├── pressure-cooker-revolved/ tek ürün fotoğrafından bir düdüklü tencere
    ├── mug-revolved/            tek telefon fotoğrafından porselen bir kupa
    ├── cologne-bottle-revolved/ tek kırpılmış telefon fotoğrafından şeffaf bir kolonya spreyi
    ├── vase-checker-revolved/   tek ürün fotoğrafından el boyaması damalı bir vazo
    ├── dining-set-single-photo/ tek ürün fotoğrafından masa üstü eşyalarıyla bir yemek takımı ve odası
    ├── pen-holder-mesh/         tek telefon fotoğrafından içindekileriyle tel kafes bir kalemlik
    ├── desk-phone-two-photos/   önden ve yandan iki telefon fotoğrafından kablolu bir masa telefonu
    ├── office-room-multiphoto/  on beş telefon fotoğrafından gezilebilir bir ofis ve koridor
    └── laundromat-room/         tek render'dan dolaşılabilir bir çamaşırhane
```

`scripts/` ya da `examples/` içindeki hiçbir şeyi sizin çalıştırmanız gerekmez; bunları Claude çalıştırır. İsterseniz
her örneğin `README.md` dosyası komutlarını sırasıyla listeler.

## 5. Güncelleme

git ile kurduysanız:

```bash
cd ~/.claude/skills/reference-to-3d && git pull
```

Ardından yeni bir Claude Code oturumu açın.

## 6. Sorun giderme

| Sorun | Çözüm |
|---|---|
| `/reference-to-3d` listede görünmüyor | `SKILL.md` dosyasının `~/.claude/skills/reference-to-3d/SKILL.md` yolunda olduğunu kontrol edin, sonra yeni bir oturum açın. |
| "Blender bulunamadı" | Claude'a Blender'ın tam yolunu söyleyin (2. bölüm). |
| `uv: command not found` | uv'yi kurun (1. bölüm) ve yeni bir terminal açın. |
| İlk çalıştırma yavaş | uv paketleri (OpenCV, numpy) bir kez indiriyor; sonraki çalıştırmalar hızlıdır. |
| .blend dosyası gri açılıyor | 3B görünümün sağ üstündeki üçüncü küre simgesine, yani **Material Preview**'a geçin. |
