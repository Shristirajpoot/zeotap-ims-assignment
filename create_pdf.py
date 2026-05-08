from fpdf import FPDF
import datetime

class AssignmentPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Mission-Critical Incident Management System (IMS)', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Infrastructure / SRE Intern Assignment - Zeotap', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = AssignmentPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    content = [
        "Candidate Name: Shristi Rajpoot",
        f"Date: {datetime.date.today().strftime('%d %B %Y')}",
        "GitHub Repository: https://github.com/Shristirajpoot/zeotap-ims-assignment",
        "",
        "Overview: I have successfully built the highly resilient Incident Management System designed to ingest high volumes of signals (10k+/sec) using an asynchronous queue and debouncing mechanisms.",
        "",
        "Technical Stack:",
        "- Backend: Python 3.11, FastAPI, Asyncio (for high concurrency)",
        "- Storage: PostgreSQL (Source of Truth), MongoDB (Data Lake), Redis (Cache)",
        "- Frontend: React, Vite, TailwindCSS",
        "",
        "Key SRE & Resilience Features:",
        "1. Backpressure & Rate Limiting: Implemented `slowapi` to limit the /ingest endpoint to prevent cascading failures during spikes. An in-memory async queue buffers traffic and processes it in batches.",
        "2. Debouncing: Multiple signals for the same component within a short time frame are grouped into a single Work Item, while all raw logs are safely stored in MongoDB.",
        "3. Design Patterns: Utilized State Pattern for workflow lifecycle (enforcing Mandatory RCA) and Strategy Pattern for Alert Severity assignment.",
        "4. Observability: A background worker periodically logs /ingest throughput (signals/sec) to stdout.",
        "",
        "Running the Application: Please use `docker-compose up --build -d` to launch the stack. The React dashboard will be available at http://localhost:80. A `simulate_failure.py` script is included to generate high-volume outage signals."
    ]

    for item in content:
        pdf.multi_cell(190, 8, item)
            
    pdf.output("Shristi Rajpoot - Infrastructure SRE Intern Assignment.pdf", "F")
    print("PDF generated successfully.")

if __name__ == "__main__":
    create_pdf()
