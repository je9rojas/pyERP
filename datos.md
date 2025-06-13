erp/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routes/
│   └── crud/
│
├── frontend/
│   ├── js/
│   ├── css/
│   └── templates/
        ├── index.html
        ├── ventas.html
        ├── compras.html

│
├── .env               
├── requirements.txt
├── render.yaml           ✅
└── README.md



uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

.\venv\Scripts\activate

(venv) PS D:\Projects\pyERP> uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000  