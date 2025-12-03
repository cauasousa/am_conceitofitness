#!/usr/bin/env bash
# Inicia a aplicação Flask usando Gunicorn
# gunicorn app:app
gunicorn --workers 4 app:app