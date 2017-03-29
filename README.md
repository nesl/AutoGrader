# AutoGrader

Web frontend of Embedded Systems Auto Grader project

## Install Python 3, Django and missing modules
- Install Python 3
  - Run the command ```python3``` to see if Python 3 is already installed. 
  - If not, go to this link https://www.python.org/downloads/ to get the latest version of Python.

- Install Django
  - Go to your Python ```~/site-packages``` path, which is probably ```/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/site-packages``` for Mac, and then run the following two commands:
    - ```git clone git://github.com/django/django.git```
    - ```pip install -e django/```
  - You might also need to get ```pip3``` by ```sudo apt-get install python3-pip```.

- Install missing modules
  - ```pip3 install requests```
  - ```pip3 install django-datetime-widget```
  - ```pip3 install django-widget-tweaks```
  - ```pip3 install django-bootstrap3```
  - ```pip3 install django-ipware```
  - ```pip3 install django-guardian```
  - ```pip3 install django-chartjs```
  - ```pip3 install django-ckeditor```


- If you are using PostgreSQL as your database
  - ```pip3 install psycopg2```

- Install web server components for deployment
  - ```sudo pip3 install uwsgi```
  - ```sudo apt-get install nginx```

## Configuration
- TODO: add these files as samples
  - nginx config file
  - uwsgi config file
  - django settings file

## Run the Project
 - Under ```~/AutoGrader/embed_grader```, run the command ```python3 manage.py runserver```
 - Django database: ```localhost:8000/admin```
 
## Documentation
 - Front-end Web Interface:
    https://docs.google.com/presentation/d/1_ruoovIQotxBM4Y-iti7lQ4pCLVoermDLqipjri1fas/edit#slide=id.p
 - System Diagram:
    https://docs.google.com/drawings/d/17p6AJe_jlNczr7rI9q8qLMmYHKDRXLg_uexPmBcsbmc/edit
 - Database Element:
    https://docs.google.com/document/d/1XgrPa4Yvj6kiQ2qQBOehS6-iW9hohrqubGEyCEV7bjc/edit
