install:
	uv pip install -r requirements.txt

# run:
# 	uv run uvicorn main:app --app-dir src --reload

# test:
# 	uv run pytest -v

# clean-cache:
# 	find . -type d -name "__pycache__" -exec rm -r {} + && find . -type f -name "*.pyc" -delete
