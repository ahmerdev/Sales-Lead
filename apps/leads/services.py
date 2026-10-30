import csv
import io
from .models import Lead

def import_leads_from_csv(csv_file, workspace):
    """
    Parses an uploaded CSV file, intelligently maps columns, and imports leads
    under the tenant's workspace.
    """
    decoded_file = csv_file.read().decode('utf-8-sig', errors='replace')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)
    
    # Normalize headers
    field_map = {}
    if reader.fieldnames:
        for header in reader.fieldnames:
            h_lower = header.strip().lower().replace('_', ' ').replace('-', ' ')
            if any(k in h_lower for k in ['business name', 'company', 'name', 'title']):
                field_map['business_name'] = header
            elif any(k in h_lower for k in ['website', 'url', 'domain', 'web']):
                field_map['website'] = header
            elif 'email' in h_lower:
                field_map['email'] = header
            elif any(k in h_lower for k in ['phone', 'mobile', 'tel', 'cell']):
                field_map['phone'] = header
            elif any(k in h_lower for k in ['city', 'location', 'town']):
                field_map['city'] = header
            elif any(k in h_lower for k in ['industry', 'category', 'sector', 'niche']):
                field_map['industry'] = header
            elif 'country' in h_lower:
                field_map['country'] = header

    created_count = 0
    errors = []

    for row_idx, row in enumerate(reader, start=1):
        try:
            b_name = row.get(field_map.get('business_name', 'business_name'), '').strip()
            if not b_name:
                continue

            website = row.get(field_map.get('website', 'website'), '').strip()
            email = row.get(field_map.get('email', 'email'), '').strip()
            phone = row.get(field_map.get('phone', 'phone'), '').strip()
            city = row.get(field_map.get('city', 'city'), '').strip() or 'Dubai'
            country = row.get(field_map.get('country', 'country'), '').strip() or 'United Arab Emirates'
            industry = row.get(field_map.get('industry', 'industry'), '').strip() or 'Restaurant'

            # Normalize industry to choices
            valid_industries = dict(Lead.INDUSTRY_CHOICES)
            matched_industry = 'Other'
            for ind_key, ind_label in valid_industries.items():
                if ind_key.lower() in industry.lower() or ind_label.lower() in industry.lower():
                    matched_industry = ind_key
                    break

            Lead.objects.create(
                workspace=workspace,
                business_name=b_name,
                website=website,
                email=email,
                phone=phone,
                city=city,
                country=country,
                industry=matched_industry,
                source='CSV_IMPORT',
                status='NEW'
            )
            created_count += 1
        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    return created_count, errors
