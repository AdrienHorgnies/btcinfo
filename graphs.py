import numpy as np
from django.db.models import Count, F
from matplotlib import pyplot as plt
from tqdm import tqdm

from db.models import Transaction


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
