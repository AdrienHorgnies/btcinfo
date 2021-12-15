import argparse
import logging
import os
from collections import defaultdict
from multiprocessing import Pool

import numpy as np
import pendulum
from django.core.wsgi import get_wsgi_application
import matplotlib.pyplot as plt
from tqdm import tqdm

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


def boxplot():
    """
    Draw a boxplot of the fees compared to the block size
    :return:
    """
    print('Getting blocks')
    blocks = Transaction.objects.values('block').annotate(size=Count('block_id'))
    sizes = [b['size'] for b in blocks]
    print('Got blocks')

    bin_edges = np.histogram_bin_edges(sizes, bins='doane')
    bin_indices = np.digitize(sizes, bin_edges)

    block_id_to_bin_idx = {
        b['block']: bin_id - 1 for bin_id, b in zip(bin_indices, blocks)
    }

    print('Getting transactions')
    txs = Transaction.objects.values('block').annotate(reward=F('fee') * 1.0 / F('weight'))
    print('Got transactions', txs[0] and '')

    print('Classifying transactions')
    bins = [[] for _ in range(len(bin_edges))]
    for tx in tqdm(txs):
        bin_idx = block_id_to_bin_idx[tx['block']]
        bins[bin_idx].append(tx['reward'])
    print('Classified transactions')

    print('Plotting')
    fig, ax = plt.subplots()
    title = "Récompense en fonction de la taille de bloc"

    fig.canvas.manager.set_window_title(title)
    ax.set(title=title, xlabel='Taille de bloc', ylabel='Récompense')

    labels = [f"{e:.3f}" for e in bin_edges]
    ax.boxplot(bins, labels=labels, showfliers=False, showmeans=True)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    plt.show()


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    application = get_wsgi_application()
    from db.models import Block, Transaction
    from django.db.models import Count, F

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
    boxplot()
