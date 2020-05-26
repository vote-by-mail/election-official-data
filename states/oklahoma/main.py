import parse_pdf
import parse_html_emails
import json

if __name__ == "__main__":
    # Get all data except emails
    counties = parse_pdf.main()
    # Get all emails.
    emails = parse_html_emails.main()

    assert len(counties) == len(emails)

    for county_name, email in emails.items():
        counties[county_name]['emails'].append(email)

    counties_as_list = list(counties.values())

    with open('public/oklahoma.json', 'w') as f:
        json.dump(counties_as_list, f)
