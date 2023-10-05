# Base Image: Python 3.12
FROM python:3.12

# Copy the required contents from the current directory
#   requirements.txt --> All Python dependencies
#   utils (DIRECTORY) --> Util directories with extra resources needed by app.py
#   app.py --> Main application starting point
#   launch.sh --> Main application launcher (with enviroment variables)
ADD ./requirements.txt /app/
ADD ./utils/ /app/utils/
ADD ./app.py /app/
ADD ./launch.sh /app/

# Set the working directory to /app
WORKDIR /app

# Install dependencies from the requirements file
RUN python -m pip install -r requirements.txt

# Launch the application via launch.sh (wich launches the app.py file with the correct arguments)
ENTRYPOINT ./launch.sh
