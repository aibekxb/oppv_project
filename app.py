import re
import fitz  # PyMuPDF
from flask import Flask, render_template, request

app = Flask(__name__)

def extract_fio_smart(text):
    """Мәтіннен Аты-жөнін БЖЗҚ құжатының құрылымына сай дәл тауып алу функциясы"""
    if not text:
        return "Табылмады"
    
    # 1. Мәтінді таза жолдарға бөлеміз
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        # Егер жолдан ФИО немесе ТАӘ сөздері табылса
        if re.search(r'\b(ФИО|ТАӘ|Аты-жөні)\b', line, re.IGNORECASE):
            
            # А) Егер аты-жөні дәл осы жолда "ФИО" сөзінің жалғасында тұрса
            # Мысалы: "ФИО АХМЕТОВ АКЫЛБЕК..."
            fio_part = re.sub(r'.*?\b(ФИО|ТАӘ|Аты-жөні)\b', '', line, flags=re.IGNORECASE).strip()
            # Тек қазақ/орыс бас әріптері мен бос орындарды қалдырамыз
            fio_words = re.findall(r'[А-ЯӘІҢҒҮҰҚӨҺA-Z]+', fio_part)
            
            # Егер осы жолдан екі немесе одан көп сөз табылса (мысалы: АХМЕТОВ АКЫЛБЕК)
            if len(fio_words) >= 2:
                return " ".join(fio_words[:3])
            
            # Б) Егер "ФИО" сөзі жалғыз тұрса, аты-жөні келесі жолда деген сөз
            # Төмендегі 1-2 жолды тексереміз
            for j in range(i + 1, min(i + 3, len(lines))):
                next_line = lines[j]
                # Келесі жолдан тек қана толық бас әріппен жазылған сөздерді іздейміз
                next_words = re.findall(r'\b[А-ЯӘІҢҒҮҰҚӨҺA-Z]{2,}\b', next_line)
                
                # Егер ол жолда мағынасыз сөздер болса (мысалы: "Туған күні", "ЖСН"), оны өткізіп жібереміз
                if any(w in next_line.upper() for w in ["ТУҒАН", "ДАТА", "РОЖДЕНИЯ", "ИИН", "ЖСН"]):
                    continue
                    
                if len(next_words) >= 2:
                    return " ".join(next_words[:3])
                    
    return "Табылмады"

def analyze_pdf(pdf_file):
    try:
        # PDF-ті жадында оқу
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()

        # 1. Аты-жөнін жаңа смарт функциямен іздеу
        fio = extract_fio_smart(text)

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
