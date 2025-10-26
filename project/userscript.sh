#!/bin/bash

sudo yum install httpd -y
sudo systemctl start httpd
sudo systemctl enable httpd
sudo chmod 777 /var/www/html

# Download DynamoDB table as JSON
aws dynamodb scan --table-name flights --output json > /var/tmp/flights.json

# Convert JSON to HTML
jq -r '.Items[] | "<tr><td>" + .FlightNumber.S + "</td><td>" + .Origin.S + "</td><td>" + .Destination.S + "</td><td>" + .DepartureTime.S + "</td><td>" + .Arrival.S + "</td></tr>"' /var/tmp/flights.json | \
sed '1i\
<html>\
<head><title>Flight Information</title></head>\
<body>\
<table border="1">\
<tr><th>Flight Number</th><th>Origin</th><th>Destination</th><th>Departure Time</th><th>Arrival Time</th></tr>' | \
sed '$a\
</table>\
</body>\
</html>' > /var/tmp/flights.html

# Copy the HTML file to the web directory
sudo cp /var/tmp/flights.html /var/www/html/index.html

echo 'Script executed successfully!'