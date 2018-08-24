import csv
import codecs
import random


def main():

    bundle = [['ASH-ALL', 1500], ['BLOOD-ONLY', 1100], ['BLOOD-ARCHIVE-ONLY', 750]]

    subscribers_file_name = "./blood_subscribers.txt"
    subscriptions_file_name = "./blood_subscriptions.txt"

    out_file = codecs.open(subscriptions_file_name, 'w', 'utf-8')
    out_file.write('Membership No\t'
                   'Year\t'
                   'Bundle Name\t'
                   'On Trial\t'
                   'Trial Expiration Date\t'
                   'Amount\n')

    with open(subscribers_file_name, 'r', encoding='utf-8') as tsv:

        reader = csv.reader(tsv, delimiter="\t")
        next(reader)
        count = 0

        for line in reader:
            count += 1

            subscriber_id = line[0]
            start_year = int(line[1])

            b = bundle[random.randint(1, 1000) % 3]

            for y in range(start_year, 2017):

                if (count % 50) == 0 and y == 2016:
                    print(subscriber_id)
                    bundle_name = bundle[0][0]
                    bundle_price = bundle[0][1]
                else:
                    bundle_name = b[0]
                    bundle_price = b[1]

                if (count % 100) == 0 and y == 2016 and start_year == 2016:
                    trial = 'Y'
                    trial_expiration = "01/01/2017"
                else:
                    trial = 'N'
                    trial_expiration = ""

                row = """%s\t%s\t%s\t%s\t%s\t%s\n""" % (subscriber_id, y, bundle_name, trial, trial_expiration, bundle_price)

                out_file.write(row)

    out_file.close()


if __name__ == "__main__":
    main()


