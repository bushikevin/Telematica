from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import io

app = Flask(__name__)
risultati = []


def estrai_link(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = [urljoin(url, a.get("href")) for a in soup.find_all("a", href=True)]
        return links
    except Exception:
        return []


def valida_url(url):
    try:
        r = requests.get(url, timeout=5, allow_redirects=True)
        if r.status_code == 200:
            return "OK (200)" if not r.history else "OK (con redirezione)"
        elif r.status_code == 401:
            return "Privato (401)"
        elif r.status_code == 403:
            return "Accesso negato (403)"
        elif r.status_code == 404:
            return "Non trovato (404)"
        else:
            return f"Errore HTTP {r.status_code}"
    except requests.exceptions.ConnectionError:
        return "Connessione rifiutata"
    except requests.exceptions.Timeout:
        return "Timeout"
    except Exception as e:
        return f"Errore: {e}"


@app.route("/", methods=["GET", "POST"])
def index():
    global risultati
    risultati = []

    if request.method == "POST":
        urls_input = request.form["urls"]
        urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

        for url in urls:
            links = estrai_link(url)
            for link in links:
                stato = valida_url(link) if link.startswith(("http://", "https://")) else "Non valido"
                risultati.append((url, link, stato))

        return render_template("index.html", risultati=risultati)

    return render_template("index.html", risultati=None)


@app.route("/download/<tipo>")
def download(tipo):
    df = pd.DataFrame(risultati, columns=["Pagina di partenza", "URL", "Stato"])
    if tipo == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode()),
                         mimetype="text/csv",
                         as_attachment=True,
                         download_name="report.csv")
    elif tipo == "html":
        buf = io.StringIO()
        df.to_html(buf, index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode()),
                         mimetype="text/html",
                         as_attachment=True,
                         download_name="report.html")


if __name__ == "__main__":
    app.run(debug=True)
