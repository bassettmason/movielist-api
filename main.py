# Import necessary modules
from flask import Flask, request, render_template, jsonify, redirect, url_for
from werkzeug.exceptions import HTTPException
import os
from datetime import datetime
from webscraper import FlixPatrolScraper, service_list
import logging

# Get the secret token from environment variables
my_secret = os.environ['TOKEN']

# Create a Flask app object
app = Flask("app")

# Create a logger object with the desired settings
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)
log_file = "api.log"
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Create a file handler and set the formatter
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(log_format)
# Add the file handler to the logger
logger.addHandler(file_handler)

# Define a route for the root URL that redirects to the documentation
@app.route("/")
def index():
    return redirect(url_for('docs'))
# Define a route for the documentation page
@app.route("/docs")
def docs():
    return render_template("docs.html")
    
# Define a route for the /api/topten endpoint
@app.route("/api/topten", methods=["GET"])
def api_topten():
    try:
        # Get the data and token parameters from the request's arguments
        data = request.args.get("data")
        token = request.args.get("token")
        
        # Check if the token is valid
        if token != my_secret:
            raise HTTPException("Invalid token", 401)
        
        # Handle the different cases for the data parameter
        if data is None:
            raise HTTPException("No data requested", 400)
        elif data not in service_list:
            raise HTTPException("Data specified in topten does not exist", 404)
        # Use the FlixPatrolScraper to get the top ten movies for the specified data
        top_ten_movies = []
        with FlixPatrolScraper(service_list) as scraper:
            list_name = data.replace("-", " ")
            movie_list = scraper.scrape_top_ten_movies(data)
            print(f"Top 10 movies for {data}: {movie_list}")
            top_ten_movies.append(movie_list)
        
        # Log the successful API call
        logger.info(f"Successful API call: /api/topten?data={data}&token={token}")
        # Return the top ten movies as JSON
        return jsonify({
            "type": f"{data}_topten",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": {
                "name": f"{list_name} topten",
                "url": "https://flixpatrol.com/top10",
                "playlist": top_ten_movies
            }
        })
    except HTTPException as e:
        # Log the error with the appropriate level (INFO for 404 errors, ERROR for others)
        if e.code == 404:
            logger.info(f"API error: {e.description}")
        else:
            logger.error(f"API error: {e.description}")
        # Return the error message as JSON with the appropriate status code
        return jsonify({
            "type": "Error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": e.description
        }), e.code
    except Exception as e:
        # Log the server error with the ERROR level
        logger.error(f"Server error: {str(e)}")
        
        # Return a generic server error message as JSON with a 500 status
        return jsonify({
            "type": "Error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": str(e)
        }), 500

# Runs program
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
