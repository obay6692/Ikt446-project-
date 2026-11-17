# ابدأ من هنا — IKT466 Oslo Bysykkel

هذا مشروع قابل للتشغيل، لكنه **ليس تقريرًا نهائيًا ولا يحتوي على نتائج تدريب حقيقية بعد**.

## 1) المطلوب منك: ملفات CSV

نزّل ستة أشهر من كل سنة: أبريل، مايو، يونيو، يوليو، أغسطس، سبتمبر للسنوات
2024 و2025 و2026 (18 ملفًا). المصدر الرسمي:
https://oslobysykkel.no/en/open-data/historical

ضعها بأسماء موحدة داخل `data/raw`، مثل:

- `data/raw/2024/04.csv`
- `data/raw/2024/05.csv`
- `data/raw/2025/04.csv`
- `data/raw/2026/09.csv`

إذا حمّلت ملفًا اسمه `04 (1).csv`، استورده باستخدام الأمر:

```powershell
python import_csv.py --year 2024 --month 4 --file "C:\Users\YOU\Downloads\04 (1).csv"
```

**ملف `10.csv` (أكتوبر 2026) الذي أرسلته سابقًا ليس ضمن التجارب الرئيسية:**
لا حاجة لإضافته في مجلد بيانات أبريل–سبتمبر.

## 2) افتح المشروع على VS Code

افتح المجلد الرئيسي وليس ملف Python وحده. ثبّت Python 3.10 أو أحدث.
في Terminal الخاص بـVS Code:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

في حالة منع PowerShell لتشغيل البيئة الافتراضية، استخدم مباشرة:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3) بعد وضع الملفات كلها

```powershell
python prepare_data.py
python run_experiments.py --phase validation
```

انظر إلى ملف `outputs/validation/metrics.csv`.
نتائجه تساعدنا على مناقشة الإعدادات والفرضيات قبل فتح نتائج الاختبار.

## 4) التقييم النهائي

بعد تثبيت قرارات النمذجة وعدم تغييرها حسب نتيجة الاختبار:

```powershell
python run_experiments.py --phase test
```

الملفات المهمة موجودة داخل `outputs/test/`:
نتائج MAE وRMSE وR²، نموذج Random Forest، نموذج MLP، منحنيات
التدريب، ورسوم التوقعات مقابل الأرقام الحقيقية.

## ماذا يتنبأ البرنامج؟

كم رحلة دراجة **تبدأ في أوسلو خلال ساعة محددة**؟
مثلاً: الساعة 08:00 يوم عمل.
البرنامج لا يتنبأ بسعر أو بمكان محطة محددة، بل بالمجموع على مستوى المدينة.

## التجربتان

1. مقارنة نموذج Random Forest ونموذج MLP مع كامل تدريب 2024.
2. مقارنة النماذج عند استخدام 25% و50% و100% من أيام تدريب 2024.

سنة 2025 لا تُستخدم لتدريب النماذج، بل للتحقق والتوقف المبكر، وسنة
2026 لا تُستخدم إلا للاختبار النهائي. البيانات الناقصة لا تُستبدل بنتائج وهمية.

## الانتباه للمراجع

نذكر مستودع GitHub الذي كان مرجعًا للفكرة وطريقة تنظيم العمل:
https://github.com/alvarogrojas/bike-sharing-demand-forecasting

ونذكر المصدر الرسمي للبيانات، واستخدام ChatGPT في كتابة الكود ومراجعته.
يجب أن تستطيع شرح الكود وتشغيله بنفسك، وأن تكون كل نتائج التقرير من تجاربك.

## رفع المشروع إلى حساب GitHub الخاص بك (اختياري)

بعد إنشاء Repository فارغ في حسابك، شغّل من المجلد الرئيسي:

```bash
git init
git add .
git commit -m "Initial Oslo Bysykkel IKT466 starter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/IKT466-Oslo-Bysykkel.git
git push -u origin main
```

استبدل `YOUR_USERNAME` باسم حسابك. لا ترفع ملفات CSV كبيرة إلا إذا قررت
ذلك بوعي، فملف `.gitignore` يستبعد البيانات والنتائج تلقائيًا.
