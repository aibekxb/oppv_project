import re
import fitz  # PyMuPDF
from flask import Flask, render_template, request

app = Flask(__name__)

def clean_fio(raw_text):
    """Аты-жөнін артық таңбалардан тазалау функциясы"""
    if not raw_text:
        return "Табылмады"
    
    # Тек бірінші жолды алу
    fio = raw_text.split('\n')[0].strip()
    
    # Егер басында ФИО немесе ТАӘ сөздері қалып қойса, оларды алып тастау
    fio = re.sub(r'^(ФИО|ТАӘ|Ф.И.О|Аты-жөні)\s*', '', fio, flags=re.IGNORECASE)
    
    # Артық таңбаларды тазалау
    fio = fio.strip()
    
    # Соңындағы жалғыз тұрған бас әріптерді (мысалы, " Т", " Ф") алып тастау
    fio = re.sub(r'\s+[А-ЯA-ZӘІҢҒҮҰҚӨҺ]$', '', fio)
    
    # Максимум 3 сөзді қалдыру (Тегі Аты Әкесінің аты)
    words = fio.split()
    if len(words) > 3:
        fio = " ".join(words[:3])
        
    return fio

def analyze_pdf(pdf_file):
    try:
        # PDF-ті жадында оқу
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()

        # 1. Аты-жөнін іздеу (БЖЗҚ құжаттарына арналған күшейтілген Regex)
        # "ФИО" сөзінен кейін кез келген бос орын немесе жол ауысуын ескереді
        fio_match = re.search(r"(?:ФИО|ТАӘ|Аты-жөні)\s*[:\-]?\s*([А-ЯA-ZӘІҢҒҮҰҚӨҺ\s\n]+)", text, re.IGNORECASE)
        
        raw_fio = fio_match.group(1) if fio_match else None
        fio = clean_fio(raw_fio)

        # 2. (МКЗЖ)/ жолдарын санау
        mkzj_matches = re.findall(r"\(МКЗЖ\)/", text)
        count = len(mkzj_matches)

        return fio, count

    except Exception as e:
        print(f"Қате: {e}")
        return "Файлды өңдеу қатесі", 0

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        if 'pdf' in request.files:
            pdf = request.files["pdf"]
            if pdf.filename != '':
                fio, count = analyze_pdf(pdf)
                result = {"fio": fio, "count": count}
    return render_template("index.html", result=result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
