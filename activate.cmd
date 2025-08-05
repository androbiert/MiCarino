venv\Scripts\activate

pip freeze > requirements.txt

git init
git add .
git commit -m "Initial Django project commit"

git remote add origin https://github.com/androbiert/miCarino.git
git branch -M main
git push -u origin main

for any modifications, run:
git add .
git commit -m "Update project"
git push
