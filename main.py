import argparse
import logging
import os
from collections import defaultdict
from multiprocessing import Pool
from typing import List

import pendulum
from django.core.wsgi import get_wsgi_application

from api.btc import get_blocks, get_block, BriefBlock, DetailedBlock

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

blocks_counter = defaultdict(int)


def increase_counter(day, fun):
    """
    Count number of blocks to fetch by period (day, month, year, total)

    :param day:
    :param fun:
    :return:
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
    """
    Creates a proxy method around fun, and decreases counters by one when called.

    :param day: The day the block has been generated
    :param fun: The function to create a proxy for.
    :return: A proxy method that behaves such as fun.
    """

    def proxy(block: DetailedBlock):
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


def main(start_date, end_date):
    """
    Retrieves blocks and transactions from the API.
    """
    with Pool(2) as p1, Pool(16) as p2:
        def get_details_and_save(blocks: List[BriefBlock]):
            """
            Retrieves the details of the listed blocks and save them in the database.

            :param blocks: The blocks to get details for
            """
            for block in blocks:
                if Block.objects.filter(height=block['height']):
                    continue
                p2.apply_async(get_block,
                               (block['hash'],),
                               callback=decrease_counter(block['day'], Block.save_from_api))

        for day in end_date - start_date:
            log.info(f'Considering {day.to_formatted_date_string()}')
            # testing if there are blocks around 12 hours before day, to avoid fetching the same day twice
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
    from graphs import draw

    parser = argparse.ArgumentParser(
        description="Fetch and store blocks and transactions in the specified date interval.")
    subparsers = parser.add_subparsers(dest="command")

    retrieve_parser = subparsers.add_parser("retrieve", help="Retrieve data from the API.")
    retrieve_parser.add_argument('start_date', type=lambda s: pendulum.from_format(s, 'DD-MM-YYYY'),
                                 help="date format is DD-MM-YYYY")
    retrieve_parser.add_argument('end_date', type=lambda s: pendulum.from_format(s, 'DD-MM-YYYY'),
                                 help="date format is DD-MM-YYYY")

    graph_parser = subparsers.add_parser("draw", help="Draw graphs using saved data.")

    args = parser.parse_args()
    if args.command == 'retrieve':
        main(args.start_date, args.end_date)
    elif args.command == 'draw':
        draw()
    else:
        raise argparse.ArgumentError(args.command, "Unknown command")
