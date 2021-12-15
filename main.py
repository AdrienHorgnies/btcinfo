import logging
import os
import argparse
from collections import defaultdict
from multiprocessing import Pool

import pendulum
from django.core.wsgi import get_wsgi_application

from api.btc import get_blocks, get_block

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

PERIOD_START = pendulum.datetime(2021, 9, 15).naive()
PERIOD_END = pendulum.datetime(2021, 11, 14).naive()
blocks_counter = defaultdict(int)


def increase_counter(day, fun):
    """
    Count number of blocks to fetch by period (day, month, year, total)
    """

    def proxy(blocks):
        blocks_counter[day] += len(blocks)
        blocks_counter[day.format("YYYY MM")] += len(blocks)
        blocks_counter[day.year] += len(blocks)
        blocks_counter['total'] += len(blocks)
        for block in blocks:
            # easier to map block to day afterwards
            block['day'] = day

        return fun(blocks)

    return proxy


def decrease_counter(day, fun):
    def proxy(block):
        blocks_counter[day] -= 1
        blocks_counter[day.format("YYYY MM")] -= 1
        blocks_counter[day.year] -= 1
        blocks_counter['total'] -= 1
        log.info(f'total: {blocks_counter["total"]}, '
                 f'{day.year}={blocks_counter[day.year]}, '
                 f'{day.month}={blocks_counter[day.format("YYYY MM")]}, '
                 f'{day.day}={blocks_counter[day]}')
        return fun(block)

    return proxy


def main():
    with Pool(2) as p1, Pool(16) as p2:
        def get_details_and_save(blocks):
            for block in blocks:
                if Block.objects.filter(height=block['height']):
                    continue
                p2.apply_async(get_block,
                               (block['hash'],),
                               callback=decrease_counter(block['day'], Block.save_from_api))

        for day in PERIOD_END - PERIOD_START:
            log.info(f'Considering {day.to_formatted_date_string()}')
            # testing if there are blocks around 12 hours before day, to avoid overlapping days from API
            if Block.objects.filter(time__gt=day.subtract(hours=12), time__lt=day.subtract(hours=11)):
                log.info(f'skipping {day.to_formatted_date_string()}')
                continue
            log.info(f'Planning {day.to_formatted_date_string()}')
            p1.apply_async(get_blocks,
                           (day,),
                           callback=increase_counter(day, get_details_and_save))

        p1.close()
        p1.join()
        p2.close()
        p2.join()


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    application = get_wsgi_application()
    from db.models import Block

    parser = argparse.ArgumentParser(
        description="Fetch and store blocks and transactions in the specified date interval")
    parser.add_argument('start_date', type=lambda s: pendulum.from_format(s, 'DD-MM-YYYY'),
                        help="date format is DD-MM-YYYY")
    parser.add_argument('end_date', type=lambda s: pendulum.from_format(s, 'DD-MM-YYYY'),
                        help="date format is DD-MM-YYYY")
    args = parser.parse_args()

    PERIOD_START = args.start_date
    PERIOD_END = args.end_date

    main()
