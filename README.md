# final year project "Emo-Insight" (2020-2024)

This Flask project demonstrates user authentication using MongoDB and mysql both as the database. It provides a secure authentication system that allows users to sign up, log in, and access protected routes.

## Project Structure

- `static`: Directory for storing static files (CSS, JavaScript).
- `templates`: Directory for storing HTML templates.
- `appSql.py`: The main Flask application file.
- `config.py`: Configuration file for storing sensitive information (e.g., MongoDB URI, secret keys, mysql config as well).

## Getting Started

### Prerequisites

- Python
- Flask (install via `pip3 install Flask`)
- Flask-PyMongo (install via `pip3 install "pymongo[srv]" `)
- SqlClient, etc.
- MongoDB (set up and running)

### Installation

1. Clone the repository:

   ```bash
   https://github.com/Arshadcs20/emo-insight.git
   ```

2. Navigate to the project directory:

   ```bash
   cd emo-insight
   ```

### Usage

1. Configure MongoDB URI in the `config.py` file:

   ```python
   MONGO_URI = "your url from Atlas"
   ```

2. Run the Flask application:

   ```bash
   python appSql.py
   ```

3. Access the application in your web browser at [http://localhost:5000](http://localhost:5000).

## Other Resources

1. `https://pypi.org/project/ntscraper/ - for scraping data from websites`

## Tailwind
1. `https://tailwindcss.com/docs/installation - for styling the website`

## Visit the following portfolio site
1. `https://arshadcs20.github.io/`