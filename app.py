from flask import Flask, request, send_file
import tabula
import pandas as pd
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import tempfile

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def upload_pdf():
    if request.method == "POST":
        pdf = request.files["pdf"]

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = os.path.join(tmp, "input.pdf")
            pdf.save(pdf_path)

            tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)
            df = pd.concat(tables)

            df = df.iloc[:, :2]
            df.columns = ["Name", "Number"]

            barcode_data = []
            for i, row in df.iterrows():
                barcode = Code128(str(row["Number"]), writer=ImageWriter())
                file = os.path.join(tmp, f"b{i}")
                barcode.save(file)
                barcode_data.append((row["Name"], row["Number"], f"{file}.png"))

            output_pdf = os.path.join(tmp, "output.pdf")
            c = canvas.Canvas(output_pdf, pagesize=letter)

            x_pos = [40, 310]
            y_pos = [500, 250]
            i = 0

            for name, number, img in barcode_data:
                x = x_pos[i % 2]
                y = y_pos[(i // 2) % 2]

                c.setFont("Helvetica-Bold", 11)
                c.drawString(x, y + 120, name)
                c.drawImage(img, x, y + 20, width=240, height=90)
                c.setFont("Helvetica", 10)
                c.drawString(x, y + 5, number)

                i += 1
                if i % 4 == 0:
                    c.showPage()

            c.save()
            return send_file(output_pdf, as_attachment=True)

    return '''
    <h2>Upload PDF → Download Barcode PDF</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="pdf" required>
        <br><br>
        <button type="submit">Convert</button>
    </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

