from ivetl.models import SubscriptionPricing

membership_no = ''
year = None
has_pckg_a = False
has_pckg_b = False
to_delete = []
count = 0

for s in SubscriptionPricing.objects.filter(publisher_id='cshl').fetch_size(1000).limit(10000000):
    count += 1
    if not count % 10000:
        print(count)
    if s.membership_no != membership_no:
        membership_no = s.membership_no
        year = s.year
        has_pckg_a = has_pckg_b = False
    elif s.year != year:
        year = s.year
        has_pckg_a = has_pckg_b = False

    if s.bundle_name == 'PCKG A':
        has_pckg_a = True
    if s.bundle_name == 'PCKG B':
        has_pckg_b = True
    if has_pckg_a and has_pckg_b:
        to_delete.append(s.membership_no)