# Craigslist Item Checker
Enter search term in text file, county you want to search, and the email you want items sent to<br>
Scrapes titles, images and links from craigslist, and emails them to you.<br>
Requires one email be used as the sender.  Make sure to grant your email permission to be logged in this way, use your junk email.<br>
Does not send reposts unless the seller changes the item title.<br>

### Prerequisites
Runs locally, needs Beautiful Soup 4, Python<br>
pip install bs4

Also runs on AWS lambda with S3
Needs bs4 to be zipped with the Python file and uploaded to lambda
