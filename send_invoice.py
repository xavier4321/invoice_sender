import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, 
                                 FileType, Disposition)
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client
from jinja2 import Template
import base64
from weasyprint import HTML
from io import BytesIO

# Load your API keys
load_dotenv()

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_active_users_by_domain(domain):
    try:
        # Query Supabase for emails matching the domain
        response = supabase.table('agents').select('email').ilike('email', f'%@{domain}').execute()
        
        # Extract emails from response
        emails = [user['email'] for user in response.data]
        return emails
    except Exception as e:
        print(f"Error querying Supabase: {e}")
        return []

def create_pdf(template_string, data):
    # Render the template with data
    html_content = template_string.render(**data)
    
    # Convert to PDF
    pdf = HTML(string=html_content).write_pdf()
    return pdf

def send_email(row, test_email):
    # Get domain from agency
    domain = row['agency']
    
    # Get active users for this domain
    active_users = get_active_users_by_domain(domain)
    number_of_users = len(active_users)  # Calculate number of users from active_users list
    print(f"Found {number_of_users} active users for {domain}")
    
    # Read the HTML template
    with open('invoice_template.html', 'r') as file:
        template = Template(file.read())
    
    # Prepare data for template
    template_data = {
        'agency': row['agency'].replace('.com', ''),
        'renewal_date': row['renewal_date'],
        'number_of_users': number_of_users,  # Use calculated number
        'active_users': active_users,
        'amount': row['amount']
    }
    
    # Create PDF
    pdf_content = create_pdf(template, template_data)
    
    # Encode PDF in base64
    encoded_pdf = base64.b64encode(pdf_content).decode()
    
    # Create attachment
    attachment = Attachment(
        FileContent(encoded_pdf),
        FileName(f'invoice_{row["agency"]}.pdf'),
        FileType('application/pdf'),
        Disposition('attachment')
    )
    
    # Create email with attachment
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=test_email,  # Use the provided test email
        subject=f'Basis Invoice for {row["agency"]}',
        html_content=f'''
            <p>Hola,</p>
            <p>I just added SkyLux and Fly-Flat for testing. However, to add more agencies it's simply a matter of adding a row in the CSV. Also didn't wanna spam your inbox.</p>
            <p>Invoice attached.</p>
        '''
    )
    message.attachment = attachment
    
    return message

def process_invoices(test_email):
    output = []
    # Read CSV and process each row
    df = pd.read_csv("agencies.csv")

    # Initialize SendGrid client once outside the loop
    sg = SendGridAPIClient(SENDGRID_API_KEY)

    first_invoice = True  # Add this flag at the start
    for index, row in df.iterrows():
        try:
            message = send_email(row, test_email)
            response = sg.send(message)
            if first_invoice:
                status = f"Invoice sent to {test_email} for {row['agency']}"
                first_invoice = False  # Set flag to False after first invoice
            else:
                status = f"Another invoice sent for {row['agency']}"
            output.append(status)
            print(status)
        except Exception as e:
            error = f"Error sending to {row['agency']}: {e}"
            output.append(error)
            print(error)
    
    return '\n'.join(output)

if __name__ == "__main__":
    # This will only run when script is run directly, not when imported
    test_email = input("Enter test email address: ")
    process_invoices(test_email)
