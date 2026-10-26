\# Self-Healing RAG - Native Deployment



\## Architecture



Client

&#x20; |

&#x20; v

Streamlit :8501

&#x20; |

&#x20; v

FastAPI / Uvicorn :8000

&#x20; |

&#x20; +-- PostgreSQL

&#x20; +-- Qdrant

&#x20; +-- LLM Providers



\## Local Production Start



Backend:

start\_backend.bat



Frontend:

start\_frontend.bat



\## Linux Server Deployment



1\. Install Python 3.11

2\. Install PostgreSQL

3\. Install Tesseract OCR

4\. Copy/clone the project

5\. Create Python virtual environment

6\. Install requirements.txt

7\. Configure environment variables

8\. Initialize PostgreSQL

9\. Start FastAPI with Uvicorn

10\. Start Streamlit

11\. Run both as system services

12\. Put Nginx in front of the application

13\. Configure HTTPS and firewall



\## Backend



python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000



\## Frontend



python -m streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501

