from flask import Flask, render_template, request, send_file
import boto3
from datetime import datetime
import time
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import bs4
import geocoder
from gtts import gTTS
import os

app = Flask(__name__)

#Home route for EC2 instance creation form
@app.route('/')
def ec2_index():
    return render_template('index.html')

# Route to handle EC2 instance creation
@app.route('/launch_instance', methods=['POST'])
def launch_instance():
    access_key = request.form['access_key']
    secret_key = request.form['secret_key']
    region = request.form['region']
    instance_type = request.form['instance_type']
    image_id = request.form['image_id']

    ec2 = boto3.client('ec2', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        conn = ec2.run_instances(
            InstanceType=instance_type,
            MaxCount=1,
            MinCount=1,
            ImageId=image_id
        )
        return f"EC2 instance launched successfully: {conn}"
    except Exception as e:
        return f"Error launching EC2 instance: {str(e)}"

# Route for CloudWatch Logs form
@app.route('/cloudwatch')
def cloudwatch_index():
    return render_template('cloudwatch_logs.html')

# Route to handle CloudWatch log retrieval
@app.route('/get_logs', methods=['POST'])
def get_logs():
    access_key = request.form['access_key']
    secret_key = request.form['secret_key']
    region = request.form['region']
    log_group = request.form['log_group']
    log_stream = request.form['log_stream']

    logs = boto3.client('logs', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startFromHead=True
        )
        log_messages = [event['message'] for event in response['events']]
        return render_template('display_logs.html', logs=log_messages)
    except Exception as e:
        return f"Error retrieving logs: {str(e)}"

# Route for Transcription form
@app.route('/transcription')
def transcription_index():
    return render_template('transcription.html')

# Route to handle Transcription job
@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    access_key = request.form['access_key']
    secret_key = request.form['secret_key']
    region = request.form['region']
    bucket_name = request.form['bucket_name']
    file_key = request.form['file_key']

    s3 = boto3.client('s3', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    transcribe = boto3.client('transcribe', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    job_name = f"{file_key.split('.')[0]}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': f's3://{bucket_name}/{file_key}'},
            MediaFormat='mp3',
            LanguageCode='en-IN',
            OutputBucketName=bucket_name
        )

        # Wait for the job to complete
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                break
            time.sleep(5)

        if job_status == 'COMPLETED':
            transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            transcript_response = s3.get_object(Bucket=bucket_name, Key=f"{job_name}.json")
            transcript_text = transcript_response['Body'].read().decode('utf-8')
            transcript_data = json.loads(transcript_text)
            transcript_message = transcript_data['results']['transcripts'][0]['transcript']
            return render_template('display_transcript.html', transcript=transcript_message)
        else:
            return f"Transcription job '{job_name}' failed."
    except Exception as e:
        return f"Error starting transcription job: {str(e)}"

# Route for S3 file upload form
@app.route('/upload')
def upload_index():
    return render_template('upload.html')

# Route to handle S3 file upload
@app.route('/upload_file', methods=['POST'])
def upload_file():
    access_key = request.form['access_key']
    secret_key = request.form['secret_key']
    bucket = request.form['bucket']
    file_name_with_path = request.form['file_name_with_path']
    file_name = request.form['file_name']

    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        s3.upload_file(file_name_with_path, bucket, file_name)
        return render_template('display_upload.html', message=f"File '{file_name}' uploaded successfully to '{bucket}'.")
    except Exception as e:
        return render_template('display_upload.html', message=f"Error: {e}")

# Route for Email form
@app.route('/email')
def email_index():
    return render_template('email.html')

# Route to handle sending email
@app.route('/send_email', methods=['POST'])
def send_email():
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = request.form['sender_email']
    sender_password = request.form['sender_password']
    recipient_email = request.form['recipient_email']
    subject = request.form['subject']
    body = request.form['body']

    try:
        # Create the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        return render_template('display_email.html', message="Email sent successfully.")
    except Exception as e:
        return render_template('display_email.html', message=f"Error: {e}")

# Route for SMS form
@app.route('/sms')
def sms_index():
    return render_template('sms.html')

# Route to handle sending SMS
@app.route('/send_sms', methods=['POST'])
def send_sms():
    account_sid = request.form['account_sid']
    auth_token = request.form['auth_token']
    twilio_number = request.form['twilio_number']
    recipient_number = request.form['recipient_number']
    message_body = request.form['message_body']

    try:
        # Create Twilio client
        client = Client(account_sid, auth_token)

        # Send SMS
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=recipient_number
        )

        return render_template('display_sms.html', message=f"Message sent with SID: {message.sid}")
    except Exception as e:
        return render_template('display_sms.html', message=f"Error: {e}")

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form['query']
        url = f'https://google.com/search?q={query}'
        request_result = requests.get(url)
        soup = bs4.BeautifulSoup(request_result.text, "html.parser")
        headings = soup.find_all('h3')
        results = [heading.getText() for heading in headings]
    return render_template('search.html', results=results)

@app.route('/geolocation')
def geolocation():
    g = geocoder.ip('me')
    latlng = g.latlng
    return render_template('geolocation.html', latlng=latlng)

@app.route('/text-to-speech', methods=['GET', 'POST'])
def text_to_speech():
    if request.method == 'POST':
        text = request.form['text']
        language = 'en'
        
        # Convert text to speech
        tts = gTTS(text=text, lang=language, slow=False)
        file_path = "static/speech.mp3"
        tts.save(file_path)

        return render_template('play_audio.html', audio_file=file_path)
    
    return render_template('text_to_speech.html')

@app.route('/play/<filename>')
def play_audio(filename):
    return send_file(filename)

if __name__ == '__main__':
    app.run(debug=True)
