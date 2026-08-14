# AI CV Screening PoC

Sistem penyaringan CV berbasis AI yang dibuat sebagai **Proof of Concept (PoC)** untuk membantu proses seleksi kandidat berdasarkan kesesuaian antara CV dengan kebutuhan suatu posisi pekerjaan.

Sistem melakukan ekstraksi informasi dari CV, mencocokkan kualifikasi kandidat dengan Job Description, menghitung skor kesesuaian, dan memberikan rekomendasi kandidat.

> Project ini berfungsi sebagai alat bantu screening awal. Keputusan akhir tetap dilakukan oleh recruiter atau hiring team.

---

## Tujuan Project

Project ini dibuat untuk:

- Mengotomatisasi proses screening CV awal.
- Mengurangi proses perbandingan CV dengan Job Description secara manual.
- Mengidentifikasi kandidat yang memenuhi requirement.
- Menampilkan requirement yang terpenuhi dan belum terpenuhi.
- Memberikan ranking kandidat berdasarkan skor.
- Menghasilkan hasil screening dalam format JSON.

---

## ⚙️ Fitur Utama

- Ekstraksi teks dari CV PDF, DOCX, dan TXT.
- Ekstraksi nama kandidat.
- Ekstraksi skill.
- Ekstraksi pendidikan dan bidang pendidikan.
- Estimasi pengalaman kerja.
- Normalisasi skill dan variasi penulisan.
- Pencocokan required skills.
- Pencocokan preferred skills.
- Semantic similarity antara CV dan Job Description.
- Weighted scoring.
- Rekomendasi kandidat.
- Export hasil ke JSON.

---

## Teknologi
Python
PyMuPDF
Sentence Transformers
Scikit-learn
Regex
JSON

---

##  Model AI/ML

Project ini menggunakan pendekatan **hybrid matching**, yaitu menggabungkan pencocokan berbasis rule/keyword dengan semantic similarity.

### 1. Sentence Transformer

Untuk semantic similarity, sistem menggunakan model:
Text **all-MiniLM-L6-v2**

## Status

Proof of Concept (PoC)

Sistem saat ini berfokus pada proses screening dan ranking CV menggunakan data CV yang tersedia pada folder: **data/sample_cvs/**

---

# Panduan Menjalankan Sistem Screening CV

## 1. Persiapan Lingkungan

Sebelum menjalankan sistem, pastikan Anda berada di direktori proyek yang benar.

### Membuat Virtual Environment

Buka terminal Anda dan jalankan perintah berikut:

```bash
python -m venv .venv

```

### Aktivasi Virtual Environment

Sesuaikan dengan sistem operasi yang Anda gunakan:

* **Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1

```


* **macOS / Linux:**
```bash
source .venv/bin/activate

```

### Install Dependency

Instal semua pustaka yang diperlukan:

```bash
pip install -r requirements.txt

```

---

## 2. Menjalankan Screening

Gunakan perintah berikut untuk memulai proses screening CV berdasarkan *Job Description* (JD) yang telah disediakan:

```bash
python screen_cv.py --jd data/job_description.txt --cv-dir data/sample_cvs

```

**Keterangan Argumen:**

* `--jd`: Path menuju file teks deskripsi pekerjaan.
* `--cv-dir`: Direktori yang berisi file-file CV kandidat.

---

## 3. Hasil Output

Hasil proses screening akan disimpan secara otomatis dalam file **`results.json`**.

Berikut adalah contoh format data yang dihasilkan oleh sistem:

```json
{
    "candidate": "Bayu",
    "overall_score": 92.22,
    "recommendation": "SHORTLIST",
    "mandatory_requirements_met": true
}

```

### Penjelasan Field:

| Field | Deskripsi |
| --- | --- |
| `candidate` | Nama kandidat yang di-*screening*. |
| `overall_score` | Skor kecocokan kandidat terhadap JD (0-100). |
| `recommendation` | Keputusan sistem (`SHORTLIST` atau `REJECT`). |
| `mandatory_requirements_met` | Status pemenuhan syarat wajib (`true`/`false`). |

---



## Alur Sistem

```text
CV Kandidat
     │
     ▼
Ekstraksi Teks
     │
     ▼
Ekstraksi Profil Kandidat
     │
     ├── Nama
     ├── Skill
     ├── Pendidikan
     └── Pengalaman
     │
     ▼
Normalisasi Skill
     │
     ▼
Pencocokan Requirement
     │
     ├── Required Skills
     └── Preferred Skills
     │
     ▼
Semantic Similarity
     │
     ▼
Weighted Scoring
     │
     ▼
Recommendation
     │
     ▼
results.json
