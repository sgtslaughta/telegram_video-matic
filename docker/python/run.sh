#!/bin/bash

python3 init_db.py
python3 -m streamlit run './main.py'
