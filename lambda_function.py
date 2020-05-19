from bs4 import BeautifulSoup
import urllib.request
import pickle
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import boto3
import re
from botocore.exceptions import ClientError


def send_email(item_list, recipient_email, subject, sender_email, password):
	port = 465  # For SSL
	smtp_server = "smtp.gmail.com"
	receiver_email = recipient_email
	msg = MIMEMultipart()
	msg['From'] = 'Craigslist'
	#msg['To'] = ''
	msg['Subject'] = subject

	for item in item_list:
		msg.attach(MIMEText('<html><body><h1>'+item[0]+'</h1>'+
							'<h0>'+item[1]+'</h0>'+
							'<p><img src="'+item[2]+'"></p>' +
							'</body></html>', 'html', 'utf-8'))

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email, msg.as_string())


def check(search_term, recipient_email, county, sender_email=None, password=None, item_set=None):
	craigslist_url = 'https://'+county.replace(' ', '')+'.craigslist.org/search/sss?query='+search_term.replace(' ', '+')
	link = urllib.request.Request(craigslist_url, headers= {
		'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
	html = urllib.request.urlopen(link)
	soup = BeautifulSoup(html.read(), "html.parser")
	new_items = []
	regex = re.compile('[^a-zA-Z\s\d]')
	for box in soup.find_all('li', {'class':'result-row'}):
		i = box.find('a', {'class':'result-title hdrlnk'})
		if i.text not in item_set and search_term in regex.sub('', i.text).lower():
			print(i.text)
			item_set.add(i.text)
			sub_url = i.attrs['href']
			sub_soup = BeautifulSoup(urllib.request.urlopen(sub_url).read(), "html.parser")
			if sub_soup.find('img'):
				pic_url = sub_soup.find('img').attrs['src']
				new_items.append((i.text, sub_url, pic_url))
	if new_items:
		print('sent', search_term)
		send_email(new_items, recipient_email, search_term, sender_email, password)
		return item_set


def driver(s3):
	# writes from s3
	if s3:
		s3 = boto3.resource('s3')
		bucket = s3.Bucket('craigslist')
		items = bucket.Object('items.txt').get()['Body'].read().decode("utf-8").splitlines()
		sender, pw = bucket.Object('credentials.txt').get()['Body'].read().decode("utf-8").split()
	else:
		# items from local
		items = open('items.txt').readlines()
		sender, pw = open('credentials.txt').readlines()

	for i in items:
		st, email, county = i.strip().split(',')
		# read pickle from s3
		if s3:
			try:
				item_set = pickle.loads(bucket.Object(st+'.pickle').get()['Body'].read())
			except ClientError as ex:
				if ex.response['Error']['Code'] == "NoSuchKey":
					print('new set')
					item_set = set()
		else:
			# local pickle
			try:
				file = open(st+'.pickle', 'rb')
				item_set = pickle.load(file)
			except FileNotFoundError:
				item_set = set()

		new_items = check(search_term=st, recipient_email=email, county=county, sender_email=sender, password=pw, item_set=item_set)
		if new_items is not None:
			if s3:
				# write pickle to s3
				pi = pickle.dumps(new_items)
				s3_resource = boto3.resource('s3')
				s3_resource.Object('craigslist', st+'.pickle').put(Body=pi)
				print('wrote to s3')
			else:
				# write local pickle
				file = open(st+'.pickle', 'wb')
				pickle.dump(item_set, file)


def lambda_handler(event, context):
	driver(s3=True)
	return {
		'statusCode': 200,
		'body': json.dumps('sent from Lambda')
	}


if __name__ == '__main__':
	driver(s3=False)

