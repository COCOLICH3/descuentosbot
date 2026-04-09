"""
Corre ambos scrapers en secuencia.
Uso: python scrape_all.py
"""
import subprocess
import sys

subprocess.run([sys.executable, "scraper_carrefour.py"])
subprocess.run([sys.executable, "scraper_dia.py"])