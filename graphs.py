import numpy as np
from django.db.models import Count, F
from matplotlib import pyplot as plt
from tqdm import tqdm

from db.models import Transaction, Block


def reject_outliers(data, m=3):
    return data[abs(data - np.median(data)) < m * np.std(data)]


def draw():
    """
    Draw a boxplot of the fees compared to the block size
    :return:
    """
    print('Getting blocks')
    blocks = Transaction.objects.values('block').annotate(size=Count('block_id'))
    sizes = [b['size'] for b in blocks]
    print('Got blocks')

    print('Getting transactions')
    txs = Transaction.objects.values('block').annotate(reward=F('fee') * 1.0 / F('weight'))
    print('Got transactions', txs[0] and '')

    print('Computing service times')
    selection_times = Block.objects.values_list('time', flat=True).order_by('time')
    selection_times = np.array([t.timestamp() for t in selection_times])
    service_times = selection_times[1:] - selection_times[:-1]
    service_times = reject_outliers(service_times)

    print('Collecting fees')
    fees_n_weights = Transaction.objects.values('fee', 'weight')
    fnw_ratios = np.array([fnw['fee'] / fnw['weight'] for fnw in fees_n_weights])
    fnw_ratios = reject_outliers(fnw_ratios)

    print('Classifying transactions by fees')
    bin_edges_congestion = np.histogram_bin_edges(sizes, bins='doane')
    bin_indices_congestion = np.digitize(sizes, bin_edges_congestion)

    block_id_to_bin_idx_congestion = {
        b['block']: bin_id - 1 for bin_id, b in zip(bin_indices_congestion, blocks)
    }
    bins_congestion = [[] for _ in range(len(bin_edges_congestion))]
    for tx in tqdm(txs):
        bin_idx = block_id_to_bin_idx_congestion[tx['block']]
        bins_congestion[bin_idx].append(tx['reward'])
    print('Classified transactions')

    print('Plot sizes')
    fig_sizes, ax_sizes = plt.subplots()
    title_sizes = "Histogramme des tailles des blocs"

    fig_sizes.canvas.manager.set_window_title(title_sizes)
    ax_sizes.set(title=title_sizes, xlabel='Nombre de transactions par bloc', ylabel='Nombre de blocs')

    ax_sizes.hist(sizes, bins='auto')
    
    print('Plot service time')
    fig_service, ax_service = plt.subplots()
    title_service = "Histogramme du temps inter-bloc"

    fig_service.canvas.manager.set_window_title(title_service)
    ax_service.set(title=title_service, xlabel='Temps entre les blocs (secondes)', ylabel='Nombre de blocs')

    ax_service.hist(service_times, bins='auto')
    
    print('Plot fee ratios')
    fig_fee_ratios, ax_fee_ratios = plt.subplots()
    title_fee_ratios = "Histogramme des ratios de récompense sur poids"

    fig_fee_ratios.canvas.manager.set_window_title(title_fee_ratios)
    ax_fee_ratios.set(title=title_fee_ratios, xlabel='Ratio des frais de transactions sur poids (satoshi/WU)', ylabel='Nombre de transactions')

    ax_fee_ratios.hist(fnw_ratios, bins='auto')

    print('Plot Congestion')
    fig_congestion, ax_congestion = plt.subplots()
    title_congestion = "Ratio de récompense sur poids des transactions en fonction de la taille de bloc"

    fig_congestion.canvas.manager.set_window_title(title_congestion)
    ax_congestion.set(title=title_congestion, xlabel='Nombre de transactions par bloc', ylabel='Ratio de récompense sur poids (satoshi/WU)')

    labels_congestion = [f"{e:.0f}" for e in bin_edges_congestion]
    ax_congestion.boxplot(bins_congestion, labels=labels_congestion, showfliers=False, showmeans=True)
    ax_congestion.set_xticklabels(labels_congestion, rotation=45, ha='right')

    plt.show()
